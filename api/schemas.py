"""Pydantic request and response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class StudentRecommendationResponse(BaseModel):
    student_id: str
    student_segment_label: str | None = None
    final_recommendation_tags: str | None = None
    llm_recommendation_report: str | None = None
    created_at: datetime | None = None


class StudentListItem(BaseModel):
    student_id: str
    student_segment_label: str | None = None
    final_recommendation_tags: str | None = None
    created_at: datetime | None = None


class DashboardSummary(BaseModel):
    total_students: int
    total_segments: int
    segment_distribution: dict[str, int]


class NewStudentInput(BaseModel):
    student_id: str = Field(..., min_length=1)
    responses: dict[str, Any] = Field(default_factory=dict)
    strengths_positive_aspects: str | None = None
    challenges_suggestions: str | None = None


class NewStudentRecommendation(BaseModel):
    student_id: str
    student_segment_label: str
    final_recommendation_tags: str
    llm_recommendation_report: str
    llm_generation_source: str | None = None
