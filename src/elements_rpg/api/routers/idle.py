"""Idle router — idle tracking, offline gains, and action queue management endpoints."""

from http import HTTPStatus

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/idle", tags=["Idle & Offline"])


@router.post("/record-clear", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def record_clear() -> JSONResponse:
    """Record an area clear time for BRPM calculation."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Record area clear time"},
    )


@router.get("/tracker", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def get_idle_tracker() -> JSONResponse:
    """Get current idle tracking state and BRPM metrics."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Get idle tracker state"},
    )


@router.get("/offline-gains", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def get_offline_gains() -> JSONResponse:
    """Calculate pending offline gains (85% rate, 8hr cap)."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Calculate offline gains"},
    )


@router.get("/action-queue", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def get_action_queue() -> JSONResponse:
    """Get current action queue state (slots, active actions)."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Get action queue state"},
    )


@router.post("/action-queue", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def add_action() -> JSONResponse:
    """Add an action to the queue (crafting, cooking, training)."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Add action to queue"},
    )


@router.post("/action-queue/{action_id}/cancel", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def cancel_action(action_id: str) -> JSONResponse:
    """Cancel a queued action."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={
            "status": "not_implemented",
            "endpoint": f"Cancel action {action_id}",
        },
    )


@router.post("/action-queue/advance", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def advance_queue() -> JSONResponse:
    """Process completed actions and return results."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Advance action queue"},
    )


@router.post("/action-queue/expand", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def expand_queue() -> JSONResponse:
    """Purchase an additional action queue slot."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Expand action queue slots"},
    )
