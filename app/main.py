"""FastAPI application entrypoint for the Voice Patient Registration API."""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import Base, engine
from app.routes import appointments, dashboard, health, patients, transcripts
from app.services.patient_service import (
    InvalidFilterError,
    PatientNotFoundException,
)
from app.services.extras_service import AppointmentNotFoundException

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("voice-patient-registration")


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Create database tables on startup; optionally seed demo data."""
    import os

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured")
    if os.getenv("SEED_DEMO_DATA", "").lower() in {"1", "true", "yes"}:
        from app.database import SessionLocal
        from app.seed import seed_patients

        with SessionLocal() as db:
            seed_patients(db)
    yield


app = FastAPI(
    title="Voice Patient Registration API",
    version="1.0.0",
    description=(
        "Voice-enabled patient registration system with REST CRUD APIs, "
        "input validation, soft deletes, and Vapi tool integration."
    ),
    lifespan=lifespan,
    openapi_tags=[
        {"name": "health", "description": "Service health checks"},
        {
            "name": "patients",
            "description": "Patient registration CRUD operations",
        },
    ],
)


@app.middleware("http")
async def access_log_middleware(request: Request, call_next):
    """Log method, path, status, and latency for every HTTP request."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "REQUEST %s %s -> %s (%.1fms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(patients.router)
app.include_router(appointments.router)
app.include_router(transcripts.router)
app.include_router(dashboard.router)


def _envelope_error(message: str) -> dict:
    """Build a failure response envelope."""
    return {"data": None, "error": message}


@app.exception_handler(RequestValidationError)
async def request_validation_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Translate Pydantic validation errors into the response envelope."""
    messages: list[str] = []
    for error in exc.errors():
        location = ".".join(
            str(part) for part in error.get("loc", ()) if part != "body"
        )
        message = error.get("msg", "Invalid value")
        messages.append(f"{location}: {message}" if location else message)
    error_message = "; ".join(messages) or "Validation error"
    return JSONResponse(status_code=422, content=_envelope_error(error_message))


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Render HTTP errors using the response envelope."""
    headers = getattr(exc, "headers", None)
    return JSONResponse(
        status_code=exc.status_code,
        content=_envelope_error(str(exc.detail)),
        headers=headers,
    )


@app.exception_handler(PatientNotFoundException)
async def patient_not_found_handler(
    request: Request, exc: PatientNotFoundException
) -> JSONResponse:
    """Return 404 with the response envelope for missing patients."""
    return JSONResponse(status_code=404, content=_envelope_error(str(exc)))


@app.exception_handler(InvalidFilterError)
async def invalid_filter_handler(
    request: Request, exc: InvalidFilterError
) -> JSONResponse:
    """Return 422 with the response envelope for bad list filters."""
    return JSONResponse(status_code=422, content=_envelope_error(str(exc)))


@app.exception_handler(AppointmentNotFoundException)
async def appointment_not_found_handler(
    request: Request, exc: AppointmentNotFoundException
) -> JSONResponse:
    """Return 404 for missing appointments."""
    return JSONResponse(status_code=404, content=_envelope_error(str(exc)))


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a generic 500 envelope for unexpected errors."""
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content=_envelope_error("Internal server error"))
