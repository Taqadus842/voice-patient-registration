"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Service health check",
    response_description="Health status payload",
)
def health_check() -> dict:
    """Return a simple liveness payload."""
    return {"status": "ok"}
