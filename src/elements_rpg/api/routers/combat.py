"""Combat router — combat session management and execution endpoints."""

from http import HTTPStatus

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/combat", tags=["Combat"])


@router.post("/start", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def start_combat() -> JSONResponse:
    """Start a new combat session in the current area with the active team."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Start combat session"},
    )


@router.post("/{session_id}/round", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def process_round(session_id: str) -> JSONResponse:
    """Process one combat round and return results."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={
            "status": "not_implemented",
            "endpoint": f"Process round for session {session_id}",
        },
    )


@router.post("/{session_id}/finish", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def finish_combat(session_id: str) -> JSONResponse:
    """End a combat session and calculate rewards."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={
            "status": "not_implemented",
            "endpoint": f"Finish combat session {session_id}",
        },
    )


@router.get("/{session_id}", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def get_combat_session(session_id: str) -> JSONResponse:
    """Get the current state of a combat session."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={
            "status": "not_implemented",
            "endpoint": f"Get combat session {session_id}",
        },
    )


@router.get("/{session_id}/log", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def get_combat_log(session_id: str) -> JSONResponse:
    """Get the combat log for a session."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={
            "status": "not_implemented",
            "endpoint": f"Get combat log for session {session_id}",
        },
    )
