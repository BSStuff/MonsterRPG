"""Players router — player profile management endpoints."""

from http import HTTPStatus

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/players", tags=["Players"])


@router.get("/me", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def get_current_player() -> JSONResponse:
    """Get the authenticated player's profile."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Get current player profile"},
    )


@router.put("/me", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def update_current_player() -> JSONResponse:
    """Update the authenticated player's profile."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Update current player profile"},
    )
