"""Student recommendation persistence helpers."""

from __future__ import annotations

from sqlalchemy.orm import Session

from api.models import StudentRecommendation, StudentResponseInput


def get_recommendation_by_student_id(db: Session, student_id: str) -> StudentRecommendation | None:
    return (
        db.query(StudentRecommendation)
        .filter(StudentRecommendation.student_id == student_id)
        .first()
    )


def get_response_input_by_student_id(db: Session, student_id: str) -> StudentResponseInput | None:
    return (
        db.query(StudentResponseInput)
        .filter(StudentResponseInput.student_id == student_id)
        .first()
    )


def student_id_exists(db: Session, student_id: str) -> bool:
    return bool(
        get_recommendation_by_student_id(db, student_id)
        or get_response_input_by_student_id(db, student_id)
    )


def create_generated_student_records(
    db: Session,
    *,
    student_id: str,
    response_data: dict,
    assigned_cluster_label: str,
    final_recommendation_tags: str,
    llm_recommendation_report: str,
) -> StudentRecommendation:
    response_input = StudentResponseInput(
        student_id=student_id,
        response_data=response_data,
        assigned_cluster_label=assigned_cluster_label,
    )
    recommendation = StudentRecommendation(
        student_id=student_id,
        student_segment_label=assigned_cluster_label,
        final_recommendation_tags=final_recommendation_tags,
        llm_recommendation_report=llm_recommendation_report,
    )
    db.add(response_input)
    db.add(recommendation)
    return recommendation
