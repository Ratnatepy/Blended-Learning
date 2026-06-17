"""Helpers for parsing recommendation-related API response fields."""

from __future__ import annotations

import json
from typing import Any


def parse_tags_to_list(tags: Any) -> list[str]:
    if not tags:
        return []

    try:
        parsed = json.loads(tags) if isinstance(tags, str) else tags
        if isinstance(parsed, list):
            return [str(tag).strip() for tag in parsed if str(tag).strip()]
        return [str(parsed).strip()] if str(parsed).strip() else []
    except Exception:
        return [
            tag.strip()
            for tag in str(tags)
            .replace("[", "")
            .replace("]", "")
            .replace('"', "")
            .replace("'", "")
            .split(",")
            if tag.strip()
        ]


def get_nested_recommendation_tags(data: dict[str, Any]) -> Any:
    """Read tags from either flat or nested API response shapes."""
    if not isinstance(data, dict):
        return []

    direct_tags = data.get("final_recommendation_tags")
    if direct_tags:
        return direct_tags

    nlp_extraction = data.get("nlp_extraction", {})
    if isinstance(nlp_extraction, dict):
        nested_tags = nlp_extraction.get("final_recommendation_tags")
        if nested_tags:
            return nested_tags

        recommendation_tags = nlp_extraction.get("recommendation_tags")
        if recommendation_tags:
            return recommendation_tags

    return []


def get_recommendation_report(data: dict[str, Any]) -> str:
    if not isinstance(data, dict):
        return ""

    for key in (
        "llm_recommendation_report",
        "recommendation_report",
        "report",
        "generated_report",
    ):
        value = data.get(key)
        if value:
            return str(value)

    return ""


def clean_recommendation_text(text: Any) -> str:
    if not text:
        return ""

    cleaned = str(text)
    cleaned = cleaned.replace("&lt;br&gt;", "<br>")
    cleaned = cleaned.replace("&lt;br/&gt;", "<br>")
    cleaned = cleaned.replace("&lt;br /&gt;", "<br>")
    cleaned = cleaned.replace("<br />", "<br>")
    cleaned = cleaned.replace("<br/>", "<br>")
    return cleaned.strip()
