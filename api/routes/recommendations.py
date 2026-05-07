from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import StudentRecommendation, StudentResponseInput
from api.schemas import NewStudentInput, NewStudentRecommendation
from api.ml_model import assign_kmodes_cluster

router = APIRouter()


def get_recommendation_tags(cluster_id: int):
    if cluster_id == 1:
        return '["interaction", "learning_support", "motivation", "self_paced"]'

    if cluster_id == 2:
        return '["content_access", "digital_skill", "engagement", "self_paced"]'

    return '["balanced_support", "learning_guidance"]'


def generate_report(
    student_id: str,
    cluster_label: str,
    recommendation_tags: str,
    strengths: str | None = None,
    challenges: str | None = None
):
    report = f"""
**Student Learning Profile**

- **Student ID:** {student_id}
- **Assigned Segment:** {cluster_label}

The student was assigned to this learner segment using the saved K-Modes clustering model based on the submitted 33 blended-learning survey responses.

---

### Recommendation Tags

{recommendation_tags}

---

### Personalized Recommendation

"""

    if "Cluster 1" in cluster_label:
        report += """
This student appears to match the profile of a moderately engaged or more passive blended-learning student. The recommendation should focus on increasing interaction, strengthening motivation, providing clearer learning support, and encouraging regular self-paced study habits.

Suggested actions:

1. Join short Q&A or discussion sessions.
2. Use clear weekly study checklists.
3. Review recorded lessons before or after class.
4. Participate in peer collaboration activities.
5. Request feedback when instructions or tasks are unclear.
"""

    elif "Cluster 2" in cluster_label:
        report += """
This student appears to match the profile of a highly engaged active learner. The recommendation should focus on maintaining engagement, providing early access to content, supporting self-paced learning, and offering advanced or interactive learning activities.

Suggested actions:

1. Access lecture slides, videos, and learning materials early.
2. Participate in quizzes, forums, and practical activities.
3. Use recorded lessons for flexible review.
4. Explore advanced or enrichment learning resources.
5. Continue using digital tools to support independent learning.
"""

    else:
        report += """
This student should receive balanced blended-learning support, including structured teacher guidance, online resources, and regular progress monitoring.
"""

    if strengths:
        report += f"""

---

### Student Strengths / Positive Feedback

{strengths}
"""

    if challenges:
        report += f"""

---

### Student Challenges / Suggestions

{challenges}
"""

    return report


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
    # Generate recommendation
    # ---------------------------------------------------
    recommendation_tags = get_recommendation_tags(cluster_id)

    report = generate_report(
        student_id=payload.student_id,
        cluster_label=cluster_label,
        recommendation_tags=recommendation_tags,
        strengths=payload.strengths_positive_aspects,
        challenges=payload.challenges_suggestions
    )

    # ---------------------------------------------------
    # Save raw 33-feature input for future model tuning
    # ---------------------------------------------------
    new_response_input = StudentResponseInput(
        student_id=payload.student_id,
        response_data=payload.responses,
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
        "llm_recommendation_report": report
    }