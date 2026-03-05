"""Teams router — team management and composition endpoints."""

from http import HTTPStatus

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("/", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def list_teams() -> JSONResponse:
    """List all teams for the authenticated player."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "List all teams"},
    )


@router.post("/", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def create_team() -> JSONResponse:
    """Create a new team (up to 6 monsters)."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Create new team"},
    )


@router.put("/{team_id}", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def update_team(team_id: str) -> JSONResponse:
    """Update a team's composition."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": f"Update team {team_id}"},
    )


@router.delete("/{team_id}", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def delete_team(team_id: str) -> JSONResponse:
    """Delete a team."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": f"Delete team {team_id}"},
    )


@router.put("/{team_id}/monster/{monster_id}/role", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def set_monster_role(team_id: str, monster_id: str) -> JSONResponse:
    """Assign a role to a monster within a team."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={
            "status": "not_implemented",
            "endpoint": f"Set role for monster {monster_id} in team {team_id}",
        },
    )
