from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


def resolve_path_from_settings(settings, path_or_key: str | Path, *, from_path_dict: bool = False) -> Path:
    """Resolve either a literal config path or a key from settings.path."""
    raw = settings.path[str(path_or_key)] if from_path_dict else path_or_key
    path = Path(raw)
    return path if path.is_absolute() else (settings.root / path).resolve()


def require_columns(data: pd.DataFrame, columns: Iterable[str], context: str = "dataframe") -> None:
    """Validate that a dataframe contains required columns."""
    missing = [column for column in columns if column not in data.columns]
    if missing:
        raise KeyError(f"Missing columns for {context}: {missing}")


def read_csv_configured(path: str | Path, options: dict | None = None) -> pd.DataFrame:
    """Read a CSV file using options from config.json."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    return pd.read_csv(path, **(options or {}))


def write_csv_configured(data: pd.DataFrame, path: str | Path, options: dict | None = None) -> Path:
    """Write a CSV file using options from config.json and return the saved path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(path, **(options or {}))
    return path
