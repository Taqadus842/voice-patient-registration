"""Optional demo seed data for the patients table.

Run manually:

    python -m app.seed

Or set ``SEED_DEMO_DATA=true`` before starting the API to seed on startup
when the table is empty.
"""

import logging
from datetime import date

from sqlalchemy.orm import Session

from app.crud import create_patient, find_by_phone
from app.database import SessionLocal
from app.schemas import CreatePatient

logger = logging.getLogger("voice-patient-registration")

SEED_PATIENTS: list[dict] = [
    {
        "first_name": "Jane",
        "last_name": "Doe",
        "date_of_birth": date(1985, 6, 15),
        "sex": "female",
        "phone_number": "5551112222",
        "email": "jane.doe@example.com",
        "address_line_1": "456 Oak Avenue",
        "city": "Denver",
        "state": "CO",
        "zip_code": "80201",
        "preferred_language": "English",
    },
    {
        "first_name": "John",
        "last_name": "Smith",
        "date_of_birth": date(1972, 11, 3),
        "sex": "male",
        "phone_number": "5553334444",
        "email": "john.smith@example.com",
        "address_line_1": "789 Pine Road",
        "address_line_2": "Suite 200",
        "city": "Chicago",
        "state": "IL",
        "zip_code": "60601",
        "insurance_provider": "Acme Health",
        "insurance_member_id": "AH998877",
        "preferred_language": "English",
    },
]


def seed_patients(db: Session) -> int:
    """Insert seed patients if their phone numbers are not already present."""
    inserted = 0
    for row in SEED_PATIENTS:
        if find_by_phone(db, row["phone_number"]) is not None:
            continue
        create_patient(db, CreatePatient(**row))
        inserted += 1
    if inserted:
        logger.info("Seeded %s demo patient(s)", inserted)
    return inserted


def main() -> None:
    """CLI entrypoint: seed demo patients into the configured database."""
    with SessionLocal() as db:
        count = seed_patients(db)
        print(f"Seeded {count} new patient(s).")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
