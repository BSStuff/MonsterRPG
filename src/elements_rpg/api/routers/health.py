"""Health check endpoint for ElementsRPG API."""

from datetime import UTC, datetime

from fastapi import APIRouter

router = APIRouter(tags=["system"])

SERVICE_NAME = "ElementsRPG"
SERVICE_VERSION = "0.2.0"


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return service health status.

    No authentication required. Returns current service status,
    name, version, and UTC timestamp.
    """
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "timestamp": datetime.now(UTC).isoformat(),
    }
