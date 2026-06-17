"""API package bootstrap.

This ensures the FastAPI backend can import the reusable ML package during
local execution, tests, and Docker runs.
"""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ML_SRC_DIR = PROJECT_ROOT / "ml" / "src"

if ML_SRC_DIR.exists() and str(ML_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(ML_SRC_DIR))
