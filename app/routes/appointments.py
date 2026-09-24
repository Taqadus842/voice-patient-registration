"""Appointment scheduling endpoints (bonus)."""

from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import AppointmentRead, CreateAppointment
from app.services import extras_service

router = APIRouter(tags=["appointments"])


def _dump(appointment: object) -> dict:
    """Serialize an appointment ORM row."""
    return AppointmentRead.model_validate(appointment).model_dump(mode="json")


@router.post(
    "/patients/{patient_id}/appointments",
    status_code=status.HTTP_201_CREATED,
    summary="Schedule an appointment",
)
def schedule_appointment(
    patient_id: str,
    payload: CreateAppointment,
    db: Session = Depends(get_db),
) -> dict:
    """Create a mock appointment for an existing patient."""
    body = payload.model_copy(update={"patient_id": patient_id})
    appointment = extras_service.schedule_appointment(db, body)
    return {"data": _dump(appointment), "error": None}


@router.get(
    "/patients/{patient_id}/appointments",
    summary="List appointments for a patient",
)
def list_patient_appointments(
    patient_id: str, db: Session = Depends(get_db)
) -> dict:
    """Return appointments for one patient."""
    items = extras_service.list_appointments(db, patient_id=patient_id)
    return {"data": [_dump(item) for item in items], "error": None}


@router.get("/appointments", summary="List all appointments")
def list_appointments(
    patient_id: Optional[str] = None, db: Session = Depends(get_db)
) -> dict:
    """Return appointments with optional patient filter."""
    items = extras_service.list_appointments(db, patient_id=patient_id)
    return {"data": [_dump(item) for item in items], "error": None}
