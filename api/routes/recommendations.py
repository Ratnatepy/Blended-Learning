from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import StudentRecommendation, StudentResponseInput
from api.schemas import NewStudentInput, NewStudentRecommendation
from api.ml_model import assign_kmodes_cluster
from api.nlp_tags import extract_open_response_tags, tags_to_json
from api.llm_service import generate_new_student_report_with_llm

router = APIRouter()


@router.post("/generate", response_model=NewStudentRecommendation)
def generate_recommendation(
    payload: NewStudentInput,
    db: Session = Depends(get_db)
):
    # ---------------------------------------------------
    # Protect existing student records
    # ---------------------------------------------------
    existing_recommendation = (
        db.query(StudentRecommendation)
        .filter(StudentRecommendation.student_id == payload.student_id)
        .first()
    )

    existing_response_input = (
        db.query(StudentResponseInput)
        .filter(StudentResponseInput.student_id == payload.student_id)
        .first()
    )

    if existing_recommendation or existing_response_input:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Student ID '{payload.student_id}' already exists. "
                "This record is protected and will not be overwritten. "
                "Please use a new student ID for new input testing."
            )
        )

    # ---------------------------------------------------
    # Assign cluster using saved K-Modes model
    # ---------------------------------------------------
    try:
        cluster_id, cluster_label = assign_kmodes_cluster(payload.responses)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # ---------------------------------------------------
    # Extract NLP tags from the two open-ended text fields
    # ---------------------------------------------------
    nlp_result = extract_open_response_tags(
        strengths_positive_aspects=payload.strengths_positive_aspects,
        challenges_suggestions=payload.challenges_suggestions,
        segment_label=cluster_label
    )

    recommendation_tags = tags_to_json(nlp_result["final_recommendation_tags"])

    # ---------------------------------------------------
    # Generate the final report with OpenRouter LLM when configured.
    # If OPENROUTER_API_KEY is missing or OpenRouter fails, this returns
    # a rule-based fallback report instead of breaking the endpoint.
    # ---------------------------------------------------
    llm_result = generate_new_student_report_with_llm(
        student_id=payload.student_id,
        cluster_id=cluster_id,
        cluster_label=cluster_label,
        nlp_result=nlp_result,
        strengths_positive_aspects=payload.strengths_positive_aspects,
        challenges_suggestions=payload.challenges_suggestions,
    )

    report = llm_result["report"]
    llm_generation_source = llm_result["generation_source"]

    # ---------------------------------------------------
    # Save raw 33-feature input for future model tuning
    # ---------------------------------------------------
    new_response_input = StudentResponseInput(
        student_id=payload.student_id,
        response_data={
            "survey_responses": payload.responses,
            "open_ended_responses": {
                "strengths_positive_aspects": payload.strengths_positive_aspects,
                "challenges_suggestions": payload.challenges_suggestions
            },
            "nlp_extraction": nlp_result,
            "llm_generation_source": llm_generation_source
        },
        assigned_cluster_label=cluster_label
    )

    # ---------------------------------------------------
    # Save recommendation output for UI display/history
    # ---------------------------------------------------
    new_recommendation = StudentRecommendation(
        student_id=payload.student_id,
        student_segment_label=cluster_label,
        final_recommendation_tags=recommendation_tags,
        llm_recommendation_report=report
    )

    try:
        db.add(new_response_input)
        db.add(new_recommendation)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save new student record: {str(e)}"
        )

    return {
        "student_id": payload.student_id,
        "student_segment_label": cluster_label,
        "final_recommendation_tags": recommendation_tags,
        "llm_recommendation_report": report,
        "llm_generation_source": llm_generation_source
    }
