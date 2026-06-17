"""Lazy K-Modes model service used by the recommendation endpoint."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from api.core.config import get_api_config, resolve_ml_path
from api.core.segments import normalize_segment_label


@dataclass(frozen=True)
class KModesPrediction:
    """Prediction result returned by the K-Modes service."""

    cluster_id: int
    cluster_label: str
    raw_cluster_index: int
    distances: list[int]


class KModesModelService:
    """Load, validate, and use the saved K-Modes model.

    The model is loaded lazily and cached by ``get_kmodes_service`` so importing
    FastAPI routes does not immediately fail when model files are absent.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        api_cfg = get_api_config()
        self.cfg = dict(api_cfg.get("model", {}))
        if config:
            self.cfg.update(config)

        self.model_dir = resolve_ml_path(self.cfg["model_dir"])
        self.model_path = self.model_dir / self.cfg["kmodes_model_filename"]
        self.feature_columns_path = self.model_dir / self.cfg["feature_columns_filename"]
        self.cluster_label_map_path = self.model_dir / self.cfg["cluster_label_map_filename"]

        self.model = None
        self.feature_columns: list[str] = []
        self.cluster_label_map: dict[str, str] = {}

    def load(self) -> "KModesModelService":
        """Load model artifacts from disk if they are not already loaded."""
        if self.model is not None:
            return self

        self._check_required_files()
        try:
            self.model = joblib.load(self.model_path)
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "A package required to load the saved K-Modes model is missing. "
                "Install api/requirements.txt, including kmodes."
            ) from exc
        self.feature_columns = self._read_json_list(self.feature_columns_path)
        self.cluster_label_map = self._read_json_dict(self.cluster_label_map_path)
        return self

    def _check_required_files(self) -> None:
        missing = [
            str(path)
            for path in [self.model_path, self.feature_columns_path, self.cluster_label_map_path]
            if not path.exists()
        ]
        if missing:
            raise FileNotFoundError(
                "Missing K-Modes model artifacts. Expected files under "
                f"{self.model_dir}: " + ", ".join(missing)
            )

    @staticmethod
    def _read_json_list(path: Path) -> list[str]:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, list):
            raise ValueError(f"Expected a JSON list in {path}.")
        return [str(item) for item in data]

    @staticmethod
    def _read_json_dict(path: Path) -> dict[str, str]:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, dict):
            raise ValueError(f"Expected a JSON object in {path}.")
        return {str(key): str(value) for key, value in data.items()}

    def _build_input_array(self, responses: dict[str, Any]):
        missing = [feature for feature in self.feature_columns if feature not in responses]
        if missing:
            raise ValueError(
                f"Missing {len(missing)} required clustering features: {missing}"
            )

        row = pd.DataFrame([responses])[self.feature_columns].copy()
        input_dtype = self.cfg.get("input_dtype", "Int64")
        for column in self.feature_columns:
            row[column] = pd.to_numeric(row[column], errors="raise").astype(input_dtype).astype(str)
        return row.to_numpy()

    def _hamming_distances(self, input_array) -> list[int]:
        centroids = self.model.cluster_centroids_
        return [
            int(sum(input_array[0][index] != centroid[index] for index in range(len(self.feature_columns))))
            for centroid in centroids
        ]

    def _tie_safe_cluster_index(self, input_array, raw_cluster_index: int, distances: list[int]) -> int:
        strategy = self.cfg.get("tie_break_strategy", "highest_centroid_average")
        if strategy != "highest_centroid_average":
            return raw_cluster_index

        min_distance = min(distances)
        tied_clusters = [index for index, distance in enumerate(distances) if distance == min_distance]
        if len(tied_clusters) <= 1:
            return raw_cluster_index

        centroid_scores: list[tuple[int, float]] = []
        for cluster_index in tied_clusters:
            centroid_values = [int(value) for value in self.model.cluster_centroids_[cluster_index]]
            centroid_scores.append((cluster_index, sum(centroid_values) / len(centroid_values)))

        return max(centroid_scores, key=lambda item: item[1])[0]

    def predict(self, responses: dict[str, Any]) -> KModesPrediction:
        """Assign a student to a K-Modes cluster and return a cleaned label."""
        self.load()
        input_array = self._build_input_array(responses)
        raw_cluster_index = int(self.model.predict(input_array)[0])
        distances = self._hamming_distances(input_array)
        raw_cluster_index = self._tie_safe_cluster_index(input_array, raw_cluster_index, distances)

        label_offset = int(self.cfg.get("label_offset", 1))
        cluster_id = raw_cluster_index + label_offset
        raw_label = self.cluster_label_map.get(str(cluster_id), f"Cluster {cluster_id}")
        cluster_label = normalize_segment_label(raw_label, self.cluster_label_map)

        return KModesPrediction(
            cluster_id=cluster_id,
            cluster_label=cluster_label,
            raw_cluster_index=raw_cluster_index,
            distances=distances,
        )


@lru_cache(maxsize=1)
def get_kmodes_service() -> KModesModelService:
    """Return the process-wide cached K-Modes service."""
    return KModesModelService().load()


def assign_kmodes_cluster(responses: dict[str, Any]) -> tuple[int, str]:
    """Backward-compatible helper used by existing route code."""
    prediction = get_kmodes_service().predict(responses)
    return prediction.cluster_id, prediction.cluster_label
