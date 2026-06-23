"""Seed stored recommendation reports from the configured CSV file."""

from __future__ import annotations

import os
from pathlib import Path
import pandas as pd
from sqlalchemy.orm import Session

from api.core.config import get_api_config, resolve_ml_path
from api.core.segments import clean_report_text, normalize_segment_label
from api.models import StudentRecommendation


def _seed_cfg() -> dict:
    return get_api_config().get("seed", {})

CSV_PATH = Path(
    os.getenv(
        "SEED_CSV_PATH",
        "/app/ml/data/processed/student_recommendation_reports_current.csv"
    )
)

def _log(message: str) -> None:
    prefix = _seed_cfg().get("log_prefix", "[seed]")
    print(f"{prefix} {message}")


def load_seed_dataframe() -> pd.DataFrame | None:
    """Load and validate the configured seed CSV."""
    cfg = _seed_cfg()
    csv_path = resolve_ml_path(cfg.get("csv_path", "data/processed/student_recommendation_reports_current.csv"))

    if not csv_path.exists():
        _log(f"CSV file not found: {csv_path}")
        return None

    df = pd.read_csv(csv_path)
    required_columns = cfg.get("required_columns", [])
    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns in seed CSV: {missing_columns}")

    student_id_col = cfg.get("student_id_column", "student_id")
    df[student_id_col] = df[student_id_col].astype(str).str.strip()
    df = df[df[student_id_col] != ""].copy()
    df = df.drop_duplicates(
        subset=student_id_col,
        keep=cfg.get("deduplicate_keep", "last"),
    )

    return df


def seed_student_recommendations(db: Session) -> None:
    """Synchronize the recommendation table with the configured report CSV."""
    cfg = _seed_cfg()
    if not cfg.get("enabled", True):
        _log("Seeding is disabled in config. Skipping.")
        return

    _log("Checking database seed...")
    df = load_seed_dataframe()
    if df is None:
        return

    existing_count = db.query(StudentRecommendation).count()
    csv_count = len(df)
    _log(f"Database student records: {existing_count}")
    _log(f"CSV student records: {csv_count}")

    if existing_count == csv_count:
        _log(f"Database already matches CSV with {existing_count} records. Skipping seed.")
        return

    if not cfg.get("replace_when_count_differs", True):
        _log("Database count differs from CSV, but replacement is disabled. Skipping seed.")
        return

    _log("Database count does not match CSV. Reseeding...")
    db.query(StudentRecommendation).delete()
    db.commit()

    inserted = 0
    for _, row in df.iterrows():
        student = StudentRecommendation(
            student_id=str(row["student_id"]),
            student_segment_label=normalize_segment_label(row["student_segment_label"]),
            final_recommendation_tags=str(row["final_recommendation_tags"]),
            llm_recommendation_report=clean_report_text(str(row["llm_recommendation_report"])),
        )
        db.add(student)
        inserted += 1

    db.commit()
    final_count = db.query(StudentRecommendation).count()
    _log(f"Seeded {inserted} student recommendation records into the database.")
    _log(f"Database now has {final_count} student recommendation records.")
