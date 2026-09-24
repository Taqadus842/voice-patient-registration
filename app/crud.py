"""Low-level CRUD operations against the patients table."""

from datetime import date
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Patient, utcnow
from app.schemas import CreatePatient, UpdatePatient


def create_patient(db: Session, data: CreatePatient) -> Patient:
    """Insert a new patient record and return it."""
    payload = data.model_dump()
    patient = Patient(**payload)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def get_patient(
    db: Session, patient_id: str, include_deleted: bool = False
) -> Optional[Patient]:
    """Fetch a patient by primary key, excluding soft-deleted rows by default."""
    stmt = select(Patient).where(Patient.patient_id == patient_id)
    if not include_deleted:
        stmt = stmt.where(Patient.deleted_at.is_(None))
    return db.execute(stmt).scalar_one_or_none()


def list_patients(
    db: Session,
    last_name: Optional[str] = None,
    date_of_birth: Optional[date] = None,
    phone_number: Optional[str] = None,
) -> Sequence[Patient]:
    """List non-deleted patients with optional exact-match filters."""
    stmt = select(Patient).where(Patient.deleted_at.is_(None))
    if last_name is not None:
        stmt = stmt.where(Patient.last_name == last_name.strip())
    if date_of_birth is not None:
        stmt = stmt.where(Patient.date_of_birth == date_of_birth)
    if phone_number is not None:
        stmt = stmt.where(Patient.phone_number == phone_number)
    stmt = stmt.order_by(Patient.created_at.desc())
    return list(db.execute(stmt).scalars().all())


def update_patient(
    db: Session, patient: Patient, data: UpdatePatient
) -> Patient:
    """Apply a partial update to an existing patient record."""
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(patient, field, value)
    patient.updated_at = utcnow()
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def soft_delete_patient(db: Session, patient: Patient) -> Patient:
    """Soft-delete a patient by setting ``deleted_at``."""
    patient.deleted_at = utcnow()
    patient.updated_at = utcnow()
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def find_by_phone(db: Session, phone_number: str) -> Optional[Patient]:
    """Find a non-deleted patient by normalized phone number."""
    stmt = select(Patient).where(
        Patient.phone_number == phone_number,
        Patient.deleted_at.is_(None),
    )
    return db.execute(stmt).scalar_one_or_none()
