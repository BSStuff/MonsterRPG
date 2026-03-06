"""Integration tests for the taming router endpoints.

All endpoints require authentication. DB, service, and player lookups are mocked.
"""

from __future__ import annotations

import uuid
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
# 1. POST /taming/calculate -- chance calculation
# ===================================================================


class TestCalculateChance:
    """POST /taming/calculate."""

    @pytest.mark.asyncio
    async def test_calculate_success(self, client: AsyncClient) -> None:
        """Should return breakdown of taming chance."""
        result = {
            "species_id": "species_leaflet",
            "base_rate": 0.30,
            "food_bonus": 0.05,
            "skill_bonus": 0.0,
            "pity_bonus": 0.02,
            "attempts": 2,
            "final_chance": 0.37,
        }

        with (
            patch(
                "elements_rpg.api.routers.taming.player_service.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.taming.taming_service.calculate_chance",
                new_callable=AsyncMock,
                return_value=result,
            ),
        ):
            response = await client.post(
                "/taming/calculate",
                json={
                    "species_id": "species_leaflet",
                    "food_bonus": 0.05,
                },
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["base_rate"] == 0.30
        assert body["data"]["final_chance"] == 0.37
        assert body["data"]["attempts"] == 2

    @pytest.mark.asyncio
    async def test_calculate_invalid_species_returns_400(self, client: AsyncClient) -> None:
        """Should return 400 for unknown species."""
        with (
            patch(
                "elements_rpg.api.routers.taming.player_service.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.taming.taming_service.calculate_chance",
                new_callable=AsyncMock,
                side_effect=ValueError("Unknown species: 'bad_id'"),
            ),
        ):
            response = await client.post(
                "/taming/calculate",
                json={"species_id": "bad_id"},
            )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_calculate_no_save_returns_400(self, client: AsyncClient) -> None:
        """Should return 400 when player has no game save."""
        with (
            patch(
                "elements_rpg.api.routers.taming.player_service.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.taming.taming_service.calculate_chance",
                new_callable=AsyncMock,
                side_effect=ValueError("No game save found"),
            ),
        ):
            response = await client.post(
                "/taming/calculate",
                json={"species_id": "species_leaflet"},
            )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_calculate_empty_species_returns_422(self, client: AsyncClient) -> None:
        """Should return 422 for empty species_id (Pydantic min_length=1)."""
        response = await client.post(
            "/taming/calculate",
            json={"species_id": ""},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_calculate_food_bonus_out_of_range_returns_422(self, client: AsyncClient) -> None:
        """Should return 422 when food_bonus exceeds 1.0."""
        response = await client.post(
            "/taming/calculate",
            json={"species_id": "species_leaflet", "food_bonus": 1.5},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_calculate_no_auth(self, app, test_settings: Settings) -> None:
        """Should return 401/403 without auth."""
        app.dependency_overrides.pop(get_current_user, None)
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as unauthed:
            response = await unauthed.post(
                "/taming/calculate",
                json={"species_id": "species_leaflet"},
            )
        assert response.status_code in (401, 403)


# ===================================================================
# 2. POST /taming/attempt -- taming attempt
# ===================================================================


class TestAttemptTaming:
    """POST /taming/attempt."""

    @pytest.mark.asyncio
    async def test_attempt_success_caught(self, client: AsyncClient) -> None:
        """Should return success=True and monster data when caught."""
        result = {
            "success": True,
            "attempt_number": 3,
            "base_rate": 0.30,
            "food_bonus": 0.0,
            "skill_bonus": 0.0,
            "pity_bonus": 0.06,
            "final_chance": 0.36,
            "monster": {
                "monster_id": str(uuid.uuid4()),
                "species_id": "species_leaflet",
                "name": "Leaflet",
                "level": 1,
                "species": {
                    "name": "Leaflet",
                    "element": "nature",
                    "rarity": "common",
                },
            },
        }

        with (
            patch(
                "elements_rpg.api.routers.taming.player_service.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.taming.taming_service.attempt_tame_monster",
                new_callable=AsyncMock,
                return_value=result,
            ),
        ):
            response = await client.post(
                "/taming/attempt",
                json={"species_id": "species_leaflet"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["success"] is True
        assert body["data"]["monster"] is not None
        assert body["data"]["monster"]["name"] == "Leaflet"

    @pytest.mark.asyncio
    async def test_attempt_failed(self, client: AsyncClient) -> None:
        """Should return success=False and monster=None when taming fails."""
        result = {
            "success": False,
            "attempt_number": 1,
            "base_rate": 0.10,
            "food_bonus": 0.0,
            "skill_bonus": 0.0,
            "pity_bonus": 0.0,
            "final_chance": 0.10,
            "monster": None,
        }

        with (
            patch(
                "elements_rpg.api.routers.taming.player_service.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.taming.taming_service.attempt_tame_monster",
                new_callable=AsyncMock,
                return_value=result,
            ),
        ):
            response = await client.post(
                "/taming/attempt",
                json={"species_id": "species_ember_pup"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["success"] is False
        assert body["data"]["monster"] is None

    @pytest.mark.asyncio
    async def test_attempt_invalid_species_returns_400(self, client: AsyncClient) -> None:
        """Should return 400 for unknown species."""
        with (
            patch(
                "elements_rpg.api.routers.taming.player_service.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.taming.taming_service.attempt_tame_monster",
                new_callable=AsyncMock,
                side_effect=ValueError("Unknown species"),
            ),
        ):
            response = await client.post(
                "/taming/attempt",
                json={"species_id": "fake_species"},
            )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_attempt_with_bonuses(self, client: AsyncClient) -> None:
        """Should accept food_bonus and skill_bonus parameters."""
        result = {
            "success": False,
            "attempt_number": 1,
            "base_rate": 0.30,
            "food_bonus": 0.10,
            "skill_bonus": 0.05,
            "pity_bonus": 0.0,
            "final_chance": 0.45,
            "monster": None,
        }

        with (
            patch(
                "elements_rpg.api.routers.taming.player_service.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.taming.taming_service.attempt_tame_monster",
                new_callable=AsyncMock,
                return_value=result,
            ),
        ):
            response = await client.post(
                "/taming/attempt",
                json={
                    "species_id": "species_leaflet",
                    "food_bonus": 0.10,
                    "skill_bonus": 0.05,
                },
            )

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["food_bonus"] == 0.10
        assert body["data"]["skill_bonus"] == 0.05


# ===================================================================
# 3. GET /taming/tracker -- pity state
# ===================================================================


class TestGetTracker:
    """GET /taming/tracker."""

    @pytest.mark.asyncio
    async def test_tracker_success(self, client: AsyncClient) -> None:
        """Should return pity state per species."""
        result = {
            "species_leaflet": {"attempts": 3, "pity_bonus": 0.06},
            "species_ember_pup": {"attempts": 0, "pity_bonus": 0.0},
        }

        with (
            patch(
                "elements_rpg.api.routers.taming.player_service.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.taming.taming_service.get_tracker",
                new_callable=AsyncMock,
                return_value=result,
            ),
        ):
            response = await client.get("/taming/tracker")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["species_leaflet"]["attempts"] == 3
        assert body["data"]["species_ember_pup"]["pity_bonus"] == 0.0

    @pytest.mark.asyncio
    async def test_tracker_empty(self, client: AsyncClient) -> None:
        """Should return empty dict when no taming attempts."""
        with (
            patch(
                "elements_rpg.api.routers.taming.player_service.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.taming.taming_service.get_tracker",
                new_callable=AsyncMock,
                return_value={},
            ),
        ):
            response = await client.get("/taming/tracker")

        assert response.status_code == 200
        assert response.json()["data"] == {}

    @pytest.mark.asyncio
    async def test_tracker_no_save_returns_400(self, client: AsyncClient) -> None:
        """Should return 400 when no game save exists."""
        with (
            patch(
                "elements_rpg.api.routers.taming.player_service.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.taming.taming_service.get_tracker",
                new_callable=AsyncMock,
                side_effect=ValueError("No game save found"),
            ),
        ):
            response = await client.get("/taming/tracker")

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_tracker_no_auth(self, app, test_settings: Settings) -> None:
        """Should return 401/403 without auth."""
        app.dependency_overrides.pop(get_current_user, None)
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as unauthed:
            response = await unauthed.get("/taming/tracker")
        assert response.status_code in (401, 403)
