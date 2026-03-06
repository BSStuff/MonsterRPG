"""Integration tests for idle router -- idle tracking, offline gains, action queue.

All external dependencies (auth, DB, services) are mocked so tests run
without any live infrastructure.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from elements_rpg.api.auth import get_current_user
from elements_rpg.api.config import Settings, get_settings
from elements_rpg.db.session import get_db

VALID_JWT_PAYLOAD: dict[str, Any] = {
    "sub": "test-player-uuid-123",
    "email": "hero@example.com",
    "role": "authenticated",
    "aud": "authenticated",
    "exp": 9999999999,
}

FAKE_PLAYER_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        supabase_url="https://test.supabase.co",
        supabase_key="test-anon-key",
        supabase_jwt_secret="test-jwt-secret",
        supabase_service_key="test-service-key",
        database_url="sqlite+aiosqlite:///:memory:",
        debug=True,
    )


def _create_app():
    from elements_rpg.api.app import create_app as _create

    return _create()


def _mock_db_session() -> AsyncMock:
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    return session


def _mock_player() -> MagicMock:
    import uuid

    player = MagicMock()
    player.id = uuid.UUID(FAKE_PLAYER_ID)
    return player


@pytest.fixture
def app(test_settings: Settings):
    with patch("elements_rpg.api.app.get_settings", return_value=test_settings):
        application = _create_app()
    application.dependency_overrides[get_settings] = lambda: test_settings
    application.dependency_overrides[get_current_user] = lambda: VALID_JWT_PAYLOAD

    mock_db = _mock_db_session()

    async def _fake_db():
        yield mock_db

    application.dependency_overrides[get_db] = _fake_db
    return application


@pytest_asyncio.fixture
async def client(app) -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ===================================================================
# 1. POST /idle/record-clear
# ===================================================================


class TestRecordClear:
    """POST /idle/record-clear."""

    @pytest.mark.asyncio
    async def test_record_clear_success(self, client: AsyncClient) -> None:
        """Should record a clear and return BRPM data."""
        mock_result = {
            "area_id": "forest",
            "is_new_best": True,
            "brpm": 2.0,
            "idle_rate": 1.7,
            "best_clear_time": 30.0,
        }
        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.services.idle_service.record_clear",
                new_callable=AsyncMock,
                return_value=mock_result,
            ),
        ):
            response = await client.post(
                "/idle/record-clear",
                json={
                    "area_id": "forest",
                    "clear_time_seconds": 30.0,
                    "monsters_defeated": 5,
                },
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["is_new_best"] is True
        assert body["data"]["brpm"] == 2.0

    @pytest.mark.asyncio
    async def test_record_clear_no_auth(self, app, test_settings: Settings) -> None:
        """Should return 401/403 without auth."""
        app.dependency_overrides.pop(get_current_user, None)
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as unauthed:
            response = await unauthed.post(
                "/idle/record-clear",
                json={"area_id": "forest", "clear_time_seconds": 30.0, "monsters_defeated": 5},
            )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_record_clear_invalid_body(self, client: AsyncClient) -> None:
        """Should return 422 with invalid body."""
        with patch(
            "elements_rpg.api.dependencies.get_player_by_supabase_id",
            new_callable=AsyncMock,
            return_value=_mock_player(),
        ):
            response = await client.post(
                "/idle/record-clear",
                json={"area_id": "", "clear_time_seconds": -1, "monsters_defeated": 0},
            )
        assert response.status_code == 422


# ===================================================================
# 2. GET /idle/tracker
# ===================================================================


class TestGetTracker:
    """GET /idle/tracker."""

    @pytest.mark.asyncio
    async def test_get_tracker_success(self, client: AsyncClient) -> None:
        """Should return tracker data."""
        mock_result = {"areas": {"forest": {"brpm": 2.0, "idle_rate": 1.7}}}
        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.services.idle_service.get_tracker",
                new_callable=AsyncMock,
                return_value=mock_result,
            ),
        ):
            response = await client.get("/idle/tracker")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert "forest" in body["data"]["areas"]


# ===================================================================
# 3. GET /idle/offline-gains
# ===================================================================


class TestOfflineGains:
    """GET /idle/offline-gains."""

    @pytest.mark.asyncio
    async def test_offline_gains_success(self, client: AsyncClient) -> None:
        """Should return offline gains data."""
        from elements_rpg.idle.offline_gains import OfflineGainsResult

        mock_result = OfflineGainsResult(
            area_id="forest",
            offline_duration_hours=4.0,
            capped_duration_hours=4.0,
            idle_rate=1.7,
            total_rounds=408,
            estimated_monsters_defeated=2040,
            estimated_xp=20400,
            estimated_gold=10200,
            was_capped=False,
        )
        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.services.idle_service.calculate_offline_gains",
                new_callable=AsyncMock,
                return_value=mock_result,
            ),
        ):
            response = await client.get(
                "/idle/offline-gains", params={"area_id": "forest", "hours": 4.0}
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["total_rounds"] == 408
        assert body["data"]["was_capped"] is False

    @pytest.mark.asyncio
    async def test_offline_gains_player_not_found(self, client: AsyncClient) -> None:
        """Should return 404 if player not found."""
        with patch(
            "elements_rpg.api.dependencies.get_player_by_supabase_id",
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = await client.get(
                "/idle/offline-gains", params={"area_id": "forest", "hours": 4.0}
            )
        assert response.status_code == 404


# ===================================================================
# 4. GET /idle/action-queue
# ===================================================================


class TestGetActionQueue:
    """GET /idle/action-queue."""

    @pytest.mark.asyncio
    async def test_get_queue_success(self, client: AsyncClient) -> None:
        """Should return queue state."""
        mock_result = {
            "max_slots": 2,
            "active_count": 0,
            "has_free_slot": True,
            "actions": [],
        }
        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.services.idle_service.get_action_queue",
                new_callable=AsyncMock,
                return_value=mock_result,
            ),
        ):
            response = await client.get("/idle/action-queue")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["max_slots"] == 2


# ===================================================================
# 5. POST /idle/action-queue -- add action
# ===================================================================


class TestAddAction:
    """POST /idle/action-queue."""

    @pytest.mark.asyncio
    async def test_add_action_success(self, client: AsyncClient) -> None:
        """Should add an action and return updated queue."""
        mock_result = {
            "added": True,
            "action": {"action_id": "craft-1", "name": "Craft Potion"},
            "max_slots": 2,
            "active_count": 1,
        }
        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.services.idle_service.add_action",
                new_callable=AsyncMock,
                return_value=mock_result,
            ),
        ):
            response = await client.post(
                "/idle/action-queue",
                json={
                    "action_id": "craft-1",
                    "action_type": "craft",
                    "name": "Craft Potion",
                    "duration_seconds": 60.0,
                },
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["added"] is True

    @pytest.mark.asyncio
    async def test_add_action_queue_full(self, client: AsyncClient) -> None:
        """Should return 400 when queue is full."""
        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.services.idle_service.add_action",
                new_callable=AsyncMock,
                side_effect=ValueError("Action queue is full"),
            ),
        ):
            response = await client.post(
                "/idle/action-queue",
                json={
                    "action_id": "craft-1",
                    "action_type": "craft",
                    "name": "Craft Potion",
                    "duration_seconds": 60.0,
                },
            )
        assert response.status_code == 400


# ===================================================================
# 6. POST /idle/action-queue/{action_id}/cancel
# ===================================================================


class TestCancelAction:
    """POST /idle/action-queue/{action_id}/cancel."""

    @pytest.mark.asyncio
    async def test_cancel_action_success(self, client: AsyncClient) -> None:
        """Should cancel the action."""
        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.services.idle_service.cancel_action",
                new_callable=AsyncMock,
                return_value={"cancelled": True, "action_id": "craft-1"},
            ),
        ):
            response = await client.post("/idle/action-queue/craft-1/cancel")

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["cancelled"] is True

    @pytest.mark.asyncio
    async def test_cancel_action_not_found(self, client: AsyncClient) -> None:
        """Should return 404 when action not found."""
        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.services.idle_service.cancel_action",
                new_callable=AsyncMock,
                side_effect=ValueError("Action not found"),
            ),
        ):
            response = await client.post("/idle/action-queue/nonexistent/cancel")
        assert response.status_code == 404


# ===================================================================
# 7. POST /idle/action-queue/advance
# ===================================================================


class TestAdvanceQueue:
    """POST /idle/action-queue/advance."""

    @pytest.mark.asyncio
    async def test_advance_success(self, client: AsyncClient) -> None:
        """Should advance queue and return completed actions."""
        mock_result = {
            "advanced_seconds": 30.0,
            "completed_actions": [],
            "completed_count": 0,
            "active_count": 1,
        }
        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.services.idle_service.advance_queue",
                new_callable=AsyncMock,
                return_value=mock_result,
            ),
        ):
            response = await client.post("/idle/action-queue/advance", json={"seconds": 30.0})

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["advanced_seconds"] == 30.0


# ===================================================================
# 8. POST /idle/action-queue/expand
# ===================================================================


class TestExpandQueue:
    """POST /idle/action-queue/expand."""

    @pytest.mark.asyncio
    async def test_expand_success(self, client: AsyncClient) -> None:
        """Should expand queue and return new slot count."""
        mock_result = {"previous_slots": 2, "new_slots": 3}
        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.services.idle_service.expand_queue",
                new_callable=AsyncMock,
                return_value=mock_result,
            ),
        ):
            response = await client.post("/idle/action-queue/expand")

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["new_slots"] == 3

    @pytest.mark.asyncio
    async def test_expand_at_max(self, client: AsyncClient) -> None:
        """Should return 400 when at max capacity."""
        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.services.idle_service.expand_queue",
                new_callable=AsyncMock,
                side_effect=ValueError("Already at max capacity"),
            ),
        ):
            response = await client.post("/idle/action-queue/expand")
        assert response.status_code == 400
