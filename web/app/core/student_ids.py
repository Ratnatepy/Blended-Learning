"""Student/respondent ID validation and normalization helpers."""

from __future__ import annotations

import re
import uuid

ITC_ID_PATTERNS: tuple[str, ...] = (
    r"^e\d{8}$",          # Undergraduate: e20123456
    r"^M\d{6}$",          # Master: M061211
    r"^e\d{7}[A-Za-z]{3}$",  # PhD: e2012345NKH
    r"^p\d{8}$",          # International Program: p20123456
    r"^kpe\d{8}$",        # ITC Kep Campus: kpe20123456
    r"^tk\d{8}$",         # ITC Tboung Khmum Campus: tk20123456
)


def is_valid_itc_student_id(student_id: str) -> bool:
    if not student_id:
        return False
    cleaned = student_id.strip()
    return any(re.match(pattern, cleaned, re.IGNORECASE) for pattern in ITC_ID_PATTERNS)


def normalize_itc_student_id(student_id: str) -> str:
    """Normalize official ITC student IDs before database lookup."""
    cleaned_id = student_id.strip()

    if cleaned_id.lower().startswith(("kpe", "tk")):
        return cleaned_id.lower()

    if cleaned_id.lower().startswith(("e", "p")):
        prefix = cleaned_id[0].lower()
        rest = cleaned_id[1:]
        digits = "".join(char for char in rest if char.isdigit())
        letters = "".join(char for char in rest if char.isalpha())
        return prefix + digits + letters.upper()

    if cleaned_id.lower().startswith("m"):
        return cleaned_id.upper()

    return cleaned_id


def generate_external_student_id(prefix: str = "ext_", length: int = 10) -> str:
    return f"{prefix}{uuid.uuid4().hex[:length]}"
