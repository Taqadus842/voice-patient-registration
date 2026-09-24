"""Low-level CRUD for appointments and call transcripts."""

from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Appointment, AppointmentStatus, CallTranscript, utcnow
from app.schemas import CreateAppointment, CreateTranscript


def create_appointment(db: Session, data: CreateAppointment) -> Appointment:
    """Insert a new appointment row."""
    appointment = Appointment(
        patient_id=data.patient_id,
        scheduled_for=data.scheduled_for,
        duration_minutes=data.duration_minutes,
        reason=data.reason,
        status=AppointmentStatus.SCHEDULED,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def list_appointments(
    db: Session, patient_id: Optional[str] = None
) -> Sequence[Appointment]:
    """List active appointments, optionally filtered by patient."""
    stmt = select(Appointment).where(Appointment.deleted_at.is_(None))
    if patient_id is not None:
        stmt = stmt.where(Appointment.patient_id == patient_id)
    stmt = stmt.order_by(Appointment.scheduled_for.asc())
    return list(db.execute(stmt).scalars().all())


def get_appointment(
    db: Session, appointment_id: str
) -> Optional[Appointment]:
    """Fetch one non-deleted appointment by id."""
    stmt = select(Appointment).where(
        Appointment.appointment_id == appointment_id,
        Appointment.deleted_at.is_(None),
    )
    return db.execute(stmt).scalar_one_or_none()


def soft_delete_appointment(db: Session, appointment: Appointment) -> Appointment:
    """Soft-delete an appointment."""
    appointment.deleted_at = utcnow()
    appointment.updated_at = utcnow()
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def create_transcript(db: Session, data: CreateTranscript) -> CallTranscript:
    """Insert a call transcript/summary row."""
    transcript = CallTranscript(
        patient_id=data.patient_id,
        phone_number=data.phone_number,
        language=data.language,
        summary=data.summary,
        transcript=data.transcript,
    )
    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    return transcript


def list_transcripts(
    db: Session, patient_id: Optional[str] = None
) -> Sequence[CallTranscript]:
    """List transcripts, optionally filtered by patient."""
    stmt = select(CallTranscript)
    if patient_id is not None:
        stmt = stmt.where(CallTranscript.patient_id == patient_id)
    stmt = stmt.order_by(CallTranscript.created_at.desc())
    return list(db.execute(stmt).scalars().all())
