from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class StudentRecommendationResponse(BaseModel):
    student_id: str
    student_segment_label: Optional[str] = None
    final_recommendation_tags: Optional[str] = None
    llm_recommendation_report: Optional[str] = None


class DashboardSummary(BaseModel):
    total_students: int
    total_segments: int
    segment_distribution: Dict[str, int]


class NewStudentInput(BaseModel):
    student_id: str
    responses: Dict[str, Any]
    strengths_positive_aspects: Optional[str] = None
    challenges_suggestions: Optional[str] = None


class NewStudentRecommendation(BaseModel):
    student_id: str
    student_segment_label: str
    final_recommendation_tags: str
    llm_recommendation_report: str