from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


def cronbach_alpha(data: pd.DataFrame) -> tuple[float, int, int]:
    """Compute Cronbach's alpha for complete cases across the given items."""
    numeric = data.apply(pd.to_numeric, errors="coerce").dropna(axis=0, how="any")
    n_valid = len(numeric)
    k_items = numeric.shape[1]

    if k_items < 2 or n_valid == 0:
        return np.nan, n_valid, k_items

    item_variances = numeric.var(axis=0, ddof=1)
    total_score = numeric.sum(axis=1)
    total_variance = total_score.var(ddof=1)

    if total_variance == 0 or pd.isna(total_variance):
        return np.nan, n_valid, k_items

    alpha = (k_items / (k_items - 1)) * (1 - item_variances.sum() / total_variance)
    return float(alpha), int(n_valid), int(k_items)


def interpret_alpha(alpha: float, thresholds: list[dict]) -> str:
    """Interpret Cronbach's alpha using ordered thresholds from config.json."""
    if pd.isna(alpha):
        return "Not available"
    for rule in thresholds:
        min_value = rule.get("min")
        if min_value is None or alpha >= min_value:
            return rule["label"]
    return "Not available"


def alpha_if_item_deleted(data: pd.DataFrame) -> pd.DataFrame:
    """Compute alpha after deleting each item one by one."""
    rows = []
    for item in data.columns:
        remaining = [column for column in data.columns if column != item]
        alpha, n_valid, k_items = cronbach_alpha(data[remaining])
        rows.append(
            {
                "Deleted Item": item,
                "Remaining Items": k_items,
                "Valid Responses": n_valid,
                "Alpha if Item Deleted": round(alpha, 3) if not pd.isna(alpha) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def validate_item_columns(data: pd.DataFrame, columns: Iterable[str], context: str) -> None:
    """Validate configured reliability items before running alpha."""
    missing = [column for column in columns if column not in data.columns]
    if missing:
        raise KeyError(f"Missing reliability columns for {context}: {missing}")


def slugify_filename(value: str, suffix: str = ".csv") -> str:
    """Create a stable lowercase filename from a construct name."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", str(value).strip().lower()).strip("_")
    return f"{slug}{suffix}"


def save_alpha_if_deleted_tables(
    data: pd.DataFrame,
    constructs: dict[str, list[str]],
    output_dir: str | Path,
    write_options: dict | None = None,
) -> dict[str, Path]:
    """Save alpha-if-item-deleted tables for all configured constructs."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    saved: dict[str, Path] = {}
    for construct, items in constructs.items():
        table = alpha_if_item_deleted(data[items])
        path = output_dir / slugify_filename(f"alpha_if_deleted_{construct}")
        table.to_csv(path, **(write_options or {}))
        saved[construct] = path
    return saved


def slugify_construct_name(value: str) -> str:
    """Backward-compatible construct-name slug used by reliability notebooks."""
    return re.sub(r"[^a-zA-Z0-9]+", "_", str(value).strip().lower()).strip("_")
