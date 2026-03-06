"""Integration tests for the saves router endpoints.

All external dependencies (auth, DB, services) are mocked so tests run
without any live infrastructure.
"""

from __future__ import annotations

from datetime import UTC, datetime
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

# Minimal valid SaveRequest JSON body (wraps GameSaveData in save_data field)
VALID_SAVE_BODY: dict[str, Any] = {
    "save_data": {
        "player": {
            "player_id": FAKE_PLAYER_ID,
            "username": "Hero",
        },
    },
    "expected_version": None,
}


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
    """Create a fake player with a deterministic UUID."""
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
# 1. POST /saves -- save game state
# ===================================================================


class TestCreateSave:
    """POST /saves."""

    @pytest.mark.asyncio
    async def test_save_success(self, client: AsyncClient) -> None:
        """Saving game state should return version and timestamp."""
        fake_db_state = MagicMock()
        fake_db_state.version = 2
        fake_db_state.updated_at = datetime(2026, 3, 5, 12, 0, 0, tzinfo=UTC)

        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.saves.save_game_state",
                new_callable=AsyncMock,
                return_value=fake_db_state,
            ),
        ):
            response = await client.post("/saves/", json=VALID_SAVE_BODY)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["version"] == 2
        assert "2026-03-05" in body["timestamp"]

    @pytest.mark.asyncio
    async def test_save_no_auth(self, app, test_settings: Settings) -> None:
        """Should return 401/403 without auth token."""
        app.dependency_overrides.pop(get_current_user, None)
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as unauthed:
            response = await unauthed.post("/saves/", json=VALID_SAVE_BODY)
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_save_player_not_found(self, client: AsyncClient) -> None:
        """Should return 404 if player profile not found."""
        with patch(
            "elements_rpg.api.dependencies.get_player_by_supabase_id",
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = await client.post("/saves/", json=VALID_SAVE_BODY)
        assert response.status_code == 404


# ===================================================================
# 2. GET /saves -- load game state
# ===================================================================


class TestLoadSave:
    """GET /saves."""

    @pytest.mark.asyncio
    async def test_load_success(self, client: AsyncClient) -> None:
        """Loading game state should return data in SuccessResponse envelope."""
        fake_game_data = MagicMock()
        fake_game_data.model_dump.return_value = {
            "save_version": 1,
            "player_id": FAKE_PLAYER_ID,
            "player_name": "Hero",
        }

        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.saves.load_game_state",
                new_callable=AsyncMock,
                return_value=fake_game_data,
            ),
        ):
            response = await client.get("/saves/")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["player_name"] == "Hero"

    @pytest.mark.asyncio
    async def test_load_no_save_returns_404(self, client: AsyncClient) -> None:
        """Should return 404 when no save exists."""
        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.saves.load_game_state",
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            response = await client.get("/saves/")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_load_no_auth(self, app, test_settings: Settings) -> None:
        """Should return 401/403 without auth token."""
        app.dependency_overrides.pop(get_current_user, None)
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as unauthed:
            response = await unauthed.get("/saves/")
        assert response.status_code in (401, 403)


# ===================================================================
# 3. POST /saves/new -- create fresh save
# ===================================================================


class TestCreateNewSave:
    """POST /saves/new."""

    @pytest.mark.asyncio
    async def test_create_new_save_success(self, client: AsyncClient) -> None:
        """Should create a fresh save and return 201."""
        fake_game_data = MagicMock()
        fake_game_data.model_dump.return_value = {
            "save_version": 1,
            "player_id": FAKE_PLAYER_ID,
            "player_name": "hero@example.com",
        }

        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.saves.create_fresh_save",
                new_callable=AsyncMock,
                return_value=fake_game_data,
            ),
        ):
            response = await client.post("/saves/new")

        assert response.status_code == 201
        body = response.json()
        assert body["success"] is True
        assert body["data"]["player_name"] == "hero@example.com"

    @pytest.mark.asyncio
    async def test_create_new_save_conflict_409(self, client: AsyncClient) -> None:
        """Should return 409 if save already exists."""
        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.saves.create_fresh_save",
                new_callable=AsyncMock,
                side_effect=ValueError("Player already has a save"),
            ),
        ):
            response = await client.post("/saves/new")

        assert response.status_code == 409
        body = response.json()
        assert "already has a save" in body["detail"]


# ===================================================================
# 4. GET /saves/version -- save version metadata
# ===================================================================


class TestGetSaveVersion:
    """GET /saves/version."""

    @pytest.mark.asyncio
    async def test_version_exists(self, client: AsyncClient) -> None:
        """Should return version info when save exists."""
        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.saves.get_save_version",
                new_callable=AsyncMock,
                return_value={
                    "version": 5,
                    "updated_at": "2026-03-05T12:00:00+00:00",
                    "exists": True,
                },
            ),
        ):
            response = await client.get("/saves/version")

        assert response.status_code == 200
        body = response.json()
        assert body["version"] == 5
        assert body["exists"] is True
        assert body["updated_at"] is not None

    @pytest.mark.asyncio
    async def test_version_no_save(self, client: AsyncClient) -> None:
        """Should return version 0 and exists=False when no save."""
        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.saves.get_save_version",
                new_callable=AsyncMock,
                return_value={
                    "version": 0,
                    "updated_at": None,
                    "exists": False,
                },
            ),
        ):
            response = await client.get("/saves/version")

        assert response.status_code == 200
        body = response.json()
        assert body["version"] == 0
        assert body["exists"] is False
