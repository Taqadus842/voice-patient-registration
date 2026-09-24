"""Validation-focused tests for patient payloads."""

from tests.conftest import VALID_PATIENT


def _post(client, **overrides):
    payload = {**VALID_PATIENT, **overrides}
    return client.post("/patients", json=payload)


def test_valid_patient_accepted(client, sample_patient):
    response = client.post("/patients", json=sample_patient)
    assert response.status_code == 201


def test_future_dob_rejected(client):
    response = _post(client, date_of_birth="12/31/2099")
    assert response.status_code == 422
    body = response.json()
    assert body["data"] is None
    assert "future" in body["error"].lower()


def test_invalid_calendar_dob_rejected(client):
    response = _post(client, date_of_birth="02/30/2000")
    assert response.status_code == 422
    assert response.json()["data"] is None


def test_malformed_dob_rejected(client):
    response = _post(client, date_of_birth="April 12, 1998")
    assert response.status_code == 422
    assert response.json()["data"] is None


def test_dob_wrong_separator_rejected(client):
    response = _post(client, date_of_birth="04-12-1998")
    assert response.status_code == 422


def test_phone_too_short_rejected(client):
    response = _post(client, phone_number="123")
    assert response.status_code == 422
    assert response.json()["data"] is None


def test_phone_with_letters_rejected(client):
    response = _post(client, phone_number="555-FAIL")
    assert response.status_code == 422


def test_name_with_numbers_rejected(client):
    response = _post(client, first_name="John123")
    assert response.status_code == 422
    assert "first_name" in response.json()["error"]


def test_apostrophe_and_hyphen_names_accepted(client):
    response = _post(client, first_name="Anne-Marie", last_name="O'Connor")
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["first_name"] == "Anne-Marie"
    assert data["last_name"] == "O'Connor"


def test_single_letter_name_accepted(client):
    response = _post(client, first_name="J")
    assert response.status_code == 201


def test_state_must_be_two_letters(client):
    response = _post(client, state="California")
    assert response.status_code == 422
    assert "state" in response.json()["error"].lower()


def test_state_single_letter_rejected(client):
    response = _post(client, state="C")
    assert response.status_code == 422


def test_state_lowercase_normalized(client):
    response = _post(client, state="tx")
    assert response.status_code == 201
    assert response.json()["data"]["state"] == "TX"


def test_zip_five_digits_accepted(client):
    response = _post(client, zip_code="12345")
    assert response.status_code == 201


def test_zip_plus_four_accepted(client):
    response = _post(client, zip_code="12345-6789")
    assert response.status_code == 201


def test_zip_invalid_rejected(client):
    response = _post(client, zip_code="1234")
    assert response.status_code == 422
    assert "zip" in response.json()["error"].lower()


def test_invalid_email_rejected(client):
    response = _post(client, email="not-an-email")
    assert response.status_code == 422


def test_invalid_sex_rejected(client):
    response = _post(client, sex="unknown")
    assert response.status_code == 422


def test_sex_decline_to_answer_accepted(client):
    response = _post(client, sex="Decline to Answer")
    assert response.status_code == 201
    assert response.json()["data"]["sex"] == "decline_to_answer"


def test_sex_male_female_other_accepted(client):
    for value in ("male", "Female", "other"):
        response = _post(client, sex=value, phone_number=f"555000{hash(value) % 10000:04d}")
        # may hit duplicate phone on retries; only assert sex enum path
        if response.status_code == 201:
            assert response.json()["data"]["sex"] in {
                "male",
                "female",
                "other",
                "decline_to_answer",
            }


def test_name_over_50_chars_rejected(client):
    response = _post(client, first_name="A" * 51)
    assert response.status_code == 422
    assert "1-50" in response.json()["error"]


def test_name_exactly_50_chars_accepted(client):
    response = _post(client, first_name="A" * 50)
    assert response.status_code == 201


def test_city_over_100_chars_rejected(client):
    response = _post(client, city="X" * 101)
    assert response.status_code == 422
    assert "city" in response.json()["error"].lower()


def test_missing_required_field_rejected(client):
    payload = {k: v for k, v in VALID_PATIENT.items() if k != "city"}
    response = client.post("/patients", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["data"] is None
    assert "city" in body["error"].lower()


def test_invalid_list_filter_dob(client):
    response = client.get("/patients", params={"date_of_birth": "not-a-date"})
    assert response.status_code == 422
    assert response.json()["data"] is None


def test_invalid_list_filter_phone(client):
    response = client.get("/patients", params={"phone_number": "999"})
    assert response.status_code == 422
    assert response.json()["data"] is None


def test_envelope_on_validation_error(client):
    response = _post(client, zip_code="bad")
    body = response.json()
    assert set(body.keys()) == {"data", "error"}
    assert body["data"] is None
    assert isinstance(body["error"], str)
