"""Phone number normalization utilities."""

import re


def normalize_phone(value: str) -> str:
    """Normalize a US phone number to 10 digits.

    Accepts formats like ``5551234567``, ``(555) 123-4567``, and
    ``555-123-4567``. An optional leading country code ``1`` is stripped.
    Returns digits only.
    """
    if value is None:
        raise ValueError("Phone number is required")
    if not isinstance(value, str):
        raise ValueError("Phone number must be text")

    digits = re.sub(r"\D", "", value.strip())
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        raise ValueError("Phone number must be a 10-digit US number")
    if digits[0] in "01":
        raise ValueError("Phone number must be a valid 10-digit US number")
    return digits


def format_phone(digits: str) -> str:
    """Format a 10-digit phone number as ``(XXX) XXX-XXXX``."""
    return f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
