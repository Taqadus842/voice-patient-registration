"""Patient CRUD endpoints with a consistent response envelope."""

from typing import Optional

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import CreatePatient, PatientRead, UpdatePatient
from app.services import patient_service

router = APIRouter(tags=["patients"])


def _dump(patient: "object") -> dict:
    """Serialize a Patient ORM row into a JSON-ready dict."""
    return PatientRead.model_validate(patient).model_dump(mode="json")


@router.get(
    "/patients",
    summary="List patients",
    description="List active (non-deleted) patients with optional filters.",
)
def list_patients(
    last_name: Optional[str] = None,
    date_of_birth: Optional[str] = None,
    phone_number: Optional[str] = None,
    db: Session = Depends(get_db),
) -> dict:
    """Return a filtered list of active patients."""
    patients = patient_service.list_patients(
        db,
        last_name=last_name,
        date_of_birth=date_of_birth,
        phone_number=phone_number,
    )
    return {"data": [_dump(patient) for patient in patients], "error": None}


@router.get(
    "/patients/{patient_id}",
    summary="Get a patient",
    description="Return a single patient by id.",
)
def get_patient(patient_id: str, db: Session = Depends(get_db)) -> dict:
    """Return one patient or raise a 404."""
    patient = patient_service.get_patient(db, patient_id)
    return {"data": _dump(patient), "error": None}


@router.post(
    "/patients",
    status_code=status.HTTP_201_CREATED,
    summary="Create a patient",
    description=(
        "Create a new patient record. If an active record with the same "
        "phone number already exists, it is returned instead with status 200."
    ),
)
def create_patient(
    payload: CreatePatient,
    response: Response,
    db: Session = Depends(get_db),
) -> dict:
    """Create a patient or return the existing duplicate."""
    patient, created = patient_service.create_patient(db, payload)
    if not created:
        response.status_code = status.HTTP_200_OK
    return {"data": _dump(patient), "error": None}


@router.put(
    "/patients/{patient_id}",
    summary="Update a patient",
    description="Partially update provided fields on an existing patient.",
)
def update_patient(
    patient_id: str,
    payload: UpdatePatient,
    db: Session = Depends(get_db),
) -> dict:
    """Apply a partial update and return the updated record."""
    patient = patient_service.update_patient(db, patient_id, payload)
    return {"data": _dump(patient), "error": None}


@router.delete(
    "/patients/{patient_id}",
    summary="Soft-delete a patient",
    description="Mark a patient as deleted without removing the row.",
)
def delete_patient(patient_id: str, db: Session = Depends(get_db)) -> dict:
    """Soft-delete a patient and return the tombstoned record."""
    patient = patient_service.soft_delete(db, patient_id)
    return {"data": _dump(patient), "error": None}
