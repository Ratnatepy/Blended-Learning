from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from api.database import Base


class StudentRecommendation(Base):
    __tablename__ = "student_recommendations"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(String, unique=True, index=True, nullable=False)

    student_segment_label = Column(String, nullable=True)

    final_recommendation_tags = Column(Text, nullable=True)

    llm_recommendation_report = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StudentResponseInput(Base):
    __tablename__ = "student_response_inputs"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(String, unique=True, index=True, nullable=False)

    response_data = Column(JSONB, nullable=False)

    assigned_cluster_label = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())