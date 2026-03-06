"""Integration tests for the combat router endpoints.

All external dependencies (auth, DB) are mocked.  Combat service uses
in-memory sessions which are cleared between tests.
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
from elements_rpg.services.combat_service import clear_all_sessions

VALID_JWT_PAYLOAD: dict[str, Any] = {
    "sub": "test-player-uuid-123",
    "email": "hero@example.com",
    "role": "authenticated",
    "aud": "authenticated",
    "exp": 9999999999,
}

MOCK_OWNED_MONSTERS_PATCH = "elements_rpg.api.routers.combat.monster_service.get_owned_monsters"
MOCK_RESOLVE_PLAYER_PATCH = "elements_rpg.api.dependencies.get_player_by_supabase_id"
MOCK_EARN_GOLD_PATCH = "elements_rpg.api.routers.combat.earn_gold"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def test_settings() -> Settings:
    """Settings instance with deterministic test values."""
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


def _mock_db_session():
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    return session


def _mock_player() -> MagicMock:
    import uuid

    player = MagicMock()
    player.id = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    return player


@pytest.fixture
def app(test_settings: Settings):
    """Create a FastAPI app with overridden auth and DB dependency."""
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


@pytest.fixture(autouse=True)
def _cleanup():
    """Clear all combat sessions between tests."""
    clear_all_sessions()
    yield
    clear_all_sessions()


# ===================================================================
# 1. POST /combat/start
# ===================================================================


class TestStartCombat:
    """Tests for POST /combat/start."""

    @pytest.mark.asyncio
    async def test_start_combat_success(self, client: AsyncClient) -> None:
        """Valid request should create a combat session."""
        with (
            patch(MOCK_RESOLVE_PLAYER_PATCH, new_callable=AsyncMock, return_value=_mock_player()),
            patch(MOCK_OWNED_MONSTERS_PATCH, new_callable=AsyncMock, return_value=[]),
        ):
            response = await client.post(
                "/combat/start",
                json={"enemy_species_ids": ["species_leaflet"]},
            )
        assert response.status_code == 201
        body = response.json()
        assert body["success"] is True
        assert "session_id" in body["data"]
        assert body["data"]["state"]["round"] == 0
        assert body["data"]["state"]["is_finished"] is False

    @pytest.mark.asyncio
    async def test_start_combat_with_multiple_enemies(self, client: AsyncClient) -> None:
        """Should support multiple enemy species."""
        with (
            patch(MOCK_RESOLVE_PLAYER_PATCH, new_callable=AsyncMock, return_value=_mock_player()),
            patch(MOCK_OWNED_MONSTERS_PATCH, new_callable=AsyncMock, return_value=[]),
        ):
            response = await client.post(
                "/combat/start",
                json={
                    "enemy_species_ids": ["species_leaflet", "species_ember_pup"],
                    "enemy_level": 10,
                },
            )
        assert response.status_code == 201
        body = response.json()
        assert len(body["data"]["state"]["enemy_team"]) == 2

    @pytest.mark.asyncio
    async def test_start_combat_invalid_species(self, client: AsyncClient) -> None:
        """Should return 400 for unknown species IDs."""
        with (
            patch(MOCK_RESOLVE_PLAYER_PATCH, new_callable=AsyncMock, return_value=_mock_player()),
            patch(MOCK_OWNED_MONSTERS_PATCH, new_callable=AsyncMock, return_value=[]),
        ):
            response = await client.post(
                "/combat/start",
                json={"enemy_species_ids": ["nonexistent_species"]},
            )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_start_combat_empty_enemies(self, client: AsyncClient) -> None:
        """Should return 422 for empty enemy list."""
        response = await client.post(
            "/combat/start",
            json={"enemy_species_ids": []},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_start_combat_no_auth(self, app, test_settings: Settings) -> None:
        """Should return 401/403 without auth token."""
        # Remove auth override
        app.dependency_overrides.pop(get_current_user, None)
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as unauthed_client:
            response = await unauthed_client.post(
                "/combat/start",
                json={"enemy_species_ids": ["species_leaflet"]},
            )
        assert response.status_code in (401, 403)


# ===================================================================
# 2. POST /combat/{session_id}/round
# ===================================================================


class TestProcessRound:
    """Tests for POST /combat/{session_id}/round."""

    @pytest.mark.asyncio
    async def test_process_round_success(self, client: AsyncClient) -> None:
        """Should execute a round and return results."""
        with (
            patch(MOCK_RESOLVE_PLAYER_PATCH, new_callable=AsyncMock, return_value=_mock_player()),
            patch(MOCK_OWNED_MONSTERS_PATCH, new_callable=AsyncMock, return_value=[]),
        ):
            start_resp = await client.post(
                "/combat/start",
                json={"enemy_species_ids": ["species_leaflet"]},
            )
        session_id = start_resp.json()["data"]["session_id"]

        response = await client.post(f"/combat/{session_id}/round")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["state"]["round"] == 1
        assert "round_result" in body["data"]
        assert body["data"]["round_result"]["round_number"] == 1

    @pytest.mark.asyncio
    async def test_process_round_not_found(self, client: AsyncClient) -> None:
        """Should return 404 for unknown session."""
        response = await client.post("/combat/nonexistent-id/round")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_process_round_finished_combat(self, client: AsyncClient) -> None:
        """Should return 409 when combat is already over."""
        with (
            patch(MOCK_RESOLVE_PLAYER_PATCH, new_callable=AsyncMock, return_value=_mock_player()),
            patch(MOCK_OWNED_MONSTERS_PATCH, new_callable=AsyncMock, return_value=[]),
        ):
            start_resp = await client.post(
                "/combat/start",
                json={
                    "enemy_species_ids": ["species_leaflet"],
                    "enemy_level": 1,
                },
            )
        session_id = start_resp.json()["data"]["session_id"]

        # Run rounds until combat finishes
        for _ in range(100):
            resp = await client.post(f"/combat/{session_id}/round")
            if resp.json()["data"]["state"]["is_finished"]:
                break

        # Next round should return 409
        response = await client.post(f"/combat/{session_id}/round")
        assert response.status_code == 409


# ===================================================================
# 3. POST /combat/{session_id}/finish
# ===================================================================


class TestFinishCombat:
    """Tests for POST /combat/{session_id}/finish."""

    @pytest.mark.asyncio
    async def test_finish_combat_success(self, client: AsyncClient) -> None:
        """Should end combat and return final results with rewards."""
        with (
            patch(MOCK_RESOLVE_PLAYER_PATCH, new_callable=AsyncMock, return_value=_mock_player()),
            patch(MOCK_OWNED_MONSTERS_PATCH, new_callable=AsyncMock, return_value=[]),
        ):
            start_resp = await client.post(
                "/combat/start",
                json={"enemy_species_ids": ["species_leaflet"]},
            )
        session_id = start_resp.json()["data"]["session_id"]

        # Execute a round
        await client.post(f"/combat/{session_id}/round")

        with (
            patch(MOCK_RESOLVE_PLAYER_PATCH, new_callable=AsyncMock, return_value=_mock_player()),
            patch(MOCK_EARN_GOLD_PATCH, new_callable=AsyncMock),
        ):
            response = await client.post(f"/combat/{session_id}/finish")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert "finished" in body["data"]
        assert "rounds" in body["data"]
        assert "log" in body["data"]
        assert "rewards" in body["data"]
        assert body["data"]["rounds"] == 1

    @pytest.mark.asyncio
    async def test_finish_combat_not_found(self, client: AsyncClient) -> None:
        """Should return 404 for unknown session."""
        response = await client.post("/combat/nonexistent-id/finish")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_finish_combat_double_finish(self, client: AsyncClient) -> None:
        """Should return 404 when finishing same session twice."""
        with (
            patch(MOCK_RESOLVE_PLAYER_PATCH, new_callable=AsyncMock, return_value=_mock_player()),
            patch(MOCK_OWNED_MONSTERS_PATCH, new_callable=AsyncMock, return_value=[]),
        ):
            start_resp = await client.post(
                "/combat/start",
                json={"enemy_species_ids": ["species_leaflet"]},
            )
        session_id = start_resp.json()["data"]["session_id"]

        with (
            patch(MOCK_RESOLVE_PLAYER_PATCH, new_callable=AsyncMock, return_value=_mock_player()),
            patch(MOCK_EARN_GOLD_PATCH, new_callable=AsyncMock),
        ):
            await client.post(f"/combat/{session_id}/finish")
        response = await client.post(f"/combat/{session_id}/finish")
        assert response.status_code == 404


# ===================================================================
# 4. GET /combat/{session_id}
# ===================================================================


class TestGetCombatSession:
    """Tests for GET /combat/{session_id}."""

    @pytest.mark.asyncio
    async def test_get_session_success(self, client: AsyncClient) -> None:
        """Should return current combat state."""
        with (
            patch(MOCK_RESOLVE_PLAYER_PATCH, new_callable=AsyncMock, return_value=_mock_player()),
            patch(MOCK_OWNED_MONSTERS_PATCH, new_callable=AsyncMock, return_value=[]),
        ):
            start_resp = await client.post(
                "/combat/start",
                json={"enemy_species_ids": ["species_leaflet"]},
            )
        session_id = start_resp.json()["data"]["session_id"]

        response = await client.get(f"/combat/{session_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["session_id"] == session_id
        assert body["data"]["round"] == 0

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, client: AsyncClient) -> None:
        """Should return 404 for unknown session."""
        response = await client.get("/combat/nonexistent-id")
        assert response.status_code == 404


# ===================================================================
# 5. GET /combat/{session_id}/log
# ===================================================================


class TestGetCombatLog:
    """Tests for GET /combat/{session_id}/log."""

    @pytest.mark.asyncio
    async def test_get_log_empty(self, client: AsyncClient) -> None:
        """Log should be empty before any rounds."""
        with (
            patch(MOCK_RESOLVE_PLAYER_PATCH, new_callable=AsyncMock, return_value=_mock_player()),
            patch(MOCK_OWNED_MONSTERS_PATCH, new_callable=AsyncMock, return_value=[]),
        ):
            start_resp = await client.post(
                "/combat/start",
                json={"enemy_species_ids": ["species_leaflet"]},
            )
        session_id = start_resp.json()["data"]["session_id"]

        response = await client.get(f"/combat/{session_id}/log")
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["log"] == []
        assert body["data"]["rounds"] == 0

    @pytest.mark.asyncio
    async def test_get_log_after_round(self, client: AsyncClient) -> None:
        """Log should contain entries after rounds."""
        with (
            patch(MOCK_RESOLVE_PLAYER_PATCH, new_callable=AsyncMock, return_value=_mock_player()),
            patch(MOCK_OWNED_MONSTERS_PATCH, new_callable=AsyncMock, return_value=[]),
        ):
            start_resp = await client.post(
                "/combat/start",
                json={
                    "enemy_species_ids": ["species_leaflet", "species_ember_pup"],
                    "enemy_level": 50,
                },
            )
        session_id = start_resp.json()["data"]["session_id"]

        await client.post(f"/combat/{session_id}/round")
        await client.post(f"/combat/{session_id}/round")

        response = await client.get(f"/combat/{session_id}/log")
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["rounds"] == 2
        assert len(body["data"]["log"]) == 2

    @pytest.mark.asyncio
    async def test_get_log_not_found(self, client: AsyncClient) -> None:
        """Should return 404 for unknown session."""
        response = await client.get("/combat/nonexistent-id/log")
        assert response.status_code == 404
