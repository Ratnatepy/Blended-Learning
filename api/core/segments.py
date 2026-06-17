"""Segment-label cleanup shared by API routes and model services."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Mapping

from api.core.config import get_api_config


def _normalise_for_match(value: str | None) -> str:
    if value is None:
        return ""
    value = str(value).strip().lower().replace("_", " ")
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


@lru_cache(maxsize=1)
def known_segment_labels() -> tuple[str, ...]:
    cfg = get_api_config().get("segments", {})
    return tuple(rule["label"] for rule in cfg.get("normalization_rules", []) if "label" in rule)


def normalize_segment_label(
    label: str | None,
    cluster_label_map: Mapping[str, str] | None = None,
) -> str:
    """Convert raw/legacy cluster labels to final learner segment labels.

    Meaning-based matching is used first. Raw numeric cluster ids are only mapped
    through the supplied current model label map when configured; this avoids
    hardcoding a brittle Cluster 1/Cluster 2 meaning in route code.
    """
    cfg = get_api_config().get("segments", {})
    unknown_label = cfg.get("unknown_label", "Unknown")

    if label is None:
        return unknown_label

    raw = str(label).strip()
    if not raw:
        return unknown_label

    norm = _normalise_for_match(raw)

    for rule in cfg.get("normalization_rules", []):
        target_label = rule.get("label")
        patterns = rule.get("match_any", [])
        if target_label and any(_normalise_for_match(pattern) in norm for pattern in patterns):
            return target_label

    # Optional fallback for raw ids such as "1" or "Cluster 1". This uses the
    # current model metadata rather than a route-level hardcoded assumption.
    if cluster_label_map and cfg.get("raw_cluster_id_strategy") == "model_label_map":
        match = re.fullmatch(r"(?:cluster\s*)?(\d+(?:\.0)?)", norm)
        if match:
            key = str(int(float(match.group(1))))
            mapped = cluster_label_map.get(key)
            if mapped and mapped != raw:
                return normalize_segment_label(mapped, cluster_label_map=None)

    return raw


def clean_report_text(report: str | None) -> str | None:
    """Remove Cluster-N prefixes from stored Markdown reports without changing meaning."""
    if report is None:
        return report

    cleaned = str(report)
    cfg = get_api_config().get("segments", {})
    prefix_regex = cfg.get("strip_cluster_prefix_regex", r"\bCluster\s+\d+\s*[:\-–—]\s*")

    for segment_label in known_segment_labels():
        cleaned = re.sub(prefix_regex + re.escape(segment_label), segment_label, cleaned)

    # Also clean common exact old forms with spaces around separators.
    cleaned = re.sub(prefix_regex, "", cleaned)
    return cleaned
