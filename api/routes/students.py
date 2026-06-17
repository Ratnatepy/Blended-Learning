"""Student record and dashboard endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.core.segments import clean_report_text, normalize_segment_label
from api.database import get_db
from api.models import StudentRecommendation
from api.schemas import DashboardSummary, StudentListItem, StudentRecommendationResponse

router = APIRouter()


def student_to_response(student: StudentRecommendation) -> StudentRecommendationResponse:
    """Convert a database object to a clean API response."""
    return StudentRecommendationResponse(
        student_id=student.student_id,
        student_segment_label=normalize_segment_label(student.student_segment_label),
        final_recommendation_tags=student.final_recommendation_tags,
        llm_recommendation_report=clean_report_text(student.llm_recommendation_report),
        created_at=student.created_at,
    )


def student_to_list_item(student: StudentRecommendation) -> StudentListItem:
    """Return compact student fields used by list/dashboard pages."""
    return StudentListItem(
        student_id=student.student_id,
        student_segment_label=normalize_segment_label(student.student_segment_label),
        final_recommendation_tags=student.final_recommendation_tags,
        created_at=student.created_at,
    )


@router.get("/", response_model=list[StudentListItem])
def get_all_students(
    limit: int = Query(1000, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    """Return student recommendation records for the Student Records page."""
    students = (
        db.query(StudentRecommendation)
        .order_by(StudentRecommendation.created_at.desc(), StudentRecommendation.student_id.asc())
        .limit(limit)
        .all()
    )
    return [student_to_list_item(student) for student in students]


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Return dashboard summary with normalized segment labels."""
    students = db.query(StudentRecommendation).all()
    segment_distribution: dict[str, int] = {}

    for student in students:
        segment = normalize_segment_label(student.student_segment_label)
        segment_distribution[segment] = segment_distribution.get(segment, 0) + 1

    return DashboardSummary(
        total_students=len(students),
        total_segments=len(segment_distribution),
        segment_distribution=segment_distribution,
    )


@router.get("/recent")
def get_recent_students(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Return recently added recommendation records."""
    students = (
        db.query(StudentRecommendation)
        .order_by(StudentRecommendation.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "total_returned": len(students),
        "students": [student_to_list_item(student).dict() for student in students],
    }


@router.get("/{student_id}", response_model=StudentRecommendationResponse)
def get_student_by_id(student_id: str, db: Session = Depends(get_db)):
    student = (
        db.query(StudentRecommendation)
        .filter(StudentRecommendation.student_id == student_id)
        .first()
    )

    if not student:
        raise HTTPException(status_code=404, detail=f"Student ID {student_id} not found")

    return student_to_response(student)
