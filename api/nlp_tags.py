"""
Runtime NLP tag extraction for new student open-ended responses.

This module converts the logic from notebook/05-translation_preprocessing.ipynb and
notebook/06-nlp.ipynb into backend functions that can be called by FastAPI.

It uses:
- language detection from pre-NLP
- optional Khmer/mixed Khmer-to-English translation
- text cleaning and keyword/theme matching from NLP
- segment fallback tags when text is empty or not meaningful
- unknown phrase detection for researcher review
"""

from __future__ import annotations

import json
import re
from typing import Any

import pandas as pd

from blended_learning.config.settings import settings


# ---------------------------------------------------
# Regex patterns
# ---------------------------------------------------

KHMER_REGEX = re.compile(r"[\u1780-\u17FF]")
EN_REGEX = re.compile(r"[A-Za-z]")


# ---------------------------------------------------
# Text normalization rules
# ---------------------------------------------------

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


# ---------------------------------------------------
# Non-meaningful student responses
# ---------------------------------------------------

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


# ---------------------------------------------------
# Recommendation rule bank
# ---------------------------------------------------

RECOMMENDATION_RULE_BANK = {
    "tech_issue": {
        "title": "Improve technical access and reliability",
        "recommendation": (
            "Provide stable internet access, offline materials, "
            "clear platform instructions, and technical support."
        ),
    },
    "motivation": {
        "title": "Support motivation and self-discipline",
        "recommendation": (
            "Use weekly check-ins, reminders, progress tracking, "
            "and structured study schedules."
        ),
    },
    "interaction": {
        "title": "Increase interaction and communication",
        "recommendation": (
            "Add Q&A sessions, group discussion, peer collaboration, "
            "and faster lecturer feedback."
        ),
    },
    "learning_support": {
        "title": "Improve clarity and learning support",
        "recommendation": (
            "Provide clearer instructions, examples, recorded explanations, "
            "and step-by-step learning guides."
        ),
    },
    "learning_environment": {
        "title": "Improve learning resources and environment",
        "recommendation": (
            "Organize materials clearly, update resources, improve study spaces, "
            "and support classroom comfort."
        ),
    },
    "workload_support": {
        "title": "Manage workload and assessment pressure",
        "recommendation": (
            "Balance assignments, clarify deadlines, and align online tasks "
            "with in-person sessions."
        ),
    },
    "self_paced": {
        "title": "Support self-paced learning",
        "recommendation": (
            "Provide recorded lessons, weekly learning paths, and materials "
            "students can review at their own pace."
        ),
    },
    "content_access": {
        "title": "Strengthen access to learning materials",
        "recommendation": (
            "Upload slides, videos, references, exercises, and course materials early."
        ),
    },
    "digital_skill": {
        "title": "Develop digital learning skills",
        "recommendation": (
            "Provide guidance on LMS tools, online resources, digital research, "
            "and educational technologies."
        ),
    },
    "engagement": {
        "title": "Increase learner engagement",
        "recommendation": (
            "Use quizzes, games, practical tasks, discussions, and interactive activities."
        ),
    },
    "learning_effectiveness": {
        "title": "Improve learning effectiveness",
        "recommendation": (
            "Combine online review materials with in-person explanation, "
            "practice, and feedback."
        ),
    },
}


# ---------------------------------------------------
# Language detection
# ---------------------------------------------------

def detect_language(text: str | None) -> str:
    if text is None or pd.isna(text):
        return "empty"

    text = str(text).strip()

    if not text:
        return "empty"

    has_khmer = bool(KHMER_REGEX.search(text))
    has_english = bool(EN_REGEX.search(text))

    if has_khmer and has_english:
        return "mixed"

    if has_khmer:
        return "kh"

    if has_english:
        return "en"

    return "other"


# ---------------------------------------------------
# Khmer / mixed Khmer translation
# ---------------------------------------------------

def translate_to_english_if_needed(text: str | None) -> str:
    """
    Translate Khmer or mixed Khmer-English responses to English when possible.
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

        translated_text = GoogleTranslator(source="km", target="en").translate(text)
        return translated_text

    except Exception:
        return text


# ---------------------------------------------------
# Text cleaning
# ---------------------------------------------------

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
    text_norm = normalize_text_for_matching(text)
    return text_norm in NON_MEANINGFUL_RESPONSES


# ---------------------------------------------------
# Theme and tag detection
# ---------------------------------------------------

def detect_themes(text: str | None, theme_map: dict[str, list[str]]) -> list[str]:
    """
    Detect known themes using keyword matching.
    """

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
    """
    Convert detected themes into recommendation tags.
    """

    tags = []
    theme_to_tag = settings.theme_to_recommendation_map

    for theme in themes:
        tag = theme_to_tag.get(theme)

        if tag:
            tags.append(tag)

    return sorted(set(tags))


# ---------------------------------------------------
# Unknown phrase detection
# ---------------------------------------------------

def get_all_known_keywords() -> set[str]:
    """
    Collect all known keywords from both strength and challenge theme maps.
    Used to check whether a response contains recognized NLP vocabulary.
    """

    known_keywords: set[str] = set()

    for theme_map in [settings.strength_theme_map, settings.challenge_theme_map]:
        for keywords in theme_map.values():
            for keyword in keywords:
                keyword_norm = normalize_text_for_matching(keyword)

                if keyword_norm:
                    known_keywords.add(keyword_norm)

    return known_keywords


def contains_known_keyword(text: str | None) -> bool:
    """
    Return True if text contains at least one known keyword from the theme maps.
    """

    text_norm = normalize_text_for_matching(text)

    if not text_norm:
        return False

    known_keywords = get_all_known_keywords()

    for keyword in known_keywords:
        if keyword in text_norm:
            return True

    return False


def extract_unknown_phrases(
    strengths_clean: str,
    challenges_clean: str,
    strength_tags: list[str],
    challenge_tags: list[str],
) -> list[str]:
    """
    Detect meaningful text that does not match the current NLP dictionary.

    This does not automatically create a new official tag.
    It only saves the unmatched phrase for researcher review.
    """

    unknown_phrases: list[str] = []

    # Check strengths text
    if (
        strengths_clean
        and not is_non_meaningful_response(strengths_clean)
        and not strength_tags
        and not contains_known_keyword(strengths_clean)
    ):
        unknown_phrases.append(strengths_clean)

    # Check challenges text
    if (
        challenges_clean
        and not is_non_meaningful_response(challenges_clean)
        and not challenge_tags
        and not contains_known_keyword(challenges_clean)
    ):
        unknown_phrases.append(challenges_clean)

    return unknown_phrases


# ---------------------------------------------------
# Cluster fallback tags
# ---------------------------------------------------

def get_segment_default_tags(segment_label: str | None) -> list[str]:
    """
    If NLP cannot detect tags, use default tags from the assigned cluster.
    """

    if segment_label is None or pd.isna(segment_label):
        return []

    label = str(segment_label).lower()

    if (
        "cluster 1" in label
        or "passive" in label
        or "moderately engaged" in label
    ):
        return [
            "motivation",
            "interaction",
            "learning_support",
            "self_paced",
        ]

    if (
        "cluster 2" in label
        or "active" in label
        or "highly engaged" in label
    ):
        return [
            "content_access",
            "engagement",
            "digital_skill",
            "self_paced",
        ]

    return [
        "balanced_support",
        "learning_guidance",
    ]


# ---------------------------------------------------
# Build rule-based recommendation text
# ---------------------------------------------------

def build_rule_based_recommendations(tags: list[str]) -> list[dict[str, str]]:
    recommendations = []

    for tag in tags:
        if tag in RECOMMENDATION_RULE_BANK:
            recommendations.append(
                {
                    "tag": tag,
                    "title": RECOMMENDATION_RULE_BANK[tag]["title"],
                    "recommendation": RECOMMENDATION_RULE_BANK[tag]["recommendation"],
                }
            )

    return recommendations


# ---------------------------------------------------
# Main function called from FastAPI
# ---------------------------------------------------

def extract_open_response_tags(
    strengths_positive_aspects: str | None,
    challenges_suggestions: str | None,
    segment_label: str | None = None,
) -> dict[str, Any]:
    """
    Main function to call from FastAPI.

    Logic:
    1. Translate Khmer/mixed responses if needed.
    2. Clean open-ended text.
    3. Detect known themes.
    4. Convert themes to recommendation tags.
    5. If known NLP tags exist, use them.
    6. If no known NLP tags exist, use cluster fallback tags.
    7. If meaningful unknown phrases exist, save them for researcher review.
    """

    # Translate text if Khmer or mixed Khmer-English
    strengths_en = translate_to_english_if_needed(strengths_positive_aspects)
    challenges_en = translate_to_english_if_needed(challenges_suggestions)

    # Clean translated text
    strengths_clean = clean_basic_text(strengths_en)
    challenges_clean = clean_basic_text(challenges_en)

    # Detect known themes
    strength_themes = detect_themes(
        strengths_clean,
        settings.strength_theme_map,
    )

    challenge_themes = detect_themes(
        challenges_clean,
        settings.challenge_theme_map,
    )

    # Convert themes to recommendation tags
    strength_tags = themes_to_tags(strength_themes)
    challenge_tags = themes_to_tags(challenge_themes)

    # These are the known tags detected from NLP
    nlp_tags = sorted(set(strength_tags + challenge_tags))

    # These are fallback tags from K-Modes cluster
    fallback_tags = get_segment_default_tags(segment_label)

    # Main logic:
    # if known_tags: use known_tags
    # else: use cluster_fallback_tags
    if nlp_tags:
        final_tags = nlp_tags
        used_fallback = False
    else:
        final_tags = fallback_tags
        used_fallback = True

    final_tags = sorted(set(final_tags))

    # Unknown phrase logic:
    # if unknown_phrases: save them for review
    unknown_phrases = extract_unknown_phrases(
        strengths_clean=strengths_clean,
        challenges_clean=challenges_clean,
        strength_tags=strength_tags,
        challenge_tags=challenge_tags,
    )

    needs_nlp_review = len(unknown_phrases) > 0

    return {
        # Language information
        "strengths_language": detect_language(strengths_positive_aspects),
        "challenges_language": detect_language(challenges_suggestions),

        # Translated text
        "strengths_final_en": strengths_en,
        "challenges_final_en": challenges_en,

        # Cleaned text
        "strengths_clean": strengths_clean,
        "challenges_clean": challenges_clean,

        # Detected known themes
        "strength_themes": strength_themes,
        "challenge_themes": challenge_themes,

        # Detected known tags
        "strength_tags": strength_tags,
        "challenge_tags": challenge_tags,
        "recommendation_tags": nlp_tags,

        # Cluster fallback tags
        "segment_default_tags": fallback_tags,

        # Final tags used by the recommendation system
        "final_recommendation_tags": final_tags,

        # Recommendation rules for final tags
        "rule_based_recommendations": build_rule_based_recommendations(final_tags),

        # Fallback status
        "used_fallback": used_fallback,

        # Unknown phrase review fields
        "unknown_phrases": unknown_phrases,
        "needs_nlp_review": needs_nlp_review,
    }


# ---------------------------------------------------
# Helper for saving tags as JSON string
# ---------------------------------------------------

def tags_to_json(tags: list[str]) -> str:
    return json.dumps(tags, ensure_ascii=False)