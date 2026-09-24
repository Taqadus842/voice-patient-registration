"""US state code validation utilities."""

import re

STATE_PATTERN = re.compile(r"^[A-Za-z]{2}$")


def validate_state(value: str) -> str:
    """Validate and normalize a two-letter US state code."""
    if not isinstance(value, str):
        raise ValueError("State must be text")
    cleaned = value.strip()
    if not STATE_PATTERN.fullmatch(cleaned):
        raise ValueError("State must be exactly 2 letters (e.g. CA, NY, TX)")
    return cleaned.upper()
