"""Integration tests for skills router -- skill catalog, XP, strategies.

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
# 1. GET /skills/catalog
# ===================================================================


class TestSkillCatalog:
    """GET /skills/catalog."""

    @pytest.mark.asyncio
    async def test_catalog_returns_all_skills(self, client: AsyncClient) -> None:
        """Should return the full skill catalog."""
        response = await client.get("/skills/catalog")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)
        # MVP catalog has 28 skills
        assert len(body["data"]) == 28

    @pytest.mark.asyncio
    async def test_catalog_skill_has_required_fields(self, client: AsyncClient) -> None:
        """Each skill should have id, name, type, element, power."""
        response = await client.get("/skills/catalog")
        skill = response.json()["data"][0]
        assert "skill_id" in skill
        assert "name" in skill
        assert "skill_type" in skill
        assert "element" in skill
        assert "power" in skill


# ===================================================================
# 2. GET /skills/{skill_id}
# ===================================================================


class TestGetSkill:
    """GET /skills/{skill_id}."""

    @pytest.mark.asyncio
    async def test_get_skill_success(self, client: AsyncClient) -> None:
        """Should return skill details."""
        response = await client.get("/skills/skill_vine_whip")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["skill_id"] == "skill_vine_whip"
        assert body["data"]["name"] == "Vine Whip"

    @pytest.mark.asyncio
    async def test_get_skill_not_found(self, client: AsyncClient) -> None:
        """Should return 404 for unknown skill."""
        response = await client.get("/skills/skill_nonexistent")
        assert response.status_code == 404


# ===================================================================
# 3. POST /skills/{skill_id}/experience
# ===================================================================


class TestGrantSkillXP:
    """POST /skills/{skill_id}/experience."""

    @pytest.mark.asyncio
    async def test_grant_xp_success(self, client: AsyncClient) -> None:
        """Should grant XP and return updated info."""
        mock_result = {
            "skill_id": "skill_vine_whip",
            "name": "Vine Whip",
            "previous_level": 1,
            "new_level": 2,
            "levels_gained": [2],
            "experience": 10,
            "effective_power": 45,
            "effective_cooldown": 1.98,
            "unlocked_milestones": [],
        }
        with (
            patch(
                "elements_rpg.api.routers.skills.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.services.skills_service.grant_skill_xp",
                new_callable=AsyncMock,
                return_value=mock_result,
            ),
        ):
            response = await client.post(
                "/skills/skill_vine_whip/experience",
                json={"amount": 100},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["levels_gained"] == [2]

    @pytest.mark.asyncio
    async def test_grant_xp_invalid_amount(self, client: AsyncClient) -> None:
        """Should return 422 for zero/negative amount."""
        with patch(
            "elements_rpg.api.routers.skills.get_player_by_supabase_id",
            new_callable=AsyncMock,
            return_value=_mock_player(),
        ):
            response = await client.post(
                "/skills/skill_vine_whip/experience",
                json={"amount": 0},
            )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_grant_xp_no_auth(self, app, test_settings: Settings) -> None:
        """Should return 401/403 without auth."""
        app.dependency_overrides.pop(get_current_user, None)
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as unauthed:
            response = await unauthed.post(
                "/skills/skill_vine_whip/experience",
                json={"amount": 50},
            )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_grant_xp_skill_not_found(self, client: AsyncClient) -> None:
        """Should return 400 for unknown skill."""
        with (
            patch(
                "elements_rpg.api.routers.skills.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.services.skills_service.grant_skill_xp",
                new_callable=AsyncMock,
                side_effect=ValueError("Skill 'skill_bad' not found in catalog"),
            ),
        ):
            response = await client.post(
                "/skills/skill_bad/experience",
                json={"amount": 50},
            )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_grant_xp_player_not_found(self, client: AsyncClient) -> None:
        """Should return 404 if player not found."""
        with patch(
            "elements_rpg.api.routers.skills.get_player_by_supabase_id",
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = await client.post(
                "/skills/skill_vine_whip/experience",
                json={"amount": 50},
            )
        assert response.status_code == 404


# ===================================================================
# 4. GET /skills/strategies
# ===================================================================


class TestGetStrategies:
    """GET /skills/strategies."""

    @pytest.mark.asyncio
    async def test_strategies_returns_all(self, client: AsyncClient) -> None:
        """Should return all 5 strategy types."""
        response = await client.get("/skills/strategies")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert len(body["data"]) == 5

    @pytest.mark.asyncio
    async def test_strategy_has_required_fields(self, client: AsyncClient) -> None:
        """Each strategy should have name, description, aggression."""
        response = await client.get("/skills/strategies")
        strategy = response.json()["data"][0]
        assert "strategy" in strategy
        assert "description" in strategy
        assert "aggression" in strategy


# ===================================================================
# 5. POST /skills/strategies/{strategy}/experience
# ===================================================================


class TestGrantStrategyXP:
    """POST /skills/strategies/{strategy}/experience."""

    @pytest.mark.asyncio
    async def test_grant_strategy_xp_success(self, client: AsyncClient) -> None:
        """Should grant strategy XP and return proficiency info."""
        mock_result = {
            "strategy": "aggressive",
            "previous_level": 1,
            "new_level": 2,
            "levels_gained": [2],
            "experience": 50,
            "is_mastered": False,
        }
        with (
            patch(
                "elements_rpg.api.routers.skills.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.services.skills_service.grant_strategy_xp",
                new_callable=AsyncMock,
                return_value=mock_result,
            ),
        ):
            response = await client.post(
                "/skills/strategies/aggressive/experience",
                json={"amount": 300},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["strategy"] == "aggressive"

    @pytest.mark.asyncio
    async def test_grant_strategy_xp_invalid_strategy(self, client: AsyncClient) -> None:
        """Should return 400 for invalid strategy type."""
        with (
            patch(
                "elements_rpg.api.routers.skills.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.services.skills_service.grant_strategy_xp",
                new_callable=AsyncMock,
                side_effect=ValueError("Invalid strategy 'invalid'"),
            ),
        ):
            response = await client.post(
                "/skills/strategies/invalid/experience",
                json={"amount": 100},
            )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_grant_strategy_xp_no_auth(self, app, test_settings: Settings) -> None:
        """Should return 401/403 without auth."""
        app.dependency_overrides.pop(get_current_user, None)
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as unauthed:
            response = await unauthed.post(
                "/skills/strategies/aggressive/experience",
                json={"amount": 100},
            )
        assert response.status_code in (401, 403)
