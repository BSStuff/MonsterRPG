"""Taming router — taming chance calculation, attempts, and pity tracking."""

from http import HTTPStatus

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/taming", tags=["Taming"])


@router.get("/{species_id}/chance", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def get_taming_chance(species_id: str) -> JSONResponse:
    """Calculate the current taming chance for a species (includes pity bonus)."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={
            "status": "not_implemented",
            "endpoint": f"Get taming chance for species {species_id}",
        },
    )


@router.post("/attempt", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def attempt_taming() -> JSONResponse:
    """Attempt to tame a monster. Returns success/fail and updated pity state."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Attempt to tame a monster"},
    )


@router.get("/tracker", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def get_taming_tracker() -> JSONResponse:
    """Get current pity counters for all species."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Get taming pity tracker"},
    )
