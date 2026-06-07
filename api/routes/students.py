from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import StudentRecommendation
from api.schemas import StudentRecommendationResponse

router = APIRouter()


# ---------------------------------------------------------
# Segment label helpers
# ---------------------------------------------------------

def normalize_segment_label(label: str) -> str:
    """
    Normalize old and new cluster labels into final learner segment names.

    This avoids showing Cluster 1 / Cluster 2 in the frontend because
    K-Modes cluster IDs can change between dataset versions.
    """

    if label is None:
        return "Unknown"

    raw = str(label).strip()
    s = raw.lower()

    # Meaning-based mapping first
    if "passive" in s or "moderately" in s or "moderate" in s:
        return "Moderately Engaged (Passive) Learners"

    if "active" in s or "highly" in s or "high" in s:
        return "Highly Engaged (Active) Learners"

    # Fallback for current v1.1 / 588-row model if only raw cluster ID exists
    if s in ["cluster 1", "1", "1.0"]:
        return "Highly Engaged (Active) Learners"

    if s in ["cluster 2", "2", "2.0"]:
        return "Moderately Engaged (Passive) Learners"

    return raw


def clean_report_text(report: str) -> str:
    """
    Remove old Cluster 1 / Cluster 2 prefixes inside saved recommendation reports.
    """

    if not report:
        return report

    cleaned = str(report)

    replacements = {
        "Cluster 1: Highly Engaged (Active) Learners": "Highly Engaged (Active) Learners",
        "Cluster 2: Highly Engaged (Active) Learners": "Highly Engaged (Active) Learners",
        "Cluster 1 – Highly Engaged (Active) Learners": "Highly Engaged (Active) Learners",
        "Cluster 2 – Highly Engaged (Active) Learners": "Highly Engaged (Active) Learners",
        "Cluster 1 - Highly Engaged (Active) Learners": "Highly Engaged (Active) Learners",
        "Cluster 2 - Highly Engaged (Active) Learners": "Highly Engaged (Active) Learners",

        "Cluster 1: Moderately Engaged (Passive) Learners": "Moderately Engaged (Passive) Learners",
        "Cluster 2: Moderately Engaged (Passive) Learners": "Moderately Engaged (Passive) Learners",
        "Cluster 1 – Moderately Engaged (Passive) Learners": "Moderately Engaged (Passive) Learners",
        "Cluster 2 – Moderately Engaged (Passive) Learners": "Moderately Engaged (Passive) Learners",
        "Cluster 1 - Moderately Engaged (Passive) Learners": "Moderately Engaged (Passive) Learners",
        "Cluster 2 - Moderately Engaged (Passive) Learners": "Moderately Engaged (Passive) Learners",
    }

    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)

    return cleaned


def student_to_response(student: StudentRecommendation):
    """
    Convert database object to clean API response.
    """

    return {
        "student_id": student.student_id,
        "student_segment_label": normalize_segment_label(
            student.student_segment_label
        ),
        "final_recommendation_tags": student.final_recommendation_tags,
        "llm_recommendation_report": clean_report_text(
            student.llm_recommendation_report
        ),
        "created_at": student.created_at,
    }


@router.get("/")
def get_all_students(
    limit: int = Query(1000, ge=1, le=5000),
    db: Session = Depends(get_db)
):
    """
    Return student recommendation records for the Student Records page.

    Segment labels are normalized before sending to the frontend.
    """

    students = (
        db.query(StudentRecommendation)
        .order_by(
            StudentRecommendation.created_at.desc(),
            StudentRecommendation.student_id.asc()
        )
        .limit(limit)
        .all()
    )

    return [
        {
            "student_id": student.student_id,
            "student_segment_label": normalize_segment_label(
                student.student_segment_label
            ),
            "final_recommendation_tags": student.final_recommendation_tags,
            "created_at": student.created_at,
        }
        for student in students
    ]


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    Return dashboard summary with normalized segment labels.

    This prevents old labels such as:
    - Cluster 1: ...
    - Cluster 2: ...

    from being counted as separate learner profiles.
    """

    students = db.query(StudentRecommendation).all()

    total_students = len(students)
    segment_distribution = {}

    for student in students:
        segment = normalize_segment_label(student.student_segment_label)
        segment_distribution[segment] = segment_distribution.get(segment, 0) + 1

    return {
        "total_students": total_students,
        "total_segments": len(segment_distribution),
        "segment_distribution": segment_distribution,
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
                "student_segment_label": normalize_segment_label(
                    student.student_segment_label
                ),
                "final_recommendation_tags": student.final_recommendation_tags,
                "created_at": student.created_at,
            }
            for student in students
        ],
    }


@router.get("/{student_id}")
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

    return student_to_response(student)