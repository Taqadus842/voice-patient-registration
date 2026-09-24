"""Patient CRUD endpoint tests."""

from tests.conftest import VALID_PATIENT


def test_create_patient(client, sample_patient):
    response = client.post("/patients", json=sample_patient)
    assert response.status_code == 201
    body = response.json()
    assert body["error"] is None
    data = body["data"]
    assert data["patient_id"]
    assert data["first_name"] == "Sarah"
    assert data["last_name"] == "Davis"
    assert data["date_of_birth"] == "1998-04-12"
    assert data["sex"] == "female"
    assert data["phone_number"] == "5551234567"
    assert data["state"] == "TX"
    assert data["zip_code"] == "78701"
    assert data["preferred_language"] == "English"
    assert data["deleted_at"] is None
    assert data["created_at"]
    assert data["updated_at"]


def test_create_patient_normalizes_phone_formats(client, sample_patient):
    cases = [
        ("5551234567", "5551234567"),
        ("555-123-4567", "5551234567"),
        ("(555) 123-4567", "5551234567"),
        ("1-555-123-4567", "5551234567"),
        ("555.987.6543", "5559876543"),
    ]
    for raw, expected in cases:
        payload = {**sample_patient, "phone_number": raw}
        response = client.post("/patients", json=payload)
        # Same normalized phone is a duplicate and returns 200 with the existing record.
        assert response.status_code in (200, 201), response.text
        assert response.json()["data"]["phone_number"] == expected


def test_list_patients(client, sample_patient):
    client.post("/patients", json=sample_patient)
    response = client.get("/patients")
    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert len(body["data"]) == 1


def test_list_patients_empty(client):
    response = client.get("/patients")
    assert response.status_code == 200
    assert response.json() == {"data": [], "error": None}


def test_list_patients_filter_by_last_name(client, sample_patient):
    client.post("/patients", json=sample_patient)
    other = {
        **sample_patient,
        "first_name": "Jane",
        "last_name": "Smith",
        "phone_number": "5559876543",
    }
    client.post("/patients", json=other)

    response = client.get("/patients", params={"last_name": "Davis"})
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1
    assert response.json()["data"][0]["last_name"] == "Davis"


def test_list_patients_filter_by_phone(client, sample_patient):
    client.post("/patients", json=sample_patient)
    response = client.get("/patients", params={"phone_number": "5551234567"})
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1


def test_list_patients_filter_by_dob(client, sample_patient):
    client.post("/patients", json=sample_patient)
    response = client.get("/patients", params={"date_of_birth": "04/12/1998"})
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1

    response = client.get("/patients", params={"date_of_birth": "01/01/2000"})
    assert response.status_code == 200
    assert response.json()["data"] == []


def test_get_patient(client, created_patient):
    patient_id = created_patient["patient_id"]
    response = client.get(f"/patients/{patient_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["data"]["patient_id"] == patient_id


def test_get_patient_not_found(client):
    response = client.get("/patients/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    body = response.json()
    assert body["data"] is None
    assert body["error"]


def test_update_patient_partial(client, created_patient):
    patient_id = created_patient["patient_id"]
    response = client.put(
        f"/patients/{patient_id}",
        json={"city": "Dallas", "zip_code": "75201"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["city"] == "Dallas"
    assert data["zip_code"] == "75201"
    assert data["first_name"] == "Sarah"


def test_update_patient_not_found(client):
    response = client.put(
        "/patients/00000000-0000-0000-0000-000000000000",
        json={"city": "Dallas"},
    )
    assert response.status_code == 404
    assert response.json()["data"] is None


def test_soft_delete_patient(client, created_patient):
    patient_id = created_patient["patient_id"]
    response = client.delete(f"/patients/{patient_id}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["deleted_at"] is not None

    # Deleted patients are excluded from list and get.
    assert client.get("/patients").json()["data"] == []
    assert client.get(f"/patients/{patient_id}").status_code == 404


def test_soft_delete_not_found(client):
    response = client.delete("/patients/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_duplicate_phone_returns_existing(client, sample_patient):
    first = client.post("/patients", json=sample_patient)
    assert first.status_code == 201
    first_id = first.json()["data"]["patient_id"]

    duplicate_payload = {
        **sample_patient,
        "first_name": "Sara",
        "email": "other@example.com",
    }
    second = client.post("/patients", json=duplicate_payload)
    assert second.status_code == 200
    body = second.json()
    assert body["error"] is None
    assert body["data"]["patient_id"] == first_id
    assert body["data"]["first_name"] == "Sarah"

    # Only one active record exists.
    assert len(client.get("/patients").json()["data"]) == 1


def test_duplicate_phone_allows_new_registration_after_soft_delete(
    client, sample_patient
):
    first = client.post("/patients", json=sample_patient)
    patient_id = first.json()["data"]["patient_id"]
    client.delete(f"/patients/{patient_id}")

    second = client.post("/patients", json=sample_patient)
    assert second.status_code == 201
    assert second.json()["data"]["patient_id"] != patient_id


def test_error_envelope_shape_on_404(client):
    response = client.get("/patients/missing-id")
    body = response.json()
    assert set(body.keys()) == {"data", "error"}
    assert body["data"] is None
    assert isinstance(body["error"], str)


def test_create_minimal_patient_without_optional_fields(client, sample_patient):
    payload = {
        key: sample_patient[key]
        for key in [
            "first_name",
            "last_name",
            "date_of_birth",
            "sex",
            "phone_number",
            "address_line_1",
            "city",
            "state",
            "zip_code",
        ]
    }
    response = client.post("/patients", json=payload)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["email"] is None
    assert data["preferred_language"] == "English"
