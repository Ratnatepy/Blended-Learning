"""Endpoints for generating recommendations for new student inputs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.database import get_db
from api.llm_service import generate_new_student_report_with_llm
from api.nlp_tags import extract_open_response_tags, tags_to_json
from api.repositories.students import create_generated_student_records, student_id_exists
from api.schemas import NewStudentInput, NewStudentRecommendation
from api.services.kmodes import get_kmodes_service

router = APIRouter()


def _build_response_audit_payload(
    payload: NewStudentInput,
    nlp_result: dict,
    llm_generation_source: str,
) -> dict:
    return {
        "survey_responses": payload.responses,
        "open_ended_responses": {
            "strengths_positive_aspects": payload.strengths_positive_aspects,
            "challenges_suggestions": payload.challenges_suggestions,
        },
        "nlp_extraction": nlp_result,
        "llm_generation_source": llm_generation_source,
    }


@router.post("/generate", response_model=NewStudentRecommendation)
def generate_recommendation(payload: NewStudentInput, db: Session = Depends(get_db)):
    """Generate, save, and return a personalized recommendation report."""
    student_id = payload.student_id.strip()
    if not student_id:
        raise HTTPException(status_code=400, detail="student_id cannot be empty.")

    if student_id_exists(db, student_id):
        raise HTTPException(
            status_code=409,
            detail=(
                f"Student ID '{student_id}' already exists. "
                "This record is protected and will not be overwritten. "
                "Please use a new student ID for new input testing."
            ),
        )

    try:
        prediction = get_kmodes_service().predict(payload.responses)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    nlp_result = extract_open_response_tags(
        strengths_positive_aspects=payload.strengths_positive_aspects,
        challenges_suggestions=payload.challenges_suggestions,
        segment_label=prediction.cluster_label,
    )
    recommendation_tags = tags_to_json(nlp_result["final_recommendation_tags"])

    llm_result = generate_new_student_report_with_llm(
        student_id=student_id,
        cluster_id=prediction.cluster_id,
        cluster_label=prediction.cluster_label,
        nlp_result=nlp_result,
        strengths_positive_aspects=payload.strengths_positive_aspects,
        challenges_suggestions=payload.challenges_suggestions,
    )

    try:
        create_generated_student_records(
            db,
            student_id=student_id,
            response_data=_build_response_audit_payload(
                payload=payload,
                nlp_result=nlp_result,
                llm_generation_source=llm_result["generation_source"],
            ),
            assigned_cluster_label=prediction.cluster_label,
            final_recommendation_tags=recommendation_tags,
            llm_recommendation_report=llm_result["report"],
        )
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save new student record: {str(exc)}",
        ) from exc

    return NewStudentRecommendation(
        student_id=student_id,
        student_segment_label=prediction.cluster_label,
        final_recommendation_tags=recommendation_tags,
        llm_recommendation_report=llm_result["report"],
        llm_generation_source=llm_result["generation_source"],
    )
