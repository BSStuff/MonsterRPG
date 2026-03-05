"""Monsters router — bestiary, owned monsters, and monster management endpoints."""

from http import HTTPStatus

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/monsters", tags=["Monsters"])


@router.get("/bestiary", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def get_bestiary() -> JSONResponse:
    """List all available monster species from the bestiary."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "List all monster species"},
    )


@router.get("/owned", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def get_owned_monsters() -> JSONResponse:
    """List all monsters owned by the authenticated player."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "List owned monsters"},
    )


@router.get("/{monster_id}", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def get_monster(monster_id: str) -> JSONResponse:
    """Get details of a specific owned monster."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": f"Get monster {monster_id}"},
    )


@router.post("/{monster_id}/experience", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def grant_experience(monster_id: str) -> JSONResponse:
    """Grant experience points to a monster."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": f"Grant XP to monster {monster_id}"},
    )


@router.post("/{monster_id}/bond", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def increase_bond(monster_id: str) -> JSONResponse:
    """Increase the bond level of a monster."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={
            "status": "not_implemented",
            "endpoint": f"Increase bond for monster {monster_id}",
        },
    )


@router.post("/{monster_id}/skill/equip", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def equip_skill(monster_id: str) -> JSONResponse:
    """Equip a skill to a monster (max 4 skills)."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": f"Equip skill on monster {monster_id}"},
    )


@router.post("/{monster_id}/skill/unequip", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def unequip_skill(monster_id: str) -> JSONResponse:
    """Unequip a skill from a monster."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={
            "status": "not_implemented",
            "endpoint": f"Unequip skill from monster {monster_id}",
        },
    )
