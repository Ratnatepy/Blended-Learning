from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import StudentRecommendation
from api.schemas import StudentRecommendationResponse

router = APIRouter()


@router.get("/")
def get_all_students(
    limit: int = Query(1000, ge=1, le=5000),
    db: Session = Depends(get_db)
):
    """
    Return student recommendation records for the Student Records page.

    Default limit is 1000, enough for your original 420 records plus new demo records.
    """
    students = (
        db.query(StudentRecommendation)
        .order_by(StudentRecommendation.created_at.desc(), StudentRecommendation.student_id.asc())
        .limit(limit)
        .all()
    )

    return [
        {
            "student_id": student.student_id,
            "student_segment_label": student.student_segment_label,
            "final_recommendation_tags": student.final_recommendation_tags,
            "created_at": student.created_at,
        }
        for student in students
    ]


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


@router.get("/recent")
def get_recent_students(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Optional endpoint for checking recently added records.
    """
    students = (
        db.query(StudentRecommendation)
        .order_by(StudentRecommendation.created_at.desc())
        .limit(limit)
        .all()
    )

    return {
        "total_returned": len(students),
        "students": [
            {
                "student_id": student.student_id,
                "student_segment_label": student.student_segment_label,
                "final_recommendation_tags": student.final_recommendation_tags,
                "created_at": student.created_at,
            }
            for student in students
        ]
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