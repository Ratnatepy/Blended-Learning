import os
from pathlib import Path
import pandas as pd
from sqlalchemy.orm import Session

from api.models import StudentRecommendation

# This file must have 588 rows
CSV_PATH = Path(
    os.getenv(
        "SEED_CSV_PATH",
        "/app/ml/data/processed/student_recommendation_reports_current.csv"
    )
)

def seed_student_recommendations(db: Session):
    print("Checking database seed...")

    if not CSV_PATH.exists():
        print(f"CSV file not found: {CSV_PATH.resolve()}")
        return

    df = pd.read_csv(CSV_PATH)

    required_columns = [
        "student_id",
        "student_segment_label",
        "final_recommendation_tags",
        "llm_recommendation_report",
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"Missing required columns in CSV: {missing_columns}")

    # Clean duplicate student_id in CSV
    df["student_id"] = df["student_id"].astype(str).str.strip()
    df = df[df["student_id"] != ""].copy()
    df = df.drop_duplicates(subset="student_id", keep="last")

    existing_count = db.query(StudentRecommendation).count()
    csv_count = len(df)

    print(f"Database student records: {existing_count}")
    print(f"CSV student records: {csv_count}")

    # Only skip if database count matches CSV count
    if existing_count == csv_count:
        print(f"Database already matches CSV with {existing_count} records. Skipping seed.")
        return

    print("Database count does not match CSV. Reseeding...")

    # Clear old records
    db.query(StudentRecommendation).delete()
    db.commit()

    inserted = 0

    for _, row in df.iterrows():
        student = StudentRecommendation(
            student_id=str(row["student_id"]),
            student_segment_label=str(row["student_segment_label"]),
            final_recommendation_tags=str(row["final_recommendation_tags"]),
            llm_recommendation_report=str(row["llm_recommendation_report"]),
        )

        db.add(student)
        inserted += 1

    db.commit()

    final_count = db.query(StudentRecommendation).count()

    print(f"Seeded {inserted} student recommendation records into PostgreSQL.")
    print(f"Database now has {final_count} student recommendation records.")