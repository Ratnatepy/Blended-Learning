from __future__ import annotations

from datetime import datetime
import io
import os
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from blended_learning.config.settings import settings
from blended_learning.utils.decorator import execution_time


class KoboSync:
    """
    Synchronize the latest KoboToolbox XLS export into local raw/archive files.

    Runtime secrets stay in `.env` / environment variables:
        - KOBO_BASE_URL
        - KOBO_TOKEN
        - KOBO_ASSET_UID

    Non-secret behavior is controlled from `ml/config/config.json`:
        data_collection.kobo
    """

    DEFAULT_CONFIG: dict[str, Any] = {
        "env": {
            "base_url": "KOBO_BASE_URL",
            "token": "KOBO_TOKEN",
            "asset_uid": "KOBO_ASSET_UID",
        },
        "export_settings_endpoint": "/api/v2/assets/{asset_uid}/export-settings/",
        "preferred_export_key": "data_url_xlsx",
        "request_timeout_seconds": {
            "export_settings": 30,
            "download": 120,
        },
        "excel_read_options": {
            "engine": "openpyxl",
            "dtype": "str",
            "keep_default_na": False,
            "na_filter": False,
        },
        "output": {
            "raw_dir": "data/raw",
            "archive_dir": "data/archive",
            "processed_dir": "data/processed",
            "latest_parquet": "kobo_latest_raw.parquet",
            "latest_xlsx": "kobo_latest_raw.xlsx",
            "archive_prefix": "kobo_raw",
            "timestamp_format": "%Y%m%d_%H%M%S",
        },
    }

    def __init__(self) -> None:
        self.cfg = self._merged_config()

        env_cfg = self.cfg["env"]
        self.base_url = self._required_env(env_cfg["base_url"]).rstrip("/")
        self.token = self._required_env(env_cfg["token"])
        self.asset_uid = self._required_env(env_cfg["asset_uid"])

        output_cfg = self.cfg["output"]
        self.raw_dir = self._resolve_project_path(output_cfg["raw_dir"])
        self.archive_dir = self._resolve_project_path(output_cfg["archive_dir"])
        self.processed_dir = self._resolve_project_path(output_cfg["processed_dir"])

    def _merged_config(self) -> dict[str, Any]:
        """Merge defaults with `settings.data_collection.kobo`."""
        config = self._deep_copy(self.DEFAULT_CONFIG)
        project_config = getattr(settings, "data_collection", {}).get("kobo", {})
        self._deep_update(config, project_config)
        return config

    @staticmethod
    def _deep_copy(value: dict[str, Any]) -> dict[str, Any]:
        return {
            key: KoboSync._deep_copy(item) if isinstance(item, dict) else item
            for key, item in value.items()
        }

    @staticmethod
    def _deep_update(base: dict[str, Any], updates: dict[str, Any]) -> None:
        for key, value in updates.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                KoboSync._deep_update(base[key], value)
            else:
                base[key] = value

    @staticmethod
    def _required_env(env_name: str) -> str:
        value = os.getenv(env_name)
        if value is None or str(value).strip() == "":
            raise RuntimeError(
                f"Missing required environment variable `{env_name}`. "
                "Set it in `ml/.env` or in your shell environment."
            )
        return str(value).strip()

    @staticmethod
    def _resolve_project_path(path_value: str | Path) -> Path:
        path = Path(path_value)
        if path.is_absolute():
            return path
        return (settings.root / path).resolve()

    def _export_settings_url(self) -> str:
        endpoint = self.cfg["export_settings_endpoint"].format(
            asset_uid=self.asset_uid
        )
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def fetch(self) -> bytes:
        """Download the XLSX bytes from the saved Kobo export settings."""
        headers = {"Authorization": f"Token {self.token}"}
        timeouts = self.cfg["request_timeout_seconds"]
        preferred_key = self.cfg["preferred_export_key"]

        res = requests.get(
            self._export_settings_url(),
            headers=headers,
            timeout=timeouts["export_settings"],
        )
        res.raise_for_status()

        results = res.json().get("results", [])
        if not results:
            raise LookupError("No saved export settings found in KoboToolbox.")

        setting = next(
            (item for item in results if item.get(preferred_key)),
            results[0],
        )
        xlsx_url = setting.get(preferred_key)
        if not xlsx_url:
            raise LookupError(f"Missing `{preferred_key}` in Kobo export setting.")

        response = requests.get(
            xlsx_url,
            headers=headers,
            timeout=timeouts["download"],
        )
        response.raise_for_status()
        return response.content

    def load(self, xls_bytes: bytes) -> pd.DataFrame:
        """Load XLSX bytes into a DataFrame using config-driven read options."""
        read_options = dict(self.cfg["excel_read_options"])

        # JSON cannot store the Python `str` type, so config uses the string "str".
        if read_options.get("dtype") == "str":
            read_options["dtype"] = str

        df = pd.read_excel(io.BytesIO(xls_bytes), **read_options)
        if df.empty:
            raise ValueError("No data in XLS export.")
        return df

    def save(self, df: pd.DataFrame, xls_bytes: bytes) -> None:
        """Save latest raw data and timestamped archive files."""
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        output_cfg = self.cfg["output"]
        timestamp = datetime.now().strftime(output_cfg["timestamp_format"])
        archive_stem = f"{output_cfg['archive_prefix']}_{timestamp}"

        df.to_parquet(self.archive_dir / f"{archive_stem}.parquet", index=False)
        df.to_parquet(self.raw_dir / output_cfg["latest_parquet"], index=False)

        (self.archive_dir / f"{archive_stem}.xlsx").write_bytes(xls_bytes)
        (self.raw_dir / output_cfg["latest_xlsx"]).write_bytes(xls_bytes)

    @execution_time
    def run(self) -> pd.DataFrame:
        print("Starting Kobo XLS sync...")
        xls_bytes = self.fetch()
        df = self.load(xls_bytes)
        self.df = df
        self.save(df, xls_bytes)
        print("Kobo XLS sync completed successfully")
        return df
