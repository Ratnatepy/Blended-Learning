"""Frontend learner segment display helpers."""

from __future__ import annotations

DEFAULT_SEGMENT_ORDER: list[str] = [
    "Highly Engaged (Active) Learners",
    "Moderately Engaged (Passive) Learners",
]

DEFAULT_SEGMENT_COLOR_MAP: dict[str, str] = {
    "Highly Engaged (Active) Learners": "#22c55e",
    "Moderately Engaged (Passive) Learners": "#ef4444",
    "Unknown": "#94a3b8",
}


def normalize_segment_label(label: object) -> str:
    """Normalize old/new segment labels without relying on Cluster 1/2 IDs."""
    if label is None:
        return "Unknown"

    raw = str(label).strip()
    lowered = raw.lower()

    if "passive" in lowered or "moderately" in lowered or "moderate" in lowered:
        return "Moderately Engaged (Passive) Learners"

    if "active" in lowered or "highly" in lowered or "high" in lowered:
        return "Highly Engaged (Active) Learners"

    return raw or "Unknown"


def ordered_segments(observed_segments: list[str], preferred_order: list[str] | tuple[str, ...] | None = None) -> list[str]:
    order = list(preferred_order or DEFAULT_SEGMENT_ORDER)
    extras = [segment for segment in observed_segments if segment not in order]
    return order + extras
