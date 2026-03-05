"""Crafting router — recipes, crafting execution, inventory, and life skills endpoints."""

from http import HTTPStatus

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/crafting", tags=["Crafting & Life Skills"])


@router.get("/recipes", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def list_recipes() -> JSONResponse:
    """List all available crafting recipes."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "List crafting recipes"},
    )


@router.post("/execute", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def execute_craft() -> JSONResponse:
    """Craft an item — checks materials, deducts, and produces result."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Execute crafting recipe"},
    )


@router.get("/inventory", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def get_inventory() -> JSONResponse:
    """Get the player's material inventory."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Get material inventory"},
    )


@router.get("/life-skills", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def list_life_skills() -> JSONResponse:
    """List all life skills with levels and XP."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "List life skills"},
    )


@router.post("/life-skills/{skill_id}/experience", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def grant_life_skill_experience(skill_id: str) -> JSONResponse:
    """Grant experience to a life skill."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={
            "status": "not_implemented",
            "endpoint": f"Grant XP to life skill {skill_id}",
        },
    )
