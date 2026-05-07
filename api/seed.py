from pathlib import Path
import pandas as pd
from sqlalchemy.orm import Session

from api.models import StudentRecommendation

CSV_PATH = Path("data/processed/student_recommendation_reports.csv")


def seed_student_recommendations(db: Session):
    print("Checking database seed...")

    existing_count = db.query(StudentRecommendation).count()

    if existing_count > 0:
        print(f"Database already has {existing_count} student records. Skipping seed.")
        return

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

    print(f"Seeded {inserted} student recommendation records into PostgreSQL.")