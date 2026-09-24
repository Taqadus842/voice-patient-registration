"""Call transcript / summary endpoints (bonus)."""

from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import CreateTranscript, TranscriptRead
from app.services import extras_service

router = APIRouter(tags=["transcripts"])


def _dump(row: object) -> dict:
    """Serialize a transcript ORM row."""
    return TranscriptRead.model_validate(row).model_dump(mode="json")


@router.post(
    "/transcripts",
    status_code=status.HTTP_201_CREATED,
    summary="Save a call transcript or summary",
)
def create_transcript(payload: CreateTranscript, db: Session = Depends(get_db)) -> dict:
    """Store a call summary (and optional full transcript)."""
    row = extras_service.save_transcript(db, payload)
    return {"data": _dump(row), "error": None}


@router.get("/transcripts", summary="List call transcripts")
def list_transcripts(
    patient_id: Optional[str] = None, db: Session = Depends(get_db)
) -> dict:
    """List stored transcripts with optional patient filter."""
    rows = extras_service.list_transcripts(db, patient_id=patient_id)
    return {"data": [_dump(row) for row in rows], "error": None}


@router.get(
    "/patients/{patient_id}/transcripts",
    summary="List transcripts for a patient",
)
def list_patient_transcripts(patient_id: str, db: Session = Depends(get_db)) -> dict:
    """List transcripts linked to one patient."""
    rows = extras_service.list_transcripts(db, patient_id=patient_id)
    return {"data": [_dump(row) for row in rows], "error": None}
