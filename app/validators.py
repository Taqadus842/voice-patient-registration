"""Reusable validation helpers for patient fields."""

import re
from datetime import date

from app.utils.phone import normalize_phone
from app.utils.state_validator import validate_state

__all__ = [
    "validate_name",
    "validate_date_of_birth",
    "parse_date_of_birth",
    "normalize_phone",
    "validate_state",
    "validate_zip_code",
]

NAME_PATTERN = re.compile(r"^[A-Za-z](?:[A-Za-z' -]*[A-Za-z])?$")
DOB_PATTERN = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")
ZIP_PATTERN = re.compile(r"^\d{5}(?:-\d{4})?$")


def validate_name(value: str, field_label: str = "Name") -> str:
    """Validate a human name: 1-50 chars, letters/spaces/hyphens/apostrophes."""
    if not isinstance(value, str):
        raise ValueError(f"{field_label} must be text")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_label} is required")
    if len(cleaned) < 1 or len(cleaned) > 50:
        raise ValueError(f"{field_label} must be 1-50 characters")
    if not NAME_PATTERN.fullmatch(cleaned):
        raise ValueError(
            f"{field_label} may only contain letters, spaces, hyphens, and apostrophes"
        )
    return cleaned


def validate_city(value: str) -> str:
    """Validate city: 1-100 characters after stripping."""
    if not isinstance(value, str):
        raise ValueError("City must be text")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("City is required")
    if len(cleaned) > 100:
        raise ValueError("City must be 1-100 characters")
    return cleaned


def parse_date_of_birth(value: str) -> date:
    """Parse a date of birth string in MM/DD/YYYY format."""
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise ValueError("Date of birth must be a string in MM/DD/YYYY format")

    text = value.strip()
    match = DOB_PATTERN.fullmatch(text)
    if not match:
        raise ValueError("Date of birth must be a valid date in MM/DD/YYYY format")

    month, day, year = (int(part) for part in match.groups())
    try:
        parsed = date(year, month, day)
    except ValueError as exc:
        raise ValueError("Date of birth is not a valid calendar date") from exc

    if parsed > date.today():
        raise ValueError("Date of birth cannot be in the future")
    return parsed


def validate_date_of_birth(value: str) -> date:
    """Validate and normalize a date of birth input."""
    return parse_date_of_birth(value)


def validate_zip_code(value: str) -> str:
    """Validate a US ZIP code (12345 or 12345-6789)."""
    if not isinstance(value, str):
        raise ValueError("ZIP code must be text")
    cleaned = value.strip()
    if not ZIP_PATTERN.fullmatch(cleaned):
        raise ValueError("ZIP code must be 12345 or 12345-6789 format")
    return cleaned
