from __future__ import annotations

from pathlib import Path
import sys
from typing import Iterable


def find_ml_root(start: str | Path | None = None) -> Path:
    """Find the ml project root that contains both config/config.json and src/.

    This lets notebooks run from either ``project/ml`` or ``project/ml/notebook``.
    """
    current = Path(start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "config" / "config.json").exists() and (candidate / "src").exists():
            return candidate
    raise FileNotFoundError(
        "Could not find the ml project root containing config/config.json and src/."
    )


def add_src_to_path(ml_root: str | Path | None = None) -> Path:
    """Add the ml/src folder to sys.path and return the resolved ml root."""
    root = find_ml_root(ml_root)
    src_path = root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    return root


def resolve_project_path(path_value: str | Path, root: str | Path | None = None) -> Path:
    """Resolve a config path relative to the ml root unless it is already absolute."""
    path = Path(path_value)
    if path.is_absolute():
        return path
    return (find_ml_root(root) / path).resolve()


def require_config_keys(config: dict, keys: Iterable[str], context: str = "config") -> None:
    """Raise a helpful error when a config section is missing expected keys."""
    missing = [key for key in keys if key not in config]
    if missing:
        raise KeyError(f"Missing keys in {context}: {missing}")
