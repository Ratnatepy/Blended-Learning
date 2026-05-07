from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import StudentRecommendation
from api.schemas import StudentRecommendationResponse

router = APIRouter()


@router.get("/")
def get_students(limit: int = 20, db: Session = Depends(get_db)):
    students = (
        db.query(StudentRecommendation)
        .order_by(StudentRecommendation.student_id)
        .limit(limit)
        .all()
    )

    total = db.query(StudentRecommendation).count()

    return {
        "total": total,
        "students": [
            {
                "student_id": student.student_id,
                "student_segment_label": student.student_segment_label,
                "final_recommendation_tags": student.final_recommendation_tags,
                "llm_recommendation_report": student.llm_recommendation_report,
            }
            for student in students
        ]
    }


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    students = db.query(StudentRecommendation).all()

    total_students = len(students)

    segment_distribution = {}

    for student in students:
        segment = student.student_segment_label or "Unknown"
        segment_distribution[segment] = segment_distribution.get(segment, 0) + 1

    return {
        "total_students": total_students,
        "total_segments": len(segment_distribution),
        "segment_distribution": segment_distribution
    }


@router.get("/{student_id}", response_model=StudentRecommendationResponse)
def get_student_by_id(student_id: str, db: Session = Depends(get_db)):
    student = (
        db.query(StudentRecommendation)
        .filter(StudentRecommendation.student_id == student_id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail=f"Student ID {student_id} not found"
        )

    return student