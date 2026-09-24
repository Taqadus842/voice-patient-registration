"""Bonus feature tests: appointments, transcripts, dashboard."""

from tests.conftest import VALID_PATIENT


def test_schedule_appointment(client, created_patient):
    patient_id = created_patient["patient_id"]
    response = client.post(
        f"/patients/{patient_id}/appointments",
        json={
            "scheduled_for": "2026-10-01T09:30:00",
            "duration_minutes": 30,
            "reason": "New patient visit",
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["patient_id"] == patient_id
    assert data["status"] == "scheduled"
    assert data["duration_minutes"] == 30


def test_schedule_appointment_missing_patient(client):
    response = client.post(
        "/patients/00000000-0000-0000-0000-000000000000/appointments",
        json={"scheduled_for": "2026-10-01T09:30:00"},
    )
    assert response.status_code == 404
    assert response.json()["data"] is None


def test_list_patient_appointments(client, created_patient):
    patient_id = created_patient["patient_id"]
    client.post(
        f"/patients/{patient_id}/appointments",
        json={"scheduled_for": "2026-10-01T09:30:00"},
    )
    response = client.get(f"/patients/{patient_id}/appointments")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1


def test_list_all_appointments(client, created_patient):
    patient_id = created_patient["patient_id"]
    client.post(
        f"/patients/{patient_id}/appointments",
        json={"scheduled_for": "2026-10-02T14:00:00"},
    )
    response = client.get("/appointments")
    assert response.status_code == 200
    assert len(response.json()["data"]) >= 1


def test_appointment_invalid_duration(client, created_patient):
    patient_id = created_patient["patient_id"]
    response = client.post(
        f"/patients/{patient_id}/appointments",
        json={"scheduled_for": "2026-10-01T09:30:00", "duration_minutes": 5},
    )
    assert response.status_code == 422


def test_save_transcript(client, created_patient):
    patient_id = created_patient["patient_id"]
    response = client.post(
        "/transcripts",
        json={
            "patient_id": patient_id,
            "language": "en",
            "summary": "Registered Sarah Davis; confirmed demographics.",
            "transcript": "AI: Hello... Caller: Sarah...",
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["patient_id"] == patient_id
    assert data["language"] == "en"


def test_save_transcript_without_patient(client):
    response = client.post(
        "/transcripts",
        json={"summary": "Abandoned call before registration.", "language": "es"},
    )
    assert response.status_code == 201
    assert response.json()["data"]["patient_id"] is None


def test_transcript_requires_summary(client):
    response = client.post("/transcripts", json={"language": "en"})
    assert response.status_code == 422


def test_list_patient_transcripts(client, created_patient):
    patient_id = created_patient["patient_id"]
    client.post(
        "/transcripts",
        json={"patient_id": patient_id, "summary": "Done."},
    )
    response = client.get(f"/patients/{patient_id}/transcripts")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1


def test_dashboard_renders_html(client, created_patient):
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Patient Registration Dashboard" in response.text
    assert created_patient["first_name"] in response.text
