"""SQLAlchemy ORM models."""

import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum as SAEnum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Sex(str, enum.Enum):
    """Allowed sex values for patient registration."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    DECLINE_TO_ANSWER = "decline_to_answer"


def utcnow() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    """Generate a new UUID string primary key."""
    return str(uuid.uuid4())


class Patient(Base):
    """Patient demographic record with soft-delete support."""

    __tablename__ = "patients"

    patient_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid, nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    sex: Mapped[Sex] = mapped_column(
        SAEnum(
            Sex,
            name="sex_enum",
            native_enum=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line_1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line_2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(10), nullable=False)
    insurance_provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    insurance_member_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    preferred_language: Mapped[str] = mapped_column(
        String(50), nullable=False, default="English"
    )
    emergency_contact_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    emergency_contact_phone: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        """Return a readable representation of the patient."""
        return f"<Patient {self.patient_id} {self.first_name} {self.last_name}>"


class AppointmentStatus(str, enum.Enum):
    """Lifecycle status for a scheduled appointment."""

    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Appointment(Base):
    """Mock first-visit appointment linked to a patient."""

    __tablename__ = "appointments"

    appointment_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid, nullable=False
    )
    patient_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(nullable=False, default=30)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[AppointmentStatus] = mapped_column(
        SAEnum(
            AppointmentStatus,
            name="appointment_status_enum",
            native_enum=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=AppointmentStatus.SCHEDULED,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        """Return a readable representation of the appointment."""
        return f"<Appointment {self.appointment_id} patient={self.patient_id}>"


class CallTranscript(Base):
    """Call summary/transcript linked to a patient when known."""

    __tablename__ = "call_transcripts"

    transcript_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid, nullable=False
    )
    patient_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    language: Mapped[str] = mapped_column(
        String(20), nullable=False, default="en"
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    def __repr__(self) -> str:
        """Return a readable representation of the transcript."""
        return f"<CallTranscript {self.transcript_id} patient={self.patient_id}>"
