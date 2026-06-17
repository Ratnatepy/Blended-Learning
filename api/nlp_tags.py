"""Runtime NLP tag extraction for new student open-ended responses.

This module now reuses the project-level NLP rules from
``blended_learning.nlp.rules`` and reads behavior from ``config.json`` instead
of duplicating notebook constants inside the API.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any

import pandas as pd

from api.core.config import get_api_config
from blended_learning.config.settings import settings
from blended_learning.nlp.rules import (
    build_rule_based_recommendations,
    clean_basic_text,
    create_final_recommendation_tags,
    detect_themes,
    get_segment_default_tags,
    normalize_text_for_matching,
)


@lru_cache(maxsize=1)
def _translation_cfg() -> dict[str, Any]:
    return getattr(settings, "translation_preprocessing", {})


@lru_cache(maxsize=1)
def _nlp_cfg() -> dict[str, Any]:
    return getattr(settings, "nlp", {})


@lru_cache(maxsize=1)
def _compiled_language_patterns() -> dict[str, re.Pattern[str]]:
    regex_cfg = _translation_cfg().get("language_detection", {}).get("regex", {})
    return {
        "khmer": re.compile(regex_cfg.get("khmer", r"[\u1780-\u17FF]")),
        "english": re.compile(regex_cfg.get("english", r"[A-Za-z]")),
    }


@lru_cache(maxsize=1)
def _non_meaningful_set() -> set[str]:
    values = _nlp_cfg().get("tagging", {}).get("non_meaningful_responses", [])
    return {normalize_text_for_matching(value) for value in values}


@lru_cache(maxsize=1)
def _known_keywords() -> set[str]:
    known: set[str] = set()
    for theme_map in [settings.strength_theme_map, settings.challenge_theme_map]:
        for keywords in theme_map.values():
            known.update(
                keyword_norm
                for keyword in keywords
                if (keyword_norm := normalize_text_for_matching(keyword))
            )
    return known


def detect_language(text: str | None) -> str:
    """Detect empty, Khmer, English, mixed, or other text using config regex."""
    labels = _translation_cfg().get("language_detection", {}).get("labels", {})
    empty_label = labels.get("empty", "empty")

    if text is None or pd.isna(text):
        return empty_label

    value = str(text).strip()
    if not value:
        return empty_label

    patterns = _compiled_language_patterns()
    has_khmer = bool(patterns["khmer"].search(value))
    has_english = bool(patterns["english"].search(value))

    if has_khmer and has_english:
        return labels.get("mixed", "mixed")
    if has_khmer:
        return labels.get("khmer", "kh")
    if has_english:
        return labels.get("english", "en")
    return labels.get("other", "other")


def translate_to_english_if_needed(text: str | None) -> str:
    """Translate Khmer/mixed responses using TranslateKH when configured.

    If credentials/network are unavailable, the original text is returned so the
    API remains usable for demos and local testing.
    """
    if text is None or pd.isna(text):
        return ""

    value = str(text).strip()
    if not value:
        return ""

    translation_cfg = _translation_cfg().get("translation", {})
    api_runtime_cfg = get_api_config().get("nlp_runtime", {})
    if not api_runtime_cfg.get("translation_enabled", True):
        return value

    language = detect_language(value)
    translate_languages = set(translation_cfg.get("languages_requiring_translation", ["kh", "mixed"]))
    if language not in translate_languages:
        return value

    try:
        from blended_learning.nlp.translate_kh_service import TranslateKHService

        service = TranslateKHService()
        translated = service.translate_one(
            value,
            src_lang=translation_cfg.get("src_lang", "kh"),
            tgt_lang=translation_cfg.get("tgt_lang", "eng"),
        )
        if translated:
            return translated
        if translation_cfg.get("fallback_to_original_on_empty_translation", True):
            return value
        return ""
    except Exception:
        if api_runtime_cfg.get("fallback_to_original_on_translation_error", True):
            return value
        return ""


def is_non_meaningful_response(text: str | None) -> bool:
    """Return True when text is one of the configured non-informative tokens."""
    return normalize_text_for_matching(text) in _non_meaningful_set()


def themes_to_tags(themes: list[str]) -> list[str]:
    """Convert theme names into recommendation tags using config mapping."""
    mapping = settings.theme_to_recommendation_map
    return sorted({mapping[theme] for theme in themes if theme in mapping})


def contains_known_keyword(text: str | None) -> bool:
    text_norm = normalize_text_for_matching(text)
    return bool(text_norm and any(keyword in text_norm for keyword in _known_keywords()))


def extract_unknown_phrases(
    strengths_clean: str,
    challenges_clean: str,
    strength_tags: list[str],
    challenge_tags: list[str],
) -> list[str]:
    """Collect meaningful unmatched text for researcher review."""
    unknown: list[str] = []
    if (
        strengths_clean
        and not is_non_meaningful_response(strengths_clean)
        and not strength_tags
        and not contains_known_keyword(strengths_clean)
    ):
        unknown.append(strengths_clean)

    if (
        challenges_clean
        and not is_non_meaningful_response(challenges_clean)
        and not challenge_tags
        and not contains_known_keyword(challenges_clean)
    ):
        unknown.append(challenges_clean)

    return unknown


def extract_open_response_tags(
    strengths_positive_aspects: str | None,
    challenges_suggestions: str | None,
    segment_label: str | None = None,
) -> dict[str, Any]:
    """Extract themes, tags, fallback tags, and rule-based recommendations."""
    nlp_cfg = _nlp_cfg()
    tagging_cfg = nlp_cfg.get("tagging", {})

    strengths_en = translate_to_english_if_needed(strengths_positive_aspects)
    challenges_en = translate_to_english_if_needed(challenges_suggestions)

    strengths_clean = clean_basic_text(strengths_en, nlp_cfg.get("text_cleaning", {}))
    challenges_clean = clean_basic_text(challenges_en, nlp_cfg.get("text_cleaning", {}))

    strength_themes = detect_themes(
        strengths_clean,
        settings.strength_theme_map,
        non_meaningful_set=_non_meaningful_set(),
    )
    challenge_themes = detect_themes(
        challenges_clean,
        settings.challenge_theme_map,
        non_meaningful_set=_non_meaningful_set(),
    )

    strength_tags = themes_to_tags(strength_themes)
    challenge_tags = themes_to_tags(challenge_themes)
    nlp_tags = sorted(set(strength_tags + challenge_tags))

    fallback_tags = get_segment_default_tags(
        segment_label,
        tagging_cfg.get("segment_default_tags", []),
    )
    final_tags = create_final_recommendation_tags(
        nlp_tags,
        fallback_tags,
        use_fallback=tagging_cfg.get("use_segment_fallback_when_nlp_tags_empty", True),
    )

    unknown_phrases = extract_unknown_phrases(
        strengths_clean=strengths_clean,
        challenges_clean=challenges_clean,
        strength_tags=strength_tags,
        challenge_tags=challenge_tags,
    )

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
        "final_recommendation_tags": final_tags,
        "rule_based_recommendations": build_rule_based_recommendations(
            final_tags,
            nlp_cfg.get("recommendation_rule_bank", {}),
        ),
        "used_fallback": not bool(nlp_tags),
        "unknown_phrases": unknown_phrases,
        "needs_nlp_review": bool(unknown_phrases),
    }


def tags_to_json(tags: list[str]) -> str:
    """Serialize tags using the configured JSON behavior."""
    json_cfg = _nlp_cfg().get("json_serialisation", {})
    return json.dumps(tags, ensure_ascii=bool(json_cfg.get("ensure_ascii", False)))
