from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import normalized_mutual_info_score


def modal_profile(data: pd.DataFrame, label_col: str, columns: list[str]) -> pd.DataFrame:
    """Return the modal response profile for each cluster."""
    return data.groupby(label_col)[columns].agg(
        lambda x: x.mode().iloc[0] if not x.mode().empty else np.nan
    )


def build_auto_cluster_name_map(
    data: pd.DataFrame,
    label_col: str,
    columns: list[str],
    segment_label_config: dict,
    negative_vars: list[str] | None = None,
) -> tuple[dict[int, str], pd.Series, list[int]]:
    """Assign semantic segment labels based on profile engagement score.

    Higher average score after reverse-scoring configured negative variables is
    treated as more engaged. This avoids relying on unstable cluster ID numbers.
    """
    negative_vars = negative_vars or segment_label_config.get("negative_vars", [])
    profile = modal_profile(data, label_col=label_col, columns=columns)
    profile_score = profile.copy()
    reverse_sum = (
        segment_label_config.get("reverse_score_min", 1)
        + segment_label_config.get("reverse_score_max", 5)
    )
    for col in negative_vars:
        if col in profile_score.columns:
            profile_score[col] = reverse_sum - profile_score[col]

    engagement_score = profile_score.mean(axis=1)
    ranked_clusters = engagement_score.sort_values(ascending=False).index.astype(int).tolist()

    if len(ranked_clusters) == 2:
        cluster_name_map = {
            ranked_clusters[0]: segment_label_config["positive_label"],
            ranked_clusters[1]: segment_label_config["moderate_label"],
        }
    else:
        cluster_name_map = {
            ranked_clusters[0]: segment_label_config["positive_label"],
            ranked_clusters[-1]: segment_label_config.get("low_label", segment_label_config["moderate_label"]),
        }
        for cluster_id in ranked_clusters[1:-1]:
            cluster_name_map[cluster_id] = segment_label_config.get("middle_label", segment_label_config["moderate_label"])

    return cluster_name_map, engagement_score, ranked_clusters


def add_segment_labels(
    data: pd.DataFrame,
    labels: np.ndarray,
    columns: list[str],
    segment_label_config: dict,
) -> tuple[pd.DataFrame, dict[int, str], pd.Series, list[int]]:
    """Add numeric and semantic segment columns to a dataframe."""
    output = data.copy()
    id_col = segment_label_config["id_column"]
    label_col = segment_label_config["label_column"]
    output[id_col] = labels.astype(int)
    cluster_name_map, engagement_score, ranked_clusters = build_auto_cluster_name_map(
        output,
        label_col=id_col,
        columns=columns,
        segment_label_config=segment_label_config,
    )
    output[label_col] = output[id_col].map(cluster_name_map)
    existing_order = [
        label
        for label in segment_label_config.get("preferred_order", [])
        if label in output[label_col].dropna().unique()
    ]
    if existing_order:
        output[label_col] = pd.Categorical(output[label_col], categories=existing_order, ordered=True)
    return output, cluster_name_map, engagement_score, ranked_clusters


def pairwise_nmi(label_list: list[np.ndarray]) -> tuple[float, float]:
    """Compute mean and standard deviation of pairwise NMI across label arrays."""
    scores = [
        normalized_mutual_info_score(label_list[i], label_list[j])
        for i in range(len(label_list))
        for j in range(i + 1, len(label_list))
    ]
    return float(np.mean(scores)), float(np.std(scores))


def balance_cv(labels: np.ndarray) -> float:
    """Coefficient of variation of cluster sizes."""
    _, counts = np.unique(labels, return_counts=True)
    return float(counts.std() / counts.mean()) if counts.mean() > 0 else np.inf


def cluster_size_summary(labels: np.ndarray) -> tuple[int, int]:
    """Return min and max cluster size."""
    _, counts = np.unique(labels, return_counts=True)
    return int(counts.min()), int(counts.max())
