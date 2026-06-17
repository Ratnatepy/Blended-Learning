"""Configuration and path helpers for the FastAPI backend.

The API intentionally reuses the ML project's ``config/config.json`` through
``blended_learning.config.settings`` so model paths, labels, NLP rules, and LLM
settings have one source of truth.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from blended_learning.config.settings import settings

PROJECT_ROOT = Path(__file__).resolve().parents[2]
API_ROOT = PROJECT_ROOT / "api"
ML_ROOT = settings.root

# Load both possible env locations. Existing values are preserved.
for env_path in [PROJECT_ROOT / ".env", ML_ROOT / ".env"]:
    if env_path.exists():
        load_dotenv(env_path, override=False)


DEFAULT_API_CONFIG: dict[str, Any] = {
    "database": {
        "env": "DATABASE_URL",
        "default_url": "postgresql://postgres:postgres@localhost:5432/blended_learning_db",
        "pool_pre_ping": True,
        "echo": False,
    },
    "seed": {
        "enabled": True,
        "csv_path": "data/processed/student_recommendation_reports_current.csv",
        "required_columns": [
            "student_id",
            "student_segment_label",
            "final_recommendation_tags",
            "llm_recommendation_report",
        ],
        "student_id_column": "student_id",
        "deduplicate_keep": "last",
        "replace_when_count_differs": True,
        "log_prefix": "[seed]",
    },
    "model": {
        "model_dir": "models",
        "kmodes_model_filename": "kmodes_model.pkl",
        "feature_columns_filename": "kmodes_feature_columns.json",
        "cluster_label_map_filename": "kmodes_cluster_label_map.json",
        "label_offset": 1,
        "input_dtype": "Int64",
        "tie_break_strategy": "highest_centroid_average",
    },
    "segments": {
        "unknown_label": "Unknown",
        "normalization_rules": [
            {
                "label": "Moderately Engaged (Passive) Learners",
                "match_any": ["passive", "moderately engaged", "moderately", "moderate"],
            },
            {
                "label": "Highly Engaged (Active) Learners",
                "match_any": ["highly engaged", "highly", "active", "high"],
            },
        ],
        "raw_cluster_id_strategy": "model_label_map",
        "strip_cluster_prefix_regex": r"\bCluster\s+\d+\s*[:\-–—]\s*",
    },
    "llm_runtime": {
        "temperature": 0.3,
        "max_tokens": 900,
    },
    "nlp_runtime": {
        "translation_enabled": True,
        "fallback_to_original_on_translation_error": True,
    },
    "app": {
        "title": "Blended Learning Recommendation API",
        "description": "FastAPI backend for student segmentation and personalized recommendation prototype",
        "version": "1.0.0",
    },
}


def deep_merge(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    """Return a recursively merged copy of ``base`` and ``updates``."""
    merged = dict(base)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


@lru_cache(maxsize=1)
def get_api_config() -> dict[str, Any]:
    """Load API config from config.json, with sensible defaults."""
    return deep_merge(DEFAULT_API_CONFIG, getattr(settings, "api", {}))


def env_value(env_name: str, default: str | None = None) -> str | None:
    """Read an environment variable with an optional default."""
    return os.getenv(env_name, default)


def resolve_ml_path(path_value: str | Path) -> Path:
    """Resolve a path relative to the ML root unless it is already absolute."""
    path = Path(path_value)
    return path if path.is_absolute() else (ML_ROOT / path).resolve()


def resolve_project_path(path_value: str | Path) -> Path:
    """Resolve a path relative to the project root unless it is already absolute."""
    path = Path(path_value)
    return path if path.is_absolute() else (PROJECT_ROOT / path).resolve()
