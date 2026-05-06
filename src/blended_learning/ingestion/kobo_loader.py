from __future__ import annotations
from datetime import datetime
import io
import pandas as pd
import requests

from blended_learning.config.settings import settings
from blended_learning.utils.decorator import execution_time

class KoboSync:

    def __init__(self):
        self.base_url   = settings.KOBO_BASE_URL.rstrip("/")
        self.token      = settings.KOBO_TOKEN
        self.asset_uid  = settings.KOBO_ASSET_UID

        self.raw_dir    = settings.root / "data" / "raw"
        self.archive_dir= settings.root / "data" / "archive"
        self.processed_dir= settings.root / "data" / "processed"

    def fetch(self) -> bytes:
        headers = {"Authorization": f"Token {self.token}"}
        url     = f"{self.base_url}/api/v2/assets/{self.asset_uid}/export-settings/"

        res = requests.get(url, headers=headers, timeout=30)
        res.raise_for_status()

        results = res.json().get("results", [])
        if not results:
            raise LookupError("No saved export settings found in KoboToolbox.")
        
        setting = next(
            (s for s in results if s.get("data_url_xlsx")),
            results[0]
        )
        xlsx_url = setting.get("data_url_xlsx")

        if not xlsx_url:
            raise LookupError("Missing data_url_xlsx in export setting.")
        
        response = requests.get(xlsx_url, headers=headers, timeout=120)
        response.raise_for_status()
        return response.content
    
    def load(self, xls_bytes: bytes):
        df = pd.read_excel(
            io.BytesIO(xls_bytes),
            engine="openpyxl",
            dtype=str,
            keep_default_na=False,
            na_filter=False
        )
        if df.empty:
            raise ValueError("No data in XLS export.")
        return df
    
    def save(self, df, xls_bytes: bytes):
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        df.to_parquet(
            self.archive_dir / f"kobo_raw_{ts}.parquet",
            index=False
        )

        df.to_parquet(
            self.raw_dir / "kobo_latest_raw.parquet",
            index=False
        )

        (self.archive_dir / f"kobo_raw_{ts}.xlsx").write_bytes(xls_bytes)
        (self.raw_dir / "kobo_latest_raw.xlsx").write_bytes(xls_bytes)
    
    @execution_time
    def run(self):
        print("Starting Kobo XLS sync...")
        xls_bytes = self.fetch()
        df = self.load(xls_bytes)
        self.df = df
        self.save(df, xls_bytes)
        print("Kobo XLS sync completed successfully")
        return df
