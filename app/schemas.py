"""Pydantic schemas for request validation and response serialization."""

from datetime import date, datetime
from typing import Annotated, Any, Optional

from pydantic import BaseModel, BeforeValidator, ConfigDict, EmailStr, field_validator

from app.models import Sex
from app.validators import (
    normalize_phone,
    parse_date_of_birth,
    validate_city,
    validate_name,
    validate_state,
    validate_zip_code,
)

SEX_ALIASES = {
    "m": "male",
    "man": "male",
    "f": "female",
    "woman": "female",
    "prefer_not_to_say": "decline_to_answer",
    "declined": "decline_to_answer",
    "prefer_not_to_answer": "decline_to_answer",
}


def _parse_dob(value: Any) -> Any:
    """Coerce MM/DD/YYYY input into a ``date`` object."""
    if value is None or isinstance(value, date):
        return value
    return parse_date_of_birth(value)


DOBField = Annotated[date, BeforeValidator(_parse_dob)]


def _parse_sex(value: Any) -> Any:
    """Normalize spoken sex values to enum values (e.g. 'Decline to Answer')."""
    if value is None or isinstance(value, Sex):
        return value
    if not isinstance(value, str):
        return value
    cleaned = value.strip().lower().replace("-", "_").replace(" ", "_")
    return SEX_ALIASES.get(cleaned, cleaned)


SexField = Annotated[Sex, BeforeValidator(_parse_sex)]


def _optional_phone(value: Any) -> Any:
    """Normalize an optional phone number, allowing None/empty."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    return normalize_phone(value)


OptionalPhoneField = Annotated[str, BeforeValidator(_optional_phone)]


class PatientBase(BaseModel):
    """Shared patient fields for create and read operations."""

    first_name: str
    last_name: str
    date_of_birth: DOBField
    sex: SexField
    phone_number: str
    email: Optional[EmailStr] = None
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: str = "English"
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def _check_name(cls, value: str, info: Any) -> str:
        """Validate person names (1-50 chars)."""
        label = info.field_name.replace("_", " ").title()
        return validate_name(value, field_label=label)

    @field_validator("phone_number", mode="before")
    @classmethod
    def _check_phone(cls, value: Any) -> str:
        """Normalize phone number to digits only."""
        return normalize_phone(value)

    @field_validator("emergency_contact_phone", mode="before")
    @classmethod
    def _check_emergency_phone(cls, value: Any) -> Any:
        """Normalize optional emergency contact phone."""
        return _optional_phone(value)

    @field_validator("state")
    @classmethod
    def _check_state(cls, value: str) -> str:
        """Validate two-letter state code."""
        return validate_state(value)

    @field_validator("zip_code")
    @classmethod
    def _check_zip(cls, value: str) -> str:
        """Validate US ZIP code."""
        return validate_zip_code(value)

    @field_validator("city")
    @classmethod
    def _check_city(cls, value: str) -> str:
        """Validate city length (1-100)."""
        return validate_city(value)

    @field_validator("address_line_1", "preferred_language")
    @classmethod
    def _check_required_text(cls, value: str) -> str:
        """Ensure required text fields are non-empty after stripping."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Field is required")
        return value.strip()


class CreatePatient(PatientBase):
    """Schema for creating a new patient."""


class UpdatePatient(BaseModel):
    """Schema for partial patient updates (all fields optional)."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[DOBField] = None
    sex: Optional[SexField] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def _check_name(cls, value: Optional[str], info: Any) -> Optional[str]:
        """Validate person names when provided."""
        if value is None:
            return value
        label = info.field_name.replace("_", " ").title()
        return validate_name(value, field_label=label)

    @field_validator("phone_number", mode="before")
    @classmethod
    def _check_phone(cls, value: Any) -> Any:
        """Normalize phone number when provided."""
        return _optional_phone(value)

    @field_validator("emergency_contact_phone", mode="before")
    @classmethod
    def _check_emergency_phone(cls, value: Any) -> Any:
        """Normalize optional emergency contact phone."""
        return _optional_phone(value)

    @field_validator("state")
    @classmethod
    def _check_state(cls, value: Optional[str]) -> Optional[str]:
        """Validate state code when provided."""
        if value is None:
            return value
        return validate_state(value)

    @field_validator("zip_code")
    @classmethod
    def _check_zip(cls, value: Optional[str]) -> Optional[str]:
        """Validate ZIP code when provided."""
        if value is None:
            return value
        return validate_zip_code(value)

    @field_validator("city")
    @classmethod
    def _check_city(cls, value: Optional[str]) -> Optional[str]:
        """Validate city length when provided."""
        if value is None:
            return value
        return validate_city(value)


class PatientRead(PatientBase):
    """Schema for serializing a stored patient record."""

    model_config = ConfigDict(from_attributes=True)

    patient_id: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


def _parse_scheduled_for(value: Any) -> Any:
    """Accept ISO datetime or common spoken-ish date-time strings."""
    if value is None or isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, 9, 0, 0)
    if not isinstance(value, str):
        return value
    text = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(
            "scheduled_for must be an ISO-8601 datetime, e.g. 2026-10-01T09:30:00"
        ) from exc


ScheduledForField = Annotated[datetime, BeforeValidator(_parse_scheduled_for)]


class CreateAppointment(BaseModel):
    """Schema for scheduling a (mock) appointment."""

    patient_id: str = ""
    scheduled_for: ScheduledForField
    duration_minutes: int = 30
    reason: Optional[str] = None

    @field_validator("duration_minutes")
    @classmethod
    def _check_duration(cls, value: int) -> int:
        """Require a positive appointment length."""
        if value < 15 or value > 240:
            raise ValueError("duration_minutes must be between 15 and 240")
        return value

    @field_validator("reason")
    @classmethod
    def _check_reason(cls, value: Optional[str]) -> Optional[str]:
        """Trim optional reason text."""
        if value is None:
            return value
        return value.strip() or None


class AppointmentRead(BaseModel):
    """Schema for serializing an appointment."""

    model_config = ConfigDict(from_attributes=True)

    appointment_id: str
    patient_id: str
    scheduled_for: datetime
    duration_minutes: int
    reason: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class CreateTranscript(BaseModel):
    """Schema for storing a call summary/transcript."""

    patient_id: Optional[str] = None
    phone_number: Optional[str] = None
    language: str = "en"
    summary: str
    transcript: Optional[str] = None

    @field_validator("language")
    @classmethod
    def _check_language(cls, value: str) -> str:
        """Normalize language tag (e.g. es, en, es-MX)."""
        cleaned = value.strip().lower()
        if not cleaned or len(cleaned) > 20:
            raise ValueError("language must be a short tag such as en or es")
        return cleaned

    @field_validator("summary")
    @classmethod
    def _check_summary(cls, value: str) -> str:
        """Require a non-empty call summary."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("summary is required")
        if len(value) > 5000:
            raise ValueError("summary must be 5000 characters or fewer")
        return value.strip()

    @field_validator("phone_number", mode="before")
    @classmethod
    def _check_phone(cls, value: Any) -> Any:
        """Normalize optional phone number."""
        return _optional_phone(value)


class TranscriptRead(BaseModel):
    """Schema for serializing a stored transcript."""

    model_config = ConfigDict(from_attributes=True)

    transcript_id: str
    patient_id: Optional[str] = None
    phone_number: Optional[str] = None
    language: str
    summary: str
    transcript: Optional[str] = None
    created_at: datetime
