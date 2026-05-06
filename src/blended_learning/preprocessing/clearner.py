

"""Data cleaning pipeline for blended learning survey data.

This module defines a small, step-based cleaner that applies the
configured operations defined in `Settings` to a pandas DataFrame.
"""

from __future__ import annotations
import uuid

import pandas as pd
from pandas import isna

from blended_learning.config.settings import Settings
from blended_learning.utils.decorator import execution_time


class DataCleaner:
    """Apply cleaning operations to a survey DataFrame.

    Parameters
    ----------
    settings : Settings
        Loaded configuration values and mappings used by the cleaner.
    df : pd.DataFrame
        Raw survey data that will be transformed in place.
    """

    def __init__(self, settings: Settings, df: pd.DataFrame) -> None:
        self.settings = settings
        self.df = df

    @execution_time
    def drop_columns(self):
        """Drop configured columns that are not needed for analysis."""
        self.df = self.df.drop(
            columns=self.settings.drop_columns,
            errors="ignore",
        )
        return self

    @execution_time
    def rename_columns(self):
        """Rename raw survey columns to standardized internal names."""
        self.df = self.df.rename(columns=self.settings.rename_map)
        return self

    @execution_time
    def remove_invalid_responses(self):
        """Keep only rows that indicate a valid academic year response."""
        col = "responses_based_on_year"
        self.df = self.df[
            self.df[col]
            .astype(str)
            .str.strip()
            .str.lower()
            == "yes"
        ].copy()
        return self

    @execution_time
    def compute_response_time(self):
        """Compute survey response duration in minutes."""
        self.df["response_time_minutes"] = (
            self.df["survey_end"] - self.df["survey_start"]
        ).dt.total_seconds() / 60.0
        return self

    @execution_time
    def verify_student_itc(self):
        """Flag student records that match the configured ITC student ID pattern."""
        col = "itc_student_id"
        self.df["is_itc_student"] = (
            self.df[col]
            .astype(str)
            .str.strip()
            .str.match(self.settings.student_id_pattern)
        )

        is_missing = (
            self.df[col].isna() |
            (self.df[col].astype(str).str.strip() == "") | 
            (self.df[col].astype(str).str.lower() == "nan")
        )

        self.df.loc[is_missing, "student_id"] = [
            f"ext_{uuid.uuid4().hex[:10]}"
            for _ in range(is_missing.sum())
        ]

        # 4. For valid ones, keep original ITC ID
        self.df.loc[~is_missing, "student_id"] = (
            self.df.loc[~is_missing, col].astype(str).str.strip()
        )

        return self

    @execution_time
    def remove_duplicates(self) -> "DataCleaner":
        """Drop duplicate ITC student records while preserving the first valid response."""
        df = self.df.copy()

        itc_df = df[df["itc_student_id"].notna()].copy()
        non_itc_df = df[df["itc_student_id"].isna()].copy()

        if "response_time_minutes" in itc_df.columns:
            itc_df = itc_df.sort_values(
                "response_time_minutes",
                ascending=True,
            )

        itc_df = itc_df.loc[
            ~itc_df["itc_student_id"].duplicated(keep="first")
        ]

        self.df = pd.concat(
            [itc_df, non_itc_df],
            ignore_index=True,
        )
        return self

    @execution_time
    def flag_speeder(self):
        """Mark responses completed faster than the configured threshold."""
        threshold = self.settings.speeder_threshold_minutes
        self.df["flag_speeder"] = self.df["response_time_minutes"] < threshold
        return self

    @execution_time
    def standardise_categoricals(self):
        """Normalize categorical text columns and title-case gender/province values."""
        if "gender" in self.df.columns:
            self.df["gender"] = self.df["gender"].str.strip().str.title()

        if "province" in self.df.columns:
            self.df["province"] = (
                self.df["province"]
                .str.strip()
                .str.replace("_", " ", regex=False)
                .str.title()
            )

        categorical_cols = [
            "enrollment_status",
            "academic_year",
            "education_level",
            "major",
            "department",
            "faculty",
        ]

        for col in categorical_cols:
            if col in self.df.columns:
                self.df[col] = self.df[col].astype(str).str.strip()

        return self

    @execution_time
    def encode_ordinals(self):
        """Map ordinal survey responses to numeric values from the config."""
        for col, scale_key in self.settings.ordinal_column_scales.items():
            if col not in self.df.columns:
                continue

            scale = self.settings.scales.get(scale_key, {})
            self.df[col] = (
                self.df[col]
                .astype(str)
                .str.strip()
                .map(scale)
            )

            unmapped = self.df[col].isna().sum()
            if unmapped > 0:
                print(f"[WARN] {col}: {unmapped} unmapped values")

        return self

    def run(self):
        """Run the full sequence of cleaning steps on the attached DataFrame."""
        steps = [
            self.drop_columns,
            self.rename_columns,
            self.remove_invalid_responses,
            self.compute_response_time,
            self.verify_student_itc,
            self.remove_duplicates,
            self.standardise_categoricals,
            self.flag_speeder,
            self.encode_ordinals,
        ]

        for step in steps:
            try:
                step()
            except Exception as e:
                print(f"Error in step {step.__name__}: {e}")
                raise e

        return self
