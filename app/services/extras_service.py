"""Business logic for appointments and call transcripts."""

import logging

from sqlalchemy.orm import Session

from app import crud_extras
from app.models import Appointment, CallTranscript
from app.schemas import CreateAppointment, CreateTranscript

logger = logging.getLogger("voice-patient-registration")


class AppointmentNotFoundException(Exception):
    """Raised when an appointment cannot be found."""

    def __init__(self, appointment_id: str) -> None:
        super().__init__(f"Appointment {appointment_id} not found")
        self.appointment_id = appointment_id


def schedule_appointment(db: Session, data: CreateAppointment) -> Appointment:
    """Schedule an appointment for an existing patient."""
    from app.services.patient_service import get_patient

    get_patient(db, data.patient_id)
    appointment = crud_extras.create_appointment(db, data)
    logger.info(
        "SCHEDULED_APPOINTMENT patient_id=%s appointment_id=%s when=%s",
        appointment.patient_id,
        appointment.appointment_id,
        appointment.scheduled_for.isoformat(),
    )
    return appointment


def list_appointments(db: Session, patient_id: str | None = None) -> list[Appointment]:
    """List appointments, ensuring the patient exists when filtered."""
    if patient_id is not None:
        from app.services.patient_service import get_patient

        get_patient(db, patient_id)
    return list(crud_extras.list_appointments(db, patient_id=patient_id))


def save_transcript(db: Session, data: CreateTranscript) -> CallTranscript:
    """Persist a call summary/transcript; validate patient_id when present."""
    if data.patient_id is not None:
        from app.services.patient_service import get_patient

        get_patient(db, data.patient_id)
    transcript = crud_extras.create_transcript(db, data)
    logger.info(
        "SAVED_TRANSCRIPT transcript_id=%s patient_id=%s language=%s",
        transcript.transcript_id,
        transcript.patient_id,
        transcript.language,
    )
    return transcript


def list_transcripts(db: Session, patient_id: str | None = None) -> list[CallTranscript]:
    """List transcripts, ensuring the patient exists when filtered."""
    if patient_id is not None:
        from app.services.patient_service import get_patient

        get_patient(db, patient_id)
    return list(crud_extras.list_transcripts(db, patient_id=patient_id))
