"""Survey feature schema used by the new-student Streamlit form."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

FEATURE_LABELS: dict[str, str] = {
    "use_lecture_slides": "Lecture slides",
    "use_video_lectures": "Recorded video lectures",
    "use_quizzes": "Interactive quizzes and exercises",
    "use_articles": "Online articles and journals",
    "use_forums": "Discussion forums",
    "use_simulations": "Simulations or virtual labs",
    "online_discussion_participation": "Online discussion participation",
    "peer_collaboration": "Online peer collaboration",
    "comfort_asking_questions": "Comfort asking questions online",
    "sense_of_community": "Sense of online community",
    "integration_quality": "Online and face-to-face integration",
    "overall_understanding": "Overall subject understanding",
    "lect_clear_instructions": "Clear online instructions",
    "lect_responsive": "Lecturer responsiveness and support",
    "lect_diverse_tools": "Use of diverse digital tools",
    "lect_timely_feedback": "Timely feedback",
    "lect_foster_interaction": "Lecturer encourages interaction",
    "self_prioritize_deadlines": "Prioritizing deadlines",
    "self_study_schedule": "Personal study schedule",
    "self_prepare_class": "Preparation before class",
    "self_responsibility": "Responsibility for learning outcomes",
    "career_preparation": "Future career preparation",
    "video_helpfulness": "Recorded video lecture helpfulness",
    "digital_literacy_improvement": "Digital literacy improvement",
    "tech_issues_freq": "Technical issues frequency",
    "lms_usability": "LMS user-friendliness",
    "overall_satisfaction": "Overall blended learning satisfaction",
    "benefit_flexibility": "Flexibility in learning pace",
    "benefit_variety": "Variety of learning materials",
    "benefit_recorded_access": "Access to recorded lectures",
    "benefit_self_study_time": "More time for self-study",
    "benefit_life_balance": "Balance between personal and academic life",
    "benefit_self_directed": "Self-directed learning development",
}

FEATURE_QUESTIONS: dict[str, str] = {
    "use_lecture_slides": "How often do you use Lecture Slides (PDF, PowerPoint)?",
    "use_video_lectures": "How often do you use Recorded Video Lectures?",
    "use_quizzes": "How often do you use Interactive Quizzes and Exercises?",
    "use_articles": "How often do you use Online Articles and Journals?",
    "use_forums": "How often do you use Discussion Forums such as Moodle?",
    "use_simulations": "How often do you use Simulations or Virtual Labs?",
    "online_discussion_participation": "How often do you actively participate in online discussions or forums?",
    "peer_collaboration": "How often do you collaborate with peers online for group projects or study sessions?",
    "comfort_asking_questions": "I feel comfortable asking questions or seeking help in an online learning environment.",
    "sense_of_community": "I feel a sense of community with my classmates in the online portions of my courses.",
    "integration_quality": "The online and face-to-face components of my courses are well-integrated.",
    "overall_understanding": "Overall, blended learning helps me understand the subject matter better.",
    "lect_clear_instructions": "The lecturers provide clear instructions for online activities.",
    "lect_responsive": "The lecturers are responsive and supportive.",
    "lect_diverse_tools": "The lecturers use diverse digital tools to make learning engaging.",
    "lect_timely_feedback": "The lecturers provide timely feedback on assignments and questions.",
    "lect_foster_interaction": "The lecturers effectively foster interaction among students.",
    "self_prioritize_deadlines": "I prioritize my assignments and tasks based on deadlines.",
    "self_study_schedule": "I create and follow a personal study schedule.",
    "self_prepare_class": "I actively prepare for class by reviewing materials beforehand.",
    "self_responsibility": "I take responsibility for my own learning outcomes.",
    "career_preparation": "To what extent do you agree that blended learning prepares you well for your future career?",
    "video_helpfulness": "How helpful do you find recorded video lectures for your learning?",
    "digital_literacy_improvement": "To what extent has blended learning improved your digital literacy skills, such as using new software, online collaboration tools, and managing digital files?",
    "tech_issues_freq": "How often do you experience technical issues, such as internet disruption, software problems, or device malfunction, that interfere with your online learning?",
    "lms_usability": "How user-friendly is the Learning Management System provided by your institution, such as Moodle, Canvas, or Google Classroom?",
    "overall_satisfaction": "How satisfied are you with the blended learning approach at your institution?",
    "benefit_flexibility": "How beneficial do you find flexibility in learning pace?",
    "benefit_variety": "How beneficial do you find variety of learning materials?",
    "benefit_recorded_access": "How beneficial do you find access to recorded lectures?",
    "benefit_self_study_time": "How beneficial do you find having more time for self-study?",
    "benefit_life_balance": "How beneficial do you find better balance between personal and academic life?",
    "benefit_self_directed": "How beneficial do you find development of self-directed learning skills?",
}

FALLBACK_SCALES: dict[str, dict[str, int]] = {
    "AGREE5": {"Strongly Disagree": 1, "Disagree": 2, "Neutral": 3, "Agree": 4, "Strongly Agree": 5},
    "FREQ5": {"Never": 1, "Rarely": 2, "Sometimes": 3, "Often": 4, "Always": 5},
    "HELPFUL5": {"Not very helpful": 1, "Slightly helpful": 2, "Neutral": 3, "Helpful": 4, "Very helpful": 5},
    "TECH_FREQ5": {"Never": 1, "Rarely": 2, "Occasionally": 3, "Often": 4, "Very Often": 5},
    "LMS5": {"Very Poor": 1, "Poor": 2, "Neutral": 3, "Good": 4, "Excellent": 5},
    "SATISFY5": {"Very dissatisfied": 1, "Dissatisfied": 2, "Neutral": 3, "Satisfied": 4, "Very satisfied": 5},
    "BENEFIT5": {"Not beneficial": 1, "Slightly beneficial": 2, "Neutral": 3, "Beneficial": 4, "Extremely beneficial": 5},
    "EXTENT5": {"Not at all": 1, "A little": 2, "A moderate amount": 3, "A lot": 4, "A great deal": 5},
}

FALLBACK_ORDINAL_COLUMN_SCALES: dict[str, str] = {
    "use_lecture_slides": "FREQ5",
    "use_video_lectures": "FREQ5",
    "use_quizzes": "FREQ5",
    "use_articles": "FREQ5",
    "use_forums": "FREQ5",
    "use_simulations": "FREQ5",
    "online_discussion_participation": "FREQ5",
    "peer_collaboration": "FREQ5",
    "comfort_asking_questions": "AGREE5",
    "sense_of_community": "AGREE5",
    "integration_quality": "AGREE5",
    "overall_understanding": "AGREE5",
    "lect_clear_instructions": "AGREE5",
    "lect_responsive": "AGREE5",
    "lect_diverse_tools": "AGREE5",
    "lect_timely_feedback": "AGREE5",
    "lect_foster_interaction": "AGREE5",
    "self_prioritize_deadlines": "AGREE5",
    "self_study_schedule": "AGREE5",
    "self_prepare_class": "AGREE5",
    "self_responsibility": "AGREE5",
    "career_preparation": "AGREE5",
    "video_helpfulness": "HELPFUL5",
    "digital_literacy_improvement": "EXTENT5",
    "tech_issues_freq": "TECH_FREQ5",
    "lms_usability": "LMS5",
    "overall_satisfaction": "SATISFY5",
    "benefit_flexibility": "BENEFIT5",
    "benefit_variety": "BENEFIT5",
    "benefit_recorded_access": "BENEFIT5",
    "benefit_self_study_time": "BENEFIT5",
    "benefit_life_balance": "BENEFIT5",
    "benefit_self_directed": "BENEFIT5",
}

@dataclass(frozen=True)
class SurveySchema:
    feature_labels: dict[str, str]
    feature_questions: dict[str, str]
    scales: dict[str, dict[str, int]]
    ordinal_column_scales: dict[str, str]

    @property
    def feature_keys(self) -> list[str]:
        return list(self.feature_labels.keys())


def _only_mapping_scales(scales: dict[str, Any]) -> dict[str, dict[str, int]]:
    usable: dict[str, dict[str, int]] = {}
    for scale_name, mapping in scales.items():
        if isinstance(mapping, dict):
            usable[scale_name] = {str(label): int(value) for label, value in mapping.items()}
    return usable


def load_survey_schema(shared_config: dict[str, Any] | None = None) -> SurveySchema:
    cfg = shared_config or {}
    scales = _only_mapping_scales(cfg.get("scales", {})) or FALLBACK_SCALES
    ordinal_column_scales = cfg.get("ordinal_column_scales", {}) or FALLBACK_ORDINAL_COLUMN_SCALES

    return SurveySchema(
        feature_labels=FEATURE_LABELS,
        feature_questions=FEATURE_QUESTIONS,
        scales=scales,
        ordinal_column_scales={str(k): str(v) for k, v in ordinal_column_scales.items()},
    )
