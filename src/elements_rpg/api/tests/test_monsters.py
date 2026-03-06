"""Integration tests for the monsters router endpoints.

Bestiary endpoints are public (no auth). Owned monster endpoints require auth.
All DB and service calls are mocked.

Note: XP and bond endpoints have been removed (server-authoritative economy).
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
FAKE_MONSTER_ID = str(uuid.uuid4())


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
# 1. GET /monsters/bestiary -- public, no auth
# ===================================================================


class TestGetBestiary:
    """GET /monsters/bestiary (public)."""

    @pytest.mark.asyncio
    async def test_bestiary_returns_species_list(self, client: AsyncClient) -> None:
        """Should return a list of all species."""
        fake_species = MagicMock()
        fake_species.model_dump.return_value = {
            "species_id": "species_leaflet",
            "name": "Leaflet",
        }

        with patch(
            "elements_rpg.api.routers.monsters.monster_service.get_bestiary",
            new_callable=AsyncMock,
            return_value=[fake_species],
        ):
            response = await client.get("/monsters/bestiary")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)
        assert len(body["data"]) == 1
        assert body["data"][0]["name"] == "Leaflet"

    @pytest.mark.asyncio
    async def test_bestiary_no_auth_required(self, app, test_settings: Settings) -> None:
        """Bestiary should work even without auth."""
        app.dependency_overrides.pop(get_current_user, None)

        fake_species = MagicMock()
        fake_species.model_dump.return_value = {"species_id": "s1", "name": "S1"}

        with patch(
            "elements_rpg.api.routers.monsters.monster_service.get_bestiary",
            new_callable=AsyncMock,
            return_value=[fake_species],
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as unauthed:
                response = await unauthed.get("/monsters/bestiary")
        assert response.status_code == 200


# ===================================================================
# 2. GET /monsters/bestiary/{species_id}
# ===================================================================


class TestGetSpecies:
    """GET /monsters/bestiary/{species_id} (public)."""

    @pytest.mark.asyncio
    async def test_species_found(self, client: AsyncClient) -> None:
        """Should return species details for valid ID."""
        fake_species = MagicMock()
        fake_species.model_dump.return_value = {
            "species_id": "species_leaflet",
            "name": "Leaflet",
            "element": "nature",
        }

        with patch(
            "elements_rpg.api.routers.monsters.monster_service.get_species",
            new_callable=AsyncMock,
            return_value=fake_species,
        ):
            response = await client.get("/monsters/bestiary/species_leaflet")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["name"] == "Leaflet"

    @pytest.mark.asyncio
    async def test_species_not_found_returns_404(self, client: AsyncClient) -> None:
        """Should return 404 for invalid species ID."""
        with patch(
            "elements_rpg.api.routers.monsters.monster_service.get_species",
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = await client.get("/monsters/bestiary/nonexistent")

        assert response.status_code == 404
        body = response.json()
        assert "not found" in body["detail"].lower()


# ===================================================================
# 3. GET /monsters/owned -- auth required
# ===================================================================


class TestGetOwnedMonsters:
    """GET /monsters/owned."""

    @pytest.mark.asyncio
    async def test_owned_monsters_success(self, client: AsyncClient) -> None:
        """Should return list of owned monsters."""
        fake_monsters = [
            {"monster_id": FAKE_MONSTER_ID, "name": "Leaflet", "level": 5},
        ]

        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.monsters.monster_service.get_owned_monsters",
                new_callable=AsyncMock,
                return_value=fake_monsters,
            ),
        ):
            response = await client.get("/monsters/owned")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert len(body["data"]) == 1
        assert body["data"][0]["name"] == "Leaflet"

    @pytest.mark.asyncio
    async def test_owned_monsters_no_auth(self, app, test_settings: Settings) -> None:
        """Should return 401/403 without auth."""
        app.dependency_overrides.pop(get_current_user, None)
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as unauthed:
            response = await unauthed.get("/monsters/owned")
        assert response.status_code in (401, 403)


# ===================================================================
# 4. GET /monsters/{monster_id} -- auth required
# ===================================================================


class TestGetMonster:
    """GET /monsters/{monster_id}."""

    @pytest.mark.asyncio
    async def test_get_monster_success(self, client: AsyncClient) -> None:
        """Should return monster details for valid owned monster."""
        fake_monster = {"monster_id": FAKE_MONSTER_ID, "name": "Leaflet", "level": 10}

        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.monsters.monster_service.get_monster",
                new_callable=AsyncMock,
                return_value=fake_monster,
            ),
        ):
            response = await client.get(f"/monsters/{FAKE_MONSTER_ID}")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["level"] == 10

    @pytest.mark.asyncio
    async def test_get_monster_not_found_returns_404(self, client: AsyncClient) -> None:
        """Should return 404 for non-owned or non-existent monster."""
        some_uuid = str(uuid.uuid4())
        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.monsters.monster_service.get_monster",
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            response = await client.get(f"/monsters/{some_uuid}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_monster_invalid_uuid_returns_400(self, client: AsyncClient) -> None:
        """Should return 400 for non-UUID monster_id."""
        with patch(
            "elements_rpg.api.dependencies.get_player_by_supabase_id",
            new_callable=AsyncMock,
            return_value=_mock_player(),
        ):
            response = await client.get("/monsters/not-a-valid-uuid")

        assert response.status_code == 400


# ===================================================================
# 5. PUT /monsters/{monster_id}/skills -- update equipped skills
# ===================================================================


class TestUpdateSkills:
    """PUT /monsters/{monster_id}/skills."""

    @pytest.mark.asyncio
    async def test_update_skills_success(self, client: AsyncClient) -> None:
        """Should update equipped skills successfully."""
        result = {
            "monster_id": FAKE_MONSTER_ID,
            "equipped_skill_ids": ["skill_a", "skill_b"],
        }

        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.monsters.monster_service.update_skills",
                new_callable=AsyncMock,
                return_value=result,
            ),
        ):
            response = await client.put(
                f"/monsters/{FAKE_MONSTER_ID}/skills",
                json={"skill_ids": ["skill_a", "skill_b"]},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["equipped_skill_ids"] == ["skill_a", "skill_b"]

    @pytest.mark.asyncio
    async def test_update_skills_too_many_returns_422(self, client: AsyncClient) -> None:
        """Should return 422 when more than 4 skills provided (Pydantic max_length)."""
        with patch(
            "elements_rpg.api.dependencies.get_player_by_supabase_id",
            new_callable=AsyncMock,
            return_value=_mock_player(),
        ):
            response = await client.put(
                f"/monsters/{FAKE_MONSTER_ID}/skills",
                json={"skill_ids": ["s1", "s2", "s3", "s4", "s5"]},
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_skills_invalid_skill_returns_400(self, client: AsyncClient) -> None:
        """Should return 400 when service rejects invalid skills."""
        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.monsters.monster_service.update_skills",
                new_callable=AsyncMock,
                side_effect=ValueError("Skills not learnable by this species"),
            ),
        ):
            response = await client.put(
                f"/monsters/{FAKE_MONSTER_ID}/skills",
                json={"skill_ids": ["invalid_skill"]},
            )

        assert response.status_code == 400


# ===================================================================
# 6. Verify deleted endpoints return 404/405
# ===================================================================


class TestDeletedEndpoints:
    """Verify removed client-trusted endpoints are gone."""

    @pytest.mark.asyncio
    async def test_xp_endpoint_removed(self, client: AsyncClient) -> None:
        """POST /monsters/{id}/xp should not exist."""
        response = await client.post(
            f"/monsters/{FAKE_MONSTER_ID}/xp",
            json={"amount": 100},
        )
        assert response.status_code in (404, 405)

    @pytest.mark.asyncio
    async def test_bond_endpoint_removed(self, client: AsyncClient) -> None:
        """POST /monsters/{id}/bond should not exist."""
        response = await client.post(
            f"/monsters/{FAKE_MONSTER_ID}/bond",
            json={"amount": 5},
        )
        assert response.status_code in (404, 405)
