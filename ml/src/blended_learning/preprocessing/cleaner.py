"""Config-driven data cleaning pipeline for blended learning survey data.

The goal of this module is to keep notebook cells small and avoid repeated
hardcoded column names, thresholds, file paths, and output options. Most
behavior is controlled from `ml/config/config.json` under the `preprocessing`
key, while legacy top-level keys such as `drop_columns`, `rename_map`, and
`ordinal_column_scales` are still supported.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import uuid

import pandas as pd

from blended_learning.config.settings import Settings
from blended_learning.utils.decorator import execution_time


class DataCleaner:
    """Apply configured preprocessing steps to a survey DataFrame.

    Parameters
    ----------
    settings:
        Loaded project settings.
    df:
        Raw survey DataFrame. If omitted, use :meth:`load_raw_dataframe` first.
    """

    DEFAULT_PREPROCESSING_CONFIG: dict[str, Any] = {
        "io": {
            "input_path": "data/raw/kobo_latest_raw.xlsx",
            "output_cleaned_path": "data/processed/cleaned_data.csv",
            "read_excel_options": {"engine": "openpyxl"},
            "write_csv_options": {"index": False, "encoding": "utf-8-sig"},
        },
        "valid_response": {
            "column": "responses_based_on_year",
            "accepted_values": ["yes"],
        },
        "response_time": {
            "start_column": "survey_start",
            "end_column": "survey_end",
            "output_column": "response_time_minutes",
            "unit": "minutes",
        },
        "student_id": {
            "source_column": "itc_student_id",
            "valid_flag_column": "is_itc_student",
            "output_column": "student_id",
            "pattern_config_key": "student_id_pattern",
            "external_prefix": "ext_",
            "external_uuid_length": 10,
            "missing_tokens": ["", "nan", "none", "null"],
        },
        "duplicates": {
            "subset_column": "itc_student_id",
            "sort_column": "response_time_minutes",
            "ascending": True,
            "keep": "first",
        },
        "categorical_standardization": {
            "title_case_columns": ["gender"],
            "replace_then_title_case": {"province": {"old": "_", "new": " "}},
            "strip_columns": [
                "enrollment_status",
                "academic_year",
                "education_level",
                "major",
                "department",
                "faculty",
            ],
        },
        "speeder": {
            "output_column": "flag_speeder",
            "threshold_minutes": 3,
        },
        "ordinal_encoding": {
            "column_scales_config_key": "ordinal_column_scales",
            "scales_config_key": "scales",
            "warn_unmapped": True,
        },
        "pipeline_steps": [
            "drop_columns",
            "rename_columns",
            "remove_invalid_responses",
            "compute_response_time",
            "verify_student_itc",
            "remove_duplicates",
            "standardise_categoricals",
            "flag_speeder",
            "encode_ordinals",
        ],
    }

    def __init__(self, settings: Settings, df: pd.DataFrame | None = None) -> None:
        self.settings = settings
        self.cfg = self._merged_preprocessing_config()
        self.df = df.copy() if df is not None else pd.DataFrame()

    def _merged_preprocessing_config(self) -> dict[str, Any]:
        """Merge default preprocessing config with `settings.preprocessing`."""
        config = self._deep_copy(self.DEFAULT_PREPROCESSING_CONFIG)
        project_config = getattr(self.settings, "preprocessing", {})
        self._deep_update(config, project_config)
        return config

    @staticmethod
    def _deep_copy(value: dict[str, Any]) -> dict[str, Any]:
        return {
            key: DataCleaner._deep_copy(item) if isinstance(item, dict) else item
            for key, item in value.items()
        }

    @staticmethod
    def _deep_update(base: dict[str, Any], updates: dict[str, Any]) -> None:
        for key, value in updates.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                DataCleaner._deep_update(base[key], value)
            else:
                base[key] = value

    def _resolve_project_path(self, path_value: str | Path) -> Path:
        path = Path(path_value)
        if path.is_absolute():
            return path
        return (self.settings.root / path).resolve()

    @staticmethod
    def _normalise_series(series: pd.Series) -> pd.Series:
        return series.astype(str).str.strip().str.lower()

    def _missing_mask(self, series: pd.Series, missing_tokens: list[str]) -> pd.Series:
        tokens = {str(token).strip().lower() for token in missing_tokens}
        return series.isna() | self._normalise_series(series).isin(tokens)

    @execution_time
    def load_raw_dataframe(self) -> pd.DataFrame:
        """Load the raw survey file using config-driven input options."""
        io_cfg = self.cfg["io"]
        input_path = self._resolve_project_path(io_cfg["input_path"])
        read_options = dict(io_cfg.get("read_excel_options", {}))

        if not input_path.exists():
            raise FileNotFoundError(f"Raw input file not found: {input_path}")

        self.df = pd.read_excel(input_path, **read_options)
        return self.df

    @execution_time
    def save_cleaned_dataframe(self) -> Path:
        """Save the cleaned DataFrame using config-driven output options."""
        io_cfg = self.cfg["io"]
        output_path = self._resolve_project_path(io_cfg["output_cleaned_path"])
        output_path.parent.mkdir(parents=True, exist_ok=True)

        write_options = dict(io_cfg.get("write_csv_options", {}))
        self.df.to_csv(output_path, **write_options)
        return output_path

    @execution_time
    def drop_columns(self) -> "DataCleaner":
        """Drop configured columns that are not needed for analysis."""
        self.df = self.df.drop(
            columns=getattr(self.settings, "drop_columns", []),
            errors="ignore",
        )
        return self

    @execution_time
    def rename_columns(self) -> "DataCleaner":
        """Rename raw survey columns to standardized internal names."""
        self.df = self.df.rename(columns=getattr(self.settings, "rename_map", {}))
        return self

    @execution_time
    def remove_invalid_responses(self) -> "DataCleaner":
        """Keep only rows matching configured valid-response values."""
        valid_cfg = self.cfg["valid_response"]
        col = valid_cfg["column"]
        accepted_values = {
            str(value).strip().lower()
            for value in valid_cfg.get("accepted_values", [])
        }

        if col not in self.df.columns:
            raise KeyError(f"Configured valid-response column not found: {col}")

        mask = self._normalise_series(self.df[col]).isin(accepted_values)
        self.df = self.df[mask].copy()
        return self

    @execution_time
    def compute_response_time(self) -> "DataCleaner":
        """Compute survey response duration from configured start/end columns."""
        time_cfg = self.cfg["response_time"]
        start_col = time_cfg["start_column"]
        end_col = time_cfg["end_column"]
        output_col = time_cfg["output_column"]

        missing_cols = [col for col in [start_col, end_col] if col not in self.df.columns]
        if missing_cols:
            raise KeyError(f"Configured response-time columns not found: {missing_cols}")

        start = pd.to_datetime(self.df[start_col], errors="coerce")
        end = pd.to_datetime(self.df[end_col], errors="coerce")
        duration_seconds = (end - start).dt.total_seconds()

        unit = str(time_cfg.get("unit", "minutes")).lower()
        if unit == "seconds":
            self.df[output_col] = duration_seconds
        elif unit == "hours":
            self.df[output_col] = duration_seconds / 3600.0
        else:
            self.df[output_col] = duration_seconds / 60.0

        return self

    @execution_time
    def verify_student_itc(self) -> "DataCleaner":
        """Validate student IDs and create configured student-id columns."""
        id_cfg = self.cfg["student_id"]
        source_col = id_cfg["source_column"]
        flag_col = id_cfg["valid_flag_column"]
        output_col = id_cfg["output_column"]
        pattern_key = id_cfg.get("pattern_config_key", "student_id_pattern")
        pattern = getattr(self.settings, pattern_key)

        if source_col not in self.df.columns:
            raise KeyError(f"Configured student ID column not found: {source_col}")

        clean_ids = self.df[source_col].astype(str).str.strip()
        is_missing = self._missing_mask(self.df[source_col], id_cfg["missing_tokens"])

        self.df[flag_col] = clean_ids.str.match(pattern, na=False) & ~is_missing
        self.df.loc[is_missing, output_col] = [
            f"{id_cfg['external_prefix']}{uuid.uuid4().hex[:id_cfg['external_uuid_length']]}"
            for _ in range(int(is_missing.sum()))
        ]
        self.df.loc[~is_missing, output_col] = clean_ids.loc[~is_missing]
        return self

    @execution_time
    def remove_duplicates(self) -> "DataCleaner":
        """Drop duplicate configured student IDs while preserving non-student rows."""
        dup_cfg = self.cfg["duplicates"]
        id_col = dup_cfg["subset_column"]
        sort_col = dup_cfg["sort_column"]
        keep = dup_cfg.get("keep", "first")

        if id_col not in self.df.columns:
            raise KeyError(f"Configured duplicate ID column not found: {id_col}")

        id_cfg = self.cfg["student_id"]
        is_missing = self._missing_mask(self.df[id_col], id_cfg["missing_tokens"])
        id_df = self.df[~is_missing].copy()
        non_id_df = self.df[is_missing].copy()

        if sort_col in id_df.columns:
            id_df = id_df.sort_values(
                sort_col,
                ascending=bool(dup_cfg.get("ascending", True)),
            )

        id_df = id_df.loc[~id_df[id_col].duplicated(keep=keep)]
        self.df = pd.concat([id_df, non_id_df], ignore_index=True)
        return self

    @execution_time
    def standardise_categoricals(self) -> "DataCleaner":
        """Normalize categorical text columns using configured rules."""
        cat_cfg = self.cfg["categorical_standardization"]

        for col in cat_cfg.get("title_case_columns", []):
            if col in self.df.columns:
                self.df[col] = self.df[col].astype(str).str.strip().str.title()

        for col, rule in cat_cfg.get("replace_then_title_case", {}).items():
            if col in self.df.columns:
                self.df[col] = (
                    self.df[col]
                    .astype(str)
                    .str.strip()
                    .str.replace(rule.get("old", "_"), rule.get("new", " "), regex=False)
                    .str.title()
                )

        for col in cat_cfg.get("strip_columns", []):
            if col in self.df.columns:
                self.df[col] = self.df[col].astype(str).str.strip()

        return self

    @execution_time
    def flag_speeder(self) -> "DataCleaner":
        """Mark responses completed faster than the configured threshold."""
        speeder_cfg = self.cfg["speeder"]
        response_time_col = self.cfg["response_time"]["output_column"]
        output_col = speeder_cfg["output_column"]
        threshold = float(speeder_cfg["threshold_minutes"])

        if response_time_col not in self.df.columns:
            raise KeyError(f"Response-time column not found: {response_time_col}")

        self.df[output_col] = self.df[response_time_col] < threshold
        return self

    @execution_time
    def encode_ordinals(self) -> "DataCleaner":
        """Map ordinal survey responses to numeric values from configured scales."""
        ordinal_cfg = self.cfg["ordinal_encoding"]
        column_scales = getattr(self.settings, ordinal_cfg["column_scales_config_key"])
        scales = getattr(self.settings, ordinal_cfg["scales_config_key"])
        warn_unmapped = bool(ordinal_cfg.get("warn_unmapped", True))

        for col, scale_key in column_scales.items():
            if col not in self.df.columns:
                continue

            scale = scales.get(scale_key, {})
            self.df[col] = self.df[col].astype(str).str.strip().map(scale)

            unmapped = int(self.df[col].isna().sum())
            if warn_unmapped and unmapped > 0:
                print(f"[WARN] {col}: {unmapped} unmapped values")

        return self

    def run(self) -> "DataCleaner":
        """Run the configured preprocessing sequence."""
        for step_name in self.cfg["pipeline_steps"]:
            step = getattr(self, step_name)
            try:
                step()
            except Exception as exc:
                print(f"Error in step {step_name}: {exc}")
                raise

        return self
