# Voice Patient Registration API

Production-ready voice AI patient registration system. A Vapi-powered phone agent collects patient demographics conversationally, validates input, confirms with the caller, and saves records through a FastAPI backend backed by SQLite.

## Project overview

The system has two entry points:

1. **REST API** — CRUD endpoints for patient records with a consistent response envelope, Pydantic validation, and soft deletes.
2. **Voice agent** — a Vapi assistant (OpenAI GPT-4o Mini) with a system prompt and tool schema that calls the REST API to persist confirmed registrations.

Architecture highlights:

- **Clean architecture**: routes → service layer → CRUD → SQLAlchemy models.
- **Validation**: all input validation lives in Pydantic schemas backed by shared validators.
- **Soft delete**: records are never permanently removed; `deleted_at` marks tombstones.
- **Duplicate detection**: if an active record already exists for a phone number, that record is returned (supports returning callers).

## ASCII architecture

```
Caller
   │
Twilio Number
   │
Vapi Voice Agent
   │
GPT-4o Mini
   │
FastAPI
   │
SQLite
```

## Tech stack

| Layer      | Technology                          |
| ---------- | ----------------------------------- |
| Language   | Python 3.12+                        |
| Web        | FastAPI, Uvicorn                    |
| ORM        | SQLAlchemy 2                        |
| Validation | Pydantic v2 (`pydantic[email]`)     |
| Database   | SQLite                              |
| Voice      | Vapi, OpenAI GPT-4o Mini, Twilio    |
| Tests      | pytest, httpx                       |
| Deploy     | Railway (Nixpacks)                  |

### Tech stack justification

| Choice | Why |
| ------ | --- |
| **FastAPI** | Native async, automatic OpenAPI/Swagger, first-class Pydantic integration — ideal for a small REST API that reviewers will hit with curl and `/docs`. |
| **Pydantic v2** | One place for request validation and response serialization; matches the assessment’s “validate all inputs server-side” rule without boilerplate. |
| **SQLAlchemy 2** | Typed, maintainable ORM with soft-delete and partial-update patterns; easy to swap SQLite → Postgres via `DATABASE_URL`. |
| **SQLite** | Zero-config, file-backed persistence that survives restarts — meets the NFR without ops overhead for a take-home. |
| **Vapi + Twilio + GPT-4o Mini** | Recommended path in the assessment: real U.S. number, low-latency tool calling into `POST /patients`, fast prompt iteration. |
| **pytest + httpx** | Exercises every endpoint and validation edge case without a live phone line. |
| **Railway** | One-click deploy from GitHub with `railway.json`; env vars for secrets; free-tier friendly for review. |

## Folder structure

```
voice-patient-registration/
│
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, CORS, handlers, logging
│   ├── database.py             # Engine, session, Base
│   ├── models.py               # Patient, Appointment, CallTranscript
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── validators.py           # Shared field validators
│   ├── crud.py                 # Patient CRUD
│   ├── crud_extras.py          # Appointment/transcript CRUD
│   ├── seed.py                 # Optional demo seed data
│   │
│   ├── routes/
│   │   ├── patients.py         # /patients CRUD endpoints
│   │   ├── appointments.py     # /patients/{id}/appointments, /appointments
│   │   ├── transcripts.py      # /transcripts (call summaries)
│   │   ├── dashboard.py        # /dashboard HTML UI
│   │   └── health.py           # /health endpoint
│   │
│   ├── services/
│   │   ├── patient_service.py  # Patient business logic + REGISTERED_PATIENT log
│   │   └── extras_service.py   # Appointments + transcripts logic
│   │
│   ├── utils/
│   │   ├── phone.py            # Phone normalization
│   │   └── state_validator.py  # State code validation
│   │
│   └── vapi/
│       ├── assistant_prompt.md # Voice agent system prompt (EN/ES, scheduling)
│       └── tool_schema.json    # create / schedule / transcript tools
│
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_patients.py
│   ├── test_validation.py
│   └── test_bonuses.py
│
├── requirements.txt
├── README.md
├── .env.example
├── railway.json
├── pytest.ini
├── .gitignore
└── patients.db                 # Created at runtime
```

## Installation / setup instructions

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Environment

`.env` values:

```env
OPENAI_API_KEY=
DATABASE_URL=sqlite:///patients.db
API_BASE_URL=https://your-app.railway.app
PORT=8000
```

| Variable          | Purpose                                            |
| ----------------- | -------------------------------------------------- |
| `OPENAI_API_KEY`  | Used by the Vapi/OpenAI voice assistant            |
| `DATABASE_URL`    | SQLAlchemy database URL (SQLite by default)        |
| `API_BASE_URL`    | Public base URL used by the Vapi tool schema       |
| `PORT`            | Uvicorn port (set automatically on Railway)        |

## Run locally

```bash
uvicorn app.main:app --reload
```

The database tables are created automatically on startup.

## Swagger

Interactive API docs:

```
http://localhost:8000/docs
```

Raw OpenAPI schema:

```
http://localhost:8000/openapi.json
```

## API

### Response envelope

Success:

```json
{
  "data": { "...": "..." },
  "error": null
}
```

Failure:

```json
{
  "data": null,
  "error": "Human readable message"
}
```

`GET /health` returns `{"status": "ok"}` (no envelope).

### Endpoints

| Method | Path                    | Description                                      |
| ------ | ----------------------- | ------------------------------------------------ |
| GET    | `/health`               | Liveness check                                   |
| GET    | `/patients`             | List active patients (optional filters)          |
| GET    | `/patients/{id}`        | Fetch one patient (404 if missing/deleted)       |
| POST   | `/patients`             | Create patient (201; 200 if duplicate phone)     |
| PUT    | `/patients/{id}`        | Partial update of provided fields                |
| DELETE | `/patients/{id}`        | Soft delete (sets `deleted_at`)                  |

Query filters for `GET /patients`: `last_name`, `date_of_birth` (`MM/DD/YYYY`), `phone_number`.

### Validation rules

- **Name** — letters, spaces, hyphens, apostrophes (`Anne-Marie`, `O'Connor`); no numbers.
- **DOB** — `MM/DD/YYYY`, valid calendar date, not in the future (422 otherwise).
- **Phone** — accepts `5551234567`, `(555) 123-4567`, `555-123-4567`; stores digits only.
- **State** — exactly 2 letters; stored uppercase.
- **ZIP** — `12345` or `12345-6789`.
- **Email** — RFC-validated via `EmailStr`.

## API examples (curl)

Create a patient:

```bash
curl -X POST http://localhost:8000/patients \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Sarah",
    "last_name": "Davis",
    "date_of_birth": "04/12/1998",
    "sex": "female",
    "phone_number": "(555) 123-4567",
    "email": "sarah@example.com",
    "address_line_1": "123 Main Street",
    "city": "Austin",
    "state": "TX",
    "zip_code": "78701",
    "preferred_language": "English"
  }'
```

List patients with a filter:

```bash
curl "http://localhost:8000/patients?last_name=Davis"
```

Get one patient:

```bash
curl http://localhost:8000/patients/PATIENT_UUID
```

Update a patient (partial):

```bash
curl -X PUT http://localhost:8000/patients/PATIENT_UUID \
  -H "Content-Type: application/json" \
  -d '{"city": "Dallas", "zip_code": "75201"}'
```

Soft delete:

```bash
curl -X DELETE http://localhost:8000/patients/PATIENT_UUID
```

Health check:

```bash
curl http://localhost:8000/health
```

## Tests

```bash
pytest
```

Coverage includes:

- Health endpoint
- Create patient
- Invalid DOB (future / malformed / non-calendar)
- Invalid phone
- List, get, update, soft delete
- Duplicate phone detection
- Name/state/ZIP/email/sex validation
- Response envelope shape on errors

## Deployment

Public GitHub repo + live API URL + live phone number are required for review.

### API (Railway)

1. Push this repository to GitHub.
2. In [Railway](https://railway.app), create a new project → **Deploy from GitHub repo**.
3. Railway detects `railway.json` / Nixpacks. Set the start command (already provided):

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

4. Add environment variables in Railway:
   - `OPENAI_API_KEY`
   - `DATABASE_URL` (default `sqlite:///patients.db` works for a demo volume; use a persistent volume or external DB for production)
   - `API_BASE_URL` (your Railway public domain, e.g. `https://your-app.up.railway.app`)
5. Deploy. Verify `https://your-app.up.railway.app/health` returns `{"status":"ok"}`.
6. For durable storage on Railway, attach a Volume mounted so `patients.db` persists across deploys, or point `DATABASE_URL` at a managed Postgres/MySQL database.

Other acceptable hosts: Render, Fly.io, Replit, or ngrok (local + tunnel).

### Live phone number (Twilio + Vapi)

1. Buy/assign a U.S. number in Twilio.
2. Point the Twilio number’s voice webhook at your Vapi-assigned number (or use Vapi’s Twilio import).
3. Attach the number to the Vapi assistant (steps below).
4. Put the live API URL in the tool schema’s `{{API_BASE_URL}}`.
5. Call the number end-to-end and confirm registration appears via `GET /patients`.

## Vapi setup

1. Create a new **Assistant** in Vapi.
2. Set the model to **OpenAI GPT-4o Mini** and add your OpenAI API key.
3. Paste the contents of `app/vapi/assistant_prompt.md` into the assistant **system prompt** / first message.
4. Import `app/vapi/tool_schema.json` as a custom tool (`create_patient_record`).
5. Replace `{{API_BASE_URL}}` with your deployed API base URL (or set Vapi variable substitution for it).
6. Attach a **Twilio phone number** to the assistant.
7. Call the number and complete a registration end-to-end.

## Security

- **No hardcoded secrets** — `OPENAI_API_KEY` and friends come only from environment variables (`.env` is gitignored; `.env.example` has empty placeholders).
- **Server-side input sanitization** — every field is stripped/normalized and validated in Pydantic (names, DOB, phone → digits, state, ZIP, email, city length, sex enum) before it touches the database.
- **Soft delete** — no destructive `DELETE` of rows; reduces accidental data loss.
- **Not production-hardened** — no authn/authz, rate limiting, or HIPAA controls (see Known limitations).

## Observability

- Structured Python logging to **stdout** (picked up by Railway/Render logs).
- Every completed registration emits a greppable `REGISTERED_PATIENT:` JSON payload.
- Duplicate phone hits log `DUPLICATE_PATIENT`.
- Unhandled exceptions log a stack trace and return a generic 500 envelope (no stack traces leaked to clients).
- Uvicorn/FastAPI request logs show method, path, and status for each API call.
- Call summaries/transcripts can be stored via `POST /transcripts` (linked to `patient_id`); full raw audio remains in Vapi/Twilio.

## Logging

Every completed registration is logged to stdout (and the log stream) with a greppable marker:

```
REGISTERED_PATIENT:
{
  "patient_id": "...",
  "first_name": "Sarah",
  ...
}
```

Also logged: `SCHEDULED_APPOINTMENT`, `SAVED_TRANSCRIPT`, `DUPLICATE_PATIENT`, and per-request access lines.

## Bonus features

| Bonus | Status | How |
| ----- | ------ | --- |
| Duplicate detection by phone | ✅ | Service returns existing patient (HTTP 200); prompt offers update |
| Appointment scheduling (mock) | ✅ | `POST /patients/{id}/appointments`, `GET /appointments`; voice tool `schedule_appointment` |
| Multi-language (Spanish) | ✅ | Prompt switches on “Hablo español”; `preferred_language` + transcript `language=es` |
| Call transcript/summary | ✅ | `POST /transcripts`, `GET /patients/{id}/transcripts`; voice tool `save_call_transcript` |
| Dashboard UI | ✅ | `GET /dashboard` — server-rendered table of active patients |
| Automated tests | ✅ | `pytest` — 55+ tests across CRUD, validation, bonuses |

```bash
# Example: schedule
curl -X POST http://localhost:8000/patients/PATIENT_UUID/appointments \
  -H "Content-Type: application/json" \
  -d '{"scheduled_for": "2026-10-01T09:30:00", "reason": "New patient visit"}'

# Example: transcript
curl -X POST http://localhost:8000/transcripts \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "PATIENT_UUID", "language": "en", "summary": "Registered and confirmed demographics."}'

# Dashboard
open http://localhost:8000/dashboard
```

## Known limitations

- **HIPAA is not implemented** — no encryption at rest/in transit guarantees, BAAs, audit logging, or access controls. Do not use with real PHI in this state.
- SQLite is fine for demos, not for multi-instance production concurrency.
- No authentication/authorization on the REST API.
- Appointments are **mock** slots (no real calendar/EMR integration); clinical charting is out of scope.
- Duplicate detection is phone-based only.
- Spanish support is prompt-driven (no separate locale files or STT language pack config here).
- A live U.S. phone number depends on your Twilio + Vapi accounts (not provisioned by this repo).

## Trade-offs

- **SQLite vs Postgres** — SQLite keeps setup zero-config and Railway-friendly for a take-home demo; it trades away multi-writer concurrency and easy horizontal scaling. `DATABASE_URL` can point at Postgres without code changes.
- **Soft delete vs hard delete** — Soft deletes preserve an audit trail and support “returning caller” flows, but leave tombstone rows that queries must filter (`deleted_at IS NULL`).
- **Phone-based duplicate detection** — Matching on normalized phone is simple and works for returning callers, but shared landlines or number changes can create false positives/negatives.
- **Voice logic in the prompt, not code** — Conversation quality, corrections, and confirmation live in the Vapi system prompt for fast iteration; complex branching is harder to unit-test than Python control flow.
- **No API auth** — Open endpoints make reviewer testing easy; they are unsafe for production PHI.
- **Partial PUT** — Only provided fields update (common REST practice); clients cannot distinguish “clear field” vs “leave unchanged” for optional fields unless they send `null` explicitly.
- **State auto-uppercase** — Accepting `tx` and storing `TX` is friendlier for voice input; strictly uppercase-only input would be more rigid per the letter of the spec.
- **Mock scheduling** — Demonstrates post-registration flow without building a real booking system.

## Next steps

- Wire appointments to a real calendar/EMR
- Deeper Spanish (STT/TTS locale config in Vapi, clinical phrase glossary)
- Full transcript QA UI and retention policy
- API authentication and rate limiting
- HIPAA-ready hardening (encryption, audit trail, access controls)
