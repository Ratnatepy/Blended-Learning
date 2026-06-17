from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
from sklearn.metrics import silhouette_score


def numeric_gower_distance_matrix(
    values: pd.DataFrame,
    scale_min: float = 1.0,
    scale_max: float = 5.0,
    chunk_size: int = 128,
) -> np.ndarray:
    """Compute a Gower-style distance matrix for same-scale numeric ordinal variables.

    For encoded Likert variables on the same scale, Gower distance simplifies to
    the mean normalized absolute difference across variables.
    """
    arr = values.to_numpy(dtype=float)
    denom = float(scale_max) - float(scale_min)
    if denom <= 0:
        raise ValueError("scale_max must be greater than scale_min.")

    arr = np.clip(arr, float(scale_min), float(scale_max))
    scaled = (arr - float(scale_min)) / denom
    n_rows = scaled.shape[0]
    distances = np.zeros((n_rows, n_rows), dtype=np.float32)

    for start in range(0, n_rows, int(chunk_size)):
        stop = min(start + int(chunk_size), n_rows)
        distances[start:stop, :] = np.abs(
            scaled[start:stop, None, :] - scaled[None, :, :]
        ).mean(axis=2)

    np.fill_diagonal(distances, 0.0)
    return distances


def fit_hierarchical_from_distance(distance_matrix: np.ndarray, method: str = "average") -> np.ndarray:
    """Fit hierarchical linkage from a square precomputed distance matrix."""
    condensed = squareform(distance_matrix, checks=False)
    return linkage(condensed, method=method)


def evaluate_hierarchical_k_range(
    distance_matrix: np.ndarray,
    linkage_matrix: np.ndarray,
    k_values: list[int],
    criterion: str = "maxclust",
) -> pd.DataFrame:
    """Evaluate silhouette and balance diagnostics for candidate K values."""
    rows = []
    for k in k_values:
        labels = fcluster(linkage_matrix, t=int(k), criterion=criterion)
        counts = pd.Series(labels).value_counts().sort_index()
        try:
            sil = silhouette_score(distance_matrix, labels, metric="precomputed")
        except Exception:
            sil = np.nan
        rows.append(
            {
                "k": int(k),
                "silhouette": sil,
                "min_cluster_size": int(counts.min()),
                "max_cluster_size": int(counts.max()),
                "balance_ratio": float(counts.min() / counts.max()) if counts.max() else np.nan,
            }
        )
    return pd.DataFrame(rows)
