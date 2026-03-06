"""Integration tests for skills router -- skill catalog and strategies (read-only).

XP-granting endpoints have been removed (server-authoritative economy).
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from elements_rpg.api.auth import get_current_user
from elements_rpg.api.config import Settings, get_settings

VALID_JWT_PAYLOAD: dict[str, Any] = {
    "sub": "test-player-uuid-123",
    "email": "hero@example.com",
    "role": "authenticated",
    "aud": "authenticated",
    "exp": 9999999999,
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


@pytest.fixture
def app(test_settings: Settings):
    with patch("elements_rpg.api.app.get_settings", return_value=test_settings):
        application = _create_app()
    application.dependency_overrides[get_settings] = lambda: test_settings
    application.dependency_overrides[get_current_user] = lambda: VALID_JWT_PAYLOAD
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
# 3. GET /skills/strategies
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
# 4. Verify deleted endpoints return 404/405
# ===================================================================


class TestDeletedEndpoints:
    """Verify removed client-trusted XP endpoints are gone."""

    @pytest.mark.asyncio
    async def test_skill_xp_endpoint_removed(self, client: AsyncClient) -> None:
        """POST /skills/{id}/experience should not exist."""
        response = await client.post(
            "/skills/skill_vine_whip/experience",
            json={"amount": 100},
        )
        assert response.status_code in (404, 405)

    @pytest.mark.asyncio
    async def test_strategy_xp_endpoint_removed(self, client: AsyncClient) -> None:
        """POST /skills/strategies/{strategy}/experience should not exist."""
        response = await client.post(
            "/skills/strategies/aggressive/experience",
            json={"amount": 100},
        )
        assert response.status_code in (404, 405)
