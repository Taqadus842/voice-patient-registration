"""Shared pytest fixtures for the test suite."""

import os
from pathlib import Path

# Ensure a dedicated test database is used before the app imports database.py.
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_patients.db")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

VALID_PATIENT = {
    "first_name": "Sarah",
    "last_name": "Davis",
    "date_of_birth": "04/12/1998",
    "sex": "female",
    "phone_number": "(555) 123-4567",
    "email": "sarah.davis@example.com",
    "address_line_1": "123 Main Street",
    "address_line_2": "Apt 4B",
    "city": "Austin",
    "state": "TX",
    "zip_code": "78701",
    "insurance_provider": "Blue Cross",
    "insurance_member_id": "BC12345",
    "preferred_language": "English",
    "emergency_contact_name": "John Davis",
    "emergency_contact_phone": "555-987-6543",
}


@pytest.fixture()
def client():
    """Provide a TestClient with a fresh database for each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def sample_patient():
    """Return a copy of the valid patient payload."""
    return dict(VALID_PATIENT)


@pytest.fixture()
def created_patient(client, sample_patient):
    """Create a patient and return the response data payload."""
    response = client.post("/patients", json=sample_patient)
    assert response.status_code == 201, response.text
    return response.json()["data"]
