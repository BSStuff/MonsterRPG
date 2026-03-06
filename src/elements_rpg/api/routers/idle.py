"""Idle router -- idle tracking, offline gains, and action queue management endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from elements_rpg.api.auth import get_current_user
from elements_rpg.api.schemas import SuccessResponse
from elements_rpg.db.session import get_db
from elements_rpg.economy.action_queue import ActionType  # noqa: TC001
from elements_rpg.services import idle_service
from elements_rpg.services.player_service import get_player_by_supabase_id

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/idle", tags=["Idle & Offline"])


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class RecordClearRequest(BaseModel):
    """Request body for recording an area clear."""

    area_id: str = Field(min_length=1, description="Area that was cleared")
    clear_time_seconds: float = Field(gt=0, description="Time to clear in seconds")
    monsters_defeated: int = Field(ge=1, description="Monsters defeated this clear")
    timestamp: float = Field(default=0.0, ge=0, description="Unix timestamp")


class OfflineGainsQuery(BaseModel):
    """Query parameters for offline gains calculation."""

    area_id: str = Field(min_length=1)
    hours: float = Field(gt=0, le=24)


class AddActionRequest(BaseModel):
    """Request body for adding a queue action."""

    action_id: str = Field(min_length=1, description="Unique action identifier")
    action_type: ActionType
    name: str = Field(min_length=1, max_length=100)
    duration_seconds: float = Field(gt=0)
    required_materials: dict[str, int] = Field(default_factory=dict)
    reward_xp: int = Field(default=0, ge=0)
    reward_resources: dict[str, int] = Field(default_factory=dict)


class AdvanceQueueRequest(BaseModel):
    """Request body for advancing the action queue."""

    seconds: float = Field(gt=0, description="Seconds to advance")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _resolve_player_id(
    db: AsyncSession,
    current_user: dict[str, Any],
) -> Any:
    """Resolve internal player UUID from JWT sub claim."""
    supabase_uid: str = current_user["sub"]
    player = await get_player_by_supabase_id(db, supabase_uid)
    if player is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No player profile found for this account. Register first.",
        )
    return player.id


# ---------------------------------------------------------------------------
# Idle tracker endpoints
# ---------------------------------------------------------------------------


@router.post("/record-clear")
async def record_clear(
    body: RecordClearRequest,
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, Any]]:
    """Record an area clear time for BRPM calculation."""
    player_id = await _resolve_player_id(db, current_user)
    try:
        result = await idle_service.record_clear(
            db,
            player_id,
            body.area_id,
            body.clear_time_seconds,
            body.monsters_defeated,
            body.timestamp,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return SuccessResponse(data=result)


@router.get("/tracker")
async def get_idle_tracker(
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, Any]]:
    """Get current idle tracking state and BRPM metrics."""
    player_id = await _resolve_player_id(db, current_user)
    try:
        result = await idle_service.get_tracker(db, player_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return SuccessResponse(data=result)


@router.get("/offline-gains")
async def get_offline_gains(
    area_id: str,
    hours: float,
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, Any]]:
    """Calculate pending offline gains (85% rate, 8hr cap)."""
    player_id = await _resolve_player_id(db, current_user)
    try:
        result = await idle_service.calculate_offline_gains(db, player_id, area_id, hours)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return SuccessResponse(data=result.model_dump())


# ---------------------------------------------------------------------------
# Action queue endpoints
# ---------------------------------------------------------------------------


@router.get("/action-queue")
async def get_action_queue(
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, Any]]:
    """Get current action queue state (slots, active actions)."""
    player_id = await _resolve_player_id(db, current_user)
    try:
        result = await idle_service.get_action_queue(db, player_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return SuccessResponse(data=result)


@router.post("/action-queue")
async def add_action(
    body: AddActionRequest,
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, Any]]:
    """Add an action to the queue (crafting, cooking, training)."""
    from elements_rpg.economy.action_queue import QueuedAction

    action = QueuedAction(
        action_id=body.action_id,
        action_type=body.action_type,
        name=body.name,
        duration_seconds=body.duration_seconds,
        required_materials=body.required_materials,
        reward_xp=body.reward_xp,
        reward_resources=body.reward_resources,
    )

    player_id = await _resolve_player_id(db, current_user)
    try:
        result = await idle_service.add_action(db, player_id, action)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return SuccessResponse(data=result)


@router.post("/action-queue/{action_id}/cancel")
async def cancel_action(
    action_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, Any]]:
    """Cancel a queued action."""
    player_id = await _resolve_player_id(db, current_user)
    try:
        result = await idle_service.cancel_action(db, player_id, action_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return SuccessResponse(data=result)


@router.post("/action-queue/advance")
async def advance_queue(
    body: AdvanceQueueRequest,
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, Any]]:
    """Process completed actions and return results."""
    player_id = await _resolve_player_id(db, current_user)
    try:
        result = await idle_service.advance_queue(db, player_id, body.seconds)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return SuccessResponse(data=result)


@router.post("/action-queue/expand")
async def expand_queue(
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, Any]]:
    """Purchase an additional action queue slot."""
    player_id = await _resolve_player_id(db, current_user)
    try:
        result = await idle_service.expand_queue(db, player_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return SuccessResponse(data=result)
