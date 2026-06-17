from __future__ import annotations

import re
from typing import Iterable

import pandas as pd


def clean_basic_text(text, cfg: dict) -> str:
    """Clean translated open-ended text using regex and replacement config."""
    if pd.isna(text):
        return ""
    value = str(text)
    if cfg.get("lowercase", True):
        value = value.lower()
    if cfg.get("strip", True):
        value = value.strip()
    whitespace_regex = cfg.get("whitespace_regex", r"\s+")
    value = re.sub(whitespace_regex, " ", value)
    for old, new in cfg.get("phrase_replacements", {}).items():
        value = value.replace(old, new)
    value = re.sub(cfg.get("punctuation_regex", r"[^\w\s]"), " ", value)
    return re.sub(whitespace_regex, " ", value).strip()


def normalize_text_for_matching(text) -> str:
    """Normalize arbitrary text before rule/theme matching."""
    if pd.isna(text):
        return ""
    value = str(text).lower().replace("_", " ")
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def is_non_meaningful_response(text, non_meaningful_set: set[str]) -> bool:
    """Check whether a response is one of the configured non-informative tokens."""
    return normalize_text_for_matching(text) in non_meaningful_set


def detect_themes(text, theme_map: dict[str, list[str]], non_meaningful_set: set[str] | None = None) -> list[str]:
    """Detect configured themes by keyword containment."""
    non_meaningful_set = non_meaningful_set or set()
    if is_non_meaningful_response(text, non_meaningful_set):
        return []
    text_norm = normalize_text_for_matching(text)
    matched: list[str] = []
    for theme, keywords in theme_map.items():
        for keyword in keywords:
            keyword_norm = normalize_text_for_matching(keyword)
            if keyword_norm and keyword_norm in text_norm:
                matched.append(theme)
                break
    return sorted(set(matched))


def themes_to_tags(themes: Iterable[str], theme_to_recommendation_map: dict[str, str]) -> list[str]:
    """Convert themes to recommendation tags using config map."""
    return sorted({theme_to_recommendation_map[theme] for theme in themes if theme in theme_to_recommendation_map})


def get_segment_default_tags(segment_label, segment_default_rules: list[dict]) -> list[str]:
    """Return configured fallback tags based on meaning-based segment label matching."""
    if pd.isna(segment_label):
        return []
    label = normalize_text_for_matching(segment_label)
    for rule in segment_default_rules:
        if any(normalize_text_for_matching(pattern) in label for pattern in rule.get("match_any", [])):
            return sorted(set(rule.get("tags", [])))
    return []


def create_final_recommendation_tags(nlp_tags, fallback_tags, use_fallback: bool = True) -> list[str]:
    """Prefer detected NLP tags, optionally falling back to segment defaults."""
    if isinstance(nlp_tags, list) and nlp_tags:
        return sorted(set(nlp_tags))
    if use_fallback:
        return sorted(set(fallback_tags or []))
    return []


def build_rule_based_recommendations(tags: Iterable[str], recommendation_rule_bank: dict) -> list[dict]:
    """Build structured recommendation records from configured tag rules."""
    recommendations = []
    for tag in tags:
        if tag in recommendation_rule_bank:
            rule = recommendation_rule_bank[tag]
            recommendations.append(
                {"tag": tag, "title": rule["title"], "recommendation": rule["recommendation"]}
            )
    return recommendations
