"""Service layer for patient registration business logic."""

import json
import logging
from datetime import date
from typing import Optional, Sequence

from sqlalchemy.orm import Session

from app import crud
from app.models import Patient
from app.schemas import CreatePatient, UpdatePatient
from app.validators import normalize_phone, parse_date_of_birth

logger = logging.getLogger("voice-patient-registration")


class PatientNotFoundException(Exception):
    """Raised when a patient record cannot be found."""

    def __init__(self, patient_id: str) -> None:
        super().__init__(f"Patient {patient_id} not found")
        self.patient_id = patient_id


class InvalidFilterError(Exception):
    """Raised when a list filter value cannot be parsed."""


def create_patient(db: Session, data: CreatePatient) -> tuple[Patient, bool]:
    """Create a patient, or return the existing one for a duplicate phone.

    Returns:
        A tuple of ``(patient, created)`` where ``created`` is ``False``
        when an active record with the same phone number already exists.
    """
    existing = crud.find_by_phone(db, data.phone_number)
    if existing is not None:
        logger.info(
            "DUPLICATE_PATIENT phone=%s existing_id=%s",
            data.phone_number,
            existing.patient_id,
        )
        return existing, False

    patient = crud.create_patient(db, data)
    _log_registration(patient)
    return patient, True


def update_patient(
    db: Session, patient_id: str, data: UpdatePatient
) -> Patient:
    """Update a patient by id; raises ``PatientNotFoundException`` if missing."""
    patient = crud.get_patient(db, patient_id)
    if patient is None:
        raise PatientNotFoundException(patient_id)
    return crud.update_patient(db, patient, data)


def list_patients(
    db: Session,
    last_name: Optional[str] = None,
    date_of_birth: Optional[str] = None,
    phone_number: Optional[str] = None,
) -> Sequence[Patient]:
    """List patients with optional filters; raises ``InvalidFilterError``."""
    dob: Optional[date] = None
    if date_of_birth is not None:
        try:
            dob = parse_date_of_birth(date_of_birth)
        except ValueError as exc:
            raise InvalidFilterError(str(exc)) from exc

    phone: Optional[str] = None
    if phone_number is not None:
        try:
            phone = normalize_phone(phone_number)
        except ValueError as exc:
            raise InvalidFilterError(str(exc)) from exc

    return crud.list_patients(db, last_name=last_name, date_of_birth=dob, phone_number=phone)


def get_patient(db: Session, patient_id: str) -> Patient:
    """Fetch a patient by id; raises ``PatientNotFoundException`` if missing."""
    patient = crud.get_patient(db, patient_id)
    if patient is None:
        raise PatientNotFoundException(patient_id)
    return patient


def soft_delete(db: Session, patient_id: str) -> Patient:
    """Soft-delete a patient by id; raises ``PatientNotFoundException`` if missing."""
    patient = crud.get_patient(db, patient_id)
    if patient is None:
        raise PatientNotFoundException(patient_id)
    return crud.soft_delete_patient(db, patient)


def find_by_phone(db: Session, phone_number: str) -> Optional[Patient]:
    """Return the active patient for a phone number, if any."""
    try:
        normalized = normalize_phone(phone_number)
    except ValueError:
        return None
    return crud.find_by_phone(db, normalized)


def _log_registration(patient: Patient) -> None:
    """Log a completed registration in a structured, greppable format."""
    payload = {
        "patient_id": patient.patient_id,
        "first_name": patient.first_name,
        "last_name": patient.last_name,
        "date_of_birth": patient.date_of_birth.isoformat(),
        "sex": patient.sex.value if hasattr(patient.sex, "value") else str(patient.sex),
        "phone_number": patient.phone_number,
        "email": patient.email,
        "address_line_1": patient.address_line_1,
        "address_line_2": patient.address_line_2,
        "city": patient.city,
        "state": patient.state,
        "zip_code": patient.zip_code,
        "insurance_provider": patient.insurance_provider,
        "insurance_member_id": patient.insurance_member_id,
        "preferred_language": patient.preferred_language,
        "emergency_contact_name": patient.emergency_contact_name,
        "emergency_contact_phone": patient.emergency_contact_phone,
        "created_at": patient.created_at.isoformat(),
    }
    logger.info("REGISTERED_PATIENT:\n%s", json.dumps(payload, indent=2))
