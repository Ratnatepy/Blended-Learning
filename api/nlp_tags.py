"""
Runtime NLP tag extraction for new student open-ended responses.

This module converts the logic from notebook/05-pre-nlp.ipynb and
notebook/06-nlp.ipynb into backend functions that can be called by FastAPI.
It uses:
- language detection from pre-NLP
- optional Khmer/mixed Khmer-to-English translation
- text cleaning and keyword/theme matching from NLP
- segment fallback tags when text is empty or not meaningful
"""

from __future__ import annotations

import json
import re
from typing import Any

import pandas as pd

from blended_learning.config.settings import settings

KHMER_REGEX = re.compile(r"[\u1780-\u17FF]")
EN_REGEX = re.compile(r"[A-Za-z]")

TEXT_NORMALIZATION_REPLACEMENTS = {
    "face to face": "in_person",
    "face-to-face": "in_person",
    "face face": "in_person",
    "self study": "self_study",
    "self studying": "self_study",
    "self learning": "self_learning",
    "time management": "time_management",
    "internet connection": "internet_connection",
    "internet access": "internet_access",
    "technical issues": "technical_issues",
    "online learning": "online_learning",
    "blended learning": "blended_learning",
    "saving time": "save_time",
}

NON_MEANINGFUL_RESPONSES = {
    "",
    "no",
    "none",
    "nothing",
    "no comment",
    "not sure",
    "no idea",
    "don t know",
    "dont know",
    "don t have",
    "dont have",
    "not yet",
    "n a",
    "na",
    "nil",
    "ok",
    "okay",
    "agree",
    "all good",
    "everything is good",
    "it already great",
    "nope",
    "math",
    "french",
    "coding",
    "sad",
    "uyu",
    "uu",
    "nuh uhh",
    "dunno yet",
}


RECOMMENDATION_RULE_BANK = {
    "tech_issue": {
        "title": "Improve technical access and reliability",
        "recommendation": "Provide stable internet access, offline materials, clear platform instructions, and technical support.",
    },
    "motivation": {
        "title": "Support motivation and self-discipline",
        "recommendation": "Use weekly check-ins, reminders, progress tracking, and structured study schedules.",
    },
    "interaction": {
        "title": "Increase interaction and communication",
        "recommendation": "Add Q&A sessions, group discussion, peer collaboration, and faster lecturer feedback.",
    },
    "learning_support": {
        "title": "Improve clarity and learning support",
        "recommendation": "Provide clearer instructions, examples, recorded explanations, and step-by-step learning guides.",
    },
    "learning_environment": {
        "title": "Improve learning resources and environment",
        "recommendation": "Organize materials clearly, update resources, improve study spaces, and support classroom comfort.",
    },
    "workload_support": {
        "title": "Manage workload and assessment pressure",
        "recommendation": "Balance assignments, clarify deadlines, and align online tasks with in-person sessions.",
    },
    "self_paced": {
        "title": "Support self-paced learning",
        "recommendation": "Provide recorded lessons, weekly learning paths, and materials students can review at their own pace.",
    },
    "content_access": {
        "title": "Strengthen access to learning materials",
        "recommendation": "Upload slides, videos, references, exercises, and course materials early.",
    },
    "digital_skill": {
        "title": "Develop digital learning skills",
        "recommendation": "Provide guidance on LMS tools, online resources, digital research, and educational technologies.",
    },
    "engagement": {
        "title": "Increase learner engagement",
        "recommendation": "Use quizzes, games, practical tasks, discussions, and interactive activities.",
    },
    "learning_effectiveness": {
        "title": "Improve learning effectiveness",
        "recommendation": "Combine online review materials with in-person explanation, practice, and feedback.",
    },
}


def detect_language(text: str | None) -> str:
    if text is None or pd.isna(text):
        return "empty"

    text = str(text).strip()
    if not text:
        return "empty"

    has_kh = bool(KHMER_REGEX.search(text))
    has_en = bool(EN_REGEX.search(text))

    if has_kh and has_en:
        return "mixed"
    if has_kh:
        return "kh"
    if has_en:
        return "en"
    return "other"


def translate_to_english_if_needed(text: str | None) -> str:
    """
    Translate Khmer/mixed responses to English when possible.
    If translation fails, return the original text so the API still works.
    """
    if text is None or pd.isna(text):
        return ""

    text = str(text).strip()
    if not text:
        return ""

    language = detect_language(text)
    if language not in {"kh", "mixed"}:
        return text

    try:
        from deep_translator import GoogleTranslator

        return GoogleTranslator(source="km", target="en").translate(text)
    except Exception:
        return text


def clean_basic_text(text: str | None) -> str:
    if text is None or pd.isna(text):
        return ""

    text = str(text).lower().strip()
    text = re.sub(r"\s+", " ", text)

    for source, replacement in TEXT_NORMALIZATION_REPLACEMENTS.items():
        text = text.replace(source, replacement)

    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_text_for_matching(text: str | None) -> str:
    if text is None or pd.isna(text):
        return ""

    text = str(text).lower().replace("_", " ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_non_meaningful_response(text: str | None) -> bool:
    return normalize_text_for_matching(text) in NON_MEANINGFUL_RESPONSES


def detect_themes(text: str | None, theme_map: dict[str, list[str]]) -> list[str]:
    if is_non_meaningful_response(text):
        return []

    text_norm = normalize_text_for_matching(text)
    matched_themes: set[str] = set()

    for theme, keywords in theme_map.items():
        for keyword in keywords:
            keyword_norm = normalize_text_for_matching(keyword)
            if keyword_norm and keyword_norm in text_norm:
                matched_themes.add(theme)
                break

    return sorted(matched_themes)


def themes_to_tags(themes: list[str]) -> list[str]:
    tags = []
    theme_to_tag = settings.theme_to_recommendation_map

    for theme in themes:
        tag = theme_to_tag.get(theme)
        if tag:
            tags.append(tag)

    return sorted(set(tags))


def get_segment_default_tags(segment_label: str | None) -> list[str]:
    if segment_label is None or pd.isna(segment_label):
        return []

    label = str(segment_label).lower()

    if "cluster 1" in label or "passive" in label or "moderately engaged" in label:
        return ["motivation", "interaction", "learning_support", "self_paced"]

    if "cluster 2" in label or "active" in label or "highly engaged" in label:
        return ["content_access", "engagement", "digital_skill", "self_paced"]

    return ["balanced_support", "learning_guidance"]


def build_rule_based_recommendations(tags: list[str]) -> list[dict[str, str]]:
    return [
        {"tag": tag, **RECOMMENDATION_RULE_BANK[tag]}
        for tag in tags
        if tag in RECOMMENDATION_RULE_BANK
    ]


def extract_open_response_tags(
    strengths_positive_aspects: str | None,
    challenges_suggestions: str | None,
    segment_label: str | None = None,
) -> dict[str, Any]:
    """
    Main function to call from FastAPI.
    Returns JSON-serializable themes, tags, fallback tags, and recommendations.
    """
    strengths_en = translate_to_english_if_needed(strengths_positive_aspects)
    challenges_en = translate_to_english_if_needed(challenges_suggestions)

    strengths_clean = clean_basic_text(strengths_en)
    challenges_clean = clean_basic_text(challenges_en)

    strength_themes = detect_themes(strengths_clean, settings.strength_theme_map)
    challenge_themes = detect_themes(challenges_clean, settings.challenge_theme_map)

    strength_tags = themes_to_tags(strength_themes)
    challenge_tags = themes_to_tags(challenge_themes)
    nlp_tags = sorted(set(strength_tags + challenge_tags))

    fallback_tags = get_segment_default_tags(segment_label)
    final_tags = nlp_tags if nlp_tags else fallback_tags

    return {
        "strengths_language": detect_language(strengths_positive_aspects),
        "challenges_language": detect_language(challenges_suggestions),
        "strengths_final_en": strengths_en,
        "challenges_final_en": challenges_en,
        "strengths_clean": strengths_clean,
        "challenges_clean": challenges_clean,
        "strength_themes": strength_themes,
        "challenge_themes": challenge_themes,
        "strength_tags": strength_tags,
        "challenge_tags": challenge_tags,
        "recommendation_tags": nlp_tags,
        "segment_default_tags": fallback_tags,
        "final_recommendation_tags": sorted(set(final_tags)),
        "rule_based_recommendations": build_rule_based_recommendations(final_tags),
        "used_fallback": len(nlp_tags) == 0,
    }


def tags_to_json(tags: list[str]) -> str:
    return json.dumps(tags, ensure_ascii=False)
