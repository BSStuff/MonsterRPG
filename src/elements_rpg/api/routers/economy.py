"""Economy router — gold balance, transactions, and area information endpoints."""

from http import HTTPStatus

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/economy", tags=["Economy"])


@router.get("/balance", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def get_balance() -> JSONResponse:
    """Get the authenticated player's gold and gems balance."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Get player balance"},
    )


@router.post("/gold/earn", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def earn_gold() -> JSONResponse:
    """Add gold to the player's balance (from combat, crafting, etc.)."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Earn gold"},
    )


@router.post("/gold/spend", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def spend_gold() -> JSONResponse:
    """Spend gold with balance validation."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Spend gold"},
    )


@router.get("/transactions", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def get_transactions() -> JSONResponse:
    """Get recent transaction history for the player."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Get transaction history"},
    )


@router.get("/areas", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def list_areas() -> JSONResponse:
    """List all available game areas."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "List all areas"},
    )


@router.get("/areas/{area_id}", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def get_area(area_id: str) -> JSONResponse:
    """Get details of a specific area including monsters and materials."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": f"Get area {area_id} details"},
    )
