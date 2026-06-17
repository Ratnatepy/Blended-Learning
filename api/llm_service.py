"""Runtime LLM generation service for new FastAPI inputs.

This module connects the existing OpenRouterStudentRecommender class to the
/recommendations/generate endpoint. The rule-based tags and recommendations
remain the source of truth; OpenRouter rewrites them into a student-facing
report. If OpenRouter is not configured or fails, the API returns a safe
rule-based fallback report instead of crashing.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from api.core.config import get_api_config


def build_student_recommendation_package(
    student_id: str,
    cluster_id: int,
    cluster_label: str,
    nlp_result: dict[str, Any],
    strengths_positive_aspects: str | None = None,
    challenges_suggestions: str | None = None,
) -> dict[str, Any]:
    """Build the evidence package expected by OpenRouterStudentRecommender."""

    return {
        "student_id": student_id,
        # "student_segment": cluster_id,
        "student_segment_label": cluster_label,
        "cluster_label": cluster_label,
        "open_strengths_clean": (
            nlp_result.get("strengths_final_en")
            or nlp_result.get("strengths_clean")
            or strengths_positive_aspects
            or ""
        ),
        "open_challenges_clean": (
            nlp_result.get("challenges_final_en")
            or nlp_result.get("challenges_clean")
            or challenges_suggestions
            or ""
        ),
        "strength_sentiment_label": None,
        "challenge_sentiment_label": None,
        "strength_compound": None,
        "challenge_compound": None,
        "strength_themes": nlp_result.get("strength_themes", []),
        "challenge_themes": nlp_result.get("challenge_themes", []),
        "strength_tags": nlp_result.get("strength_tags", []),
        "challenge_tags": nlp_result.get("challenge_tags", []),
        "recommendation_tags": nlp_result.get("recommendation_tags", []),
        "segment_default_tags": nlp_result.get("segment_default_tags", []),
        "final_recommendation_tags": nlp_result.get("final_recommendation_tags", []),
        "rule_based_recommendations": nlp_result.get("rule_based_recommendations", []),
        "used_segment_fallback_tags": nlp_result.get("used_fallback", False),
    }


def build_template_fallback_report(student_package: dict[str, Any]) -> str:
    """Last-resort fallback if the OpenRouter class cannot be imported."""

    fallback_cfg = get_api_config().get("llm", {}).get("fallback_report", {})
    if not fallback_cfg:
        # Reuse the ML LLM config when the API-specific override is absent.
        from blended_learning.config.settings import settings

        fallback_cfg = getattr(settings, "llm", {}).get("fallback_report", {})

    segment = student_package.get(
        "student_segment_label",
        fallback_cfg.get("default_segment", "Unknown segment"),
    )
    strengths = student_package.get("strength_themes", [])
    challenges = student_package.get("challenge_themes", [])
    recommendations = student_package.get("rule_based_recommendations", [])

    lines: list[str] = []
    lines.append(fallback_cfg.get("title", "# Personalized Blended Learning Recommendation Report"))
    lines.append("")
    lines.append(fallback_cfg.get("profile_heading", "## 1. Student Learning Profile"))
    profile_template = fallback_cfg.get(
        "profile_template",
        "The student belongs to the **{segment}** profile.",
    )
    lines.append(profile_template.format(segment=segment))
    lines.append("")

    lines.append(fallback_cfg.get("strength_heading", "## 2. Main Strengths"))
    if strengths:
        lines.extend(f"- {theme}" for theme in strengths)
    else:
        lines.append(f"- {fallback_cfg.get('no_strength_text', 'No clear strength theme was detected.')}" )
    lines.append("")

    lines.append(fallback_cfg.get("challenge_heading", "## 3. Main Challenges"))
    if challenges:
        lines.extend(f"- {theme}" for theme in challenges)
    else:
        lines.append(f"- {fallback_cfg.get('no_challenge_text', 'No clear challenge theme was detected.')}" )
    lines.append("")

    lines.append(fallback_cfg.get("recommendation_heading", "## 4. Personalized Recommendations"))
    if recommendations:
        for recommendation in recommendations:
            title = recommendation.get("title", "Recommendation")
            text = recommendation.get("recommendation", "")
            lines.append(f"- **{title}:** {text}")
    else:
        lines.append(f"- {fallback_cfg.get('no_recommendation_text', 'Provide balanced blended-learning support.')}" )
    lines.append("")

    lines.append(fallback_cfg.get("action_plan_heading", "## 5. Short Action Plan"))
    for action in fallback_cfg.get("action_plan_items", []):
        lines.append(f"- {action}")

    return "\n".join(lines)


@lru_cache(maxsize=1)
def get_openrouter_recommender():
    """Create the OpenRouter recommender once and reuse it across requests."""

    from blended_learning.llm.openrouter import OpenRouterStudentRecommender

    return OpenRouterStudentRecommender()


def generate_new_student_report_with_llm(
    student_id: str,
    cluster_id: int,
    cluster_label: str,
    nlp_result: dict[str, Any],
    strengths_positive_aspects: str | None = None,
    challenges_suggestions: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    """Generate a report for a new input using OpenRouter when available."""

    student_package = build_student_recommendation_package(
        student_id=student_id,
        cluster_id=cluster_id,
        cluster_label=cluster_label,
        nlp_result=nlp_result,
        strengths_positive_aspects=strengths_positive_aspects,
        challenges_suggestions=challenges_suggestions,
    )

    try:
        recommender = get_openrouter_recommender()
        runtime_cfg = get_api_config().get("llm_runtime", {})
        report = recommender.generate_report_from_package(
            student_package,
            temperature=temperature if temperature is not None else runtime_cfg.get("temperature", 0.3),
            max_tokens=max_tokens if max_tokens is not None else runtime_cfg.get("max_tokens", 900),
        )
        generation_source = getattr(
            recommender,
            "last_generation_source",
            "openrouter_llm_or_rule_based_fallback",
        )
        generation_error = getattr(
            recommender,
            "last_generation_error",
            getattr(recommender, "last_error", None),
        )

    except Exception as exc:
        report = build_template_fallback_report(student_package)
        generation_source = "template_fallback_error"
        generation_error = str(exc)

    return {
        "report": report,
        "generation_source": generation_source,
        "generation_error": generation_error,
        "student_package": student_package,
    }
