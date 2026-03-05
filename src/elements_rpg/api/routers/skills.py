"""Skills router — skill catalog, progression, and strategy management endpoints."""

from http import HTTPStatus

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/skills", tags=["Skills & Strategy"])


@router.get("/catalog", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def get_skill_catalog() -> JSONResponse:
    """List all available skills in the catalog."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "List all skills in catalog"},
    )


@router.get("/{skill_id}", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def get_skill(skill_id: str) -> JSONResponse:
    """Get details of a specific skill including level and milestone."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": f"Get skill {skill_id} details"},
    )


@router.post("/{skill_id}/experience", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def grant_skill_experience(skill_id: str) -> JSONResponse:
    """Grant experience to a skill from usage."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": f"Grant XP to skill {skill_id}"},
    )


@router.get("/strategies", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def list_strategies() -> JSONResponse:
    """List all strategy profiles and proficiency levels."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "List strategy profiles"},
    )


@router.post("/strategies/{strategy}/experience", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def grant_strategy_experience(strategy: str) -> JSONResponse:
    """Grant experience to a strategy profile."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={
            "status": "not_implemented",
            "endpoint": f"Grant XP to strategy {strategy}",
        },
    )
