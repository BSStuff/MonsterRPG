"""Save/Load router — game save CRUD endpoints."""

from http import HTTPStatus

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/saves", tags=["Save/Load"])


@router.post("/", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def create_save() -> JSONResponse:
    """Create a new game save for the authenticated player."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Create new game save"},
    )


@router.get("/{save_id}", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def load_save(save_id: str) -> JSONResponse:
    """Load a specific game save by ID."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": f"Load save {save_id}"},
    )


@router.put("/{save_id}", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def update_save(save_id: str) -> JSONResponse:
    """Update an existing game save."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": f"Update save {save_id}"},
    )


@router.delete("/{save_id}", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def delete_save(save_id: str) -> JSONResponse:
    """Delete a game save."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": f"Delete save {save_id}"},
    )
