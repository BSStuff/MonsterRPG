"""End-to-end API test — simulates a full player journey through all domains.

Mocks Supabase Auth and DB dependencies. Tests that routes are wired correctly,
schemas validate, and the API is coherent across all 15+ endpoints.
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
from elements_rpg.services.combat_service import clear_all_sessions

PLAYER_UUID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

VALID_JWT_PAYLOAD: dict[str, Any] = {
    "sub": "test-supabase-uid-e2e",
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
    """Deterministic test settings."""
    return Settings(
        supabase_url="https://test.supabase.co",
        supabase_key="test-anon-key",
        supabase_jwt_secret="test-jwt-secret",
        supabase_service_key="test-service-key",
        database_url="sqlite+aiosqlite:///:memory:",
        debug=True,
    )


def _mock_db_session() -> AsyncMock:
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    return session


def _mock_player() -> MagicMock:
    """Fake player with deterministic UUID."""
    import uuid

    player = MagicMock()
    player.id = uuid.UUID(PLAYER_UUID)
    return player


def _create_app():
    from elements_rpg.api.app import create_app as _create

    return _create()


@pytest.fixture
def app(test_settings: Settings):
    """Create FastAPI app with overridden auth and DB dependencies."""
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
    """Clear combat sessions between tests."""
    clear_all_sessions()
    yield
    clear_all_sessions()


# ===================================================================
# Full player journey E2E test
# ===================================================================


class TestFullPlayerJourney:
    """End-to-end test simulating a complete player lifecycle.

    Each step is a separate test method to isolate failures, but they
    collectively verify that every major API surface is wired correctly.
    """

    # ------------------------------------------------------------------
    # 1. Register a new player (mock Supabase auth)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_01_register_player(self, client: AsyncClient) -> None:
        """POST /auth/register should create a player via Supabase proxy."""
        fake_supabase_response = {
            "access_token": "fake-access-token",
            "refresh_token": "fake-refresh-token",
            "expires_in": 3600,
            "user": {
                "id": "test-supabase-uid-e2e",
                "email": "hero@example.com",
            },
        }

        with (
            patch(
                "elements_rpg.api.routers.auth._supabase_post",
                new_callable=AsyncMock,
                return_value=fake_supabase_response,
            ),
            patch(
                "elements_rpg.api.routers.auth.create_player",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
        ):
            response = await client.post(
                "/auth/register",
                json={
                    "email": "hero@example.com",
                    "password": "securepass123",
                    "username": "HeroPlayer",
                },
            )

        assert response.status_code == 201
        body = response.json()
        assert body["data"]["access_token"] == "fake-access-token"
        assert body["data"]["user"]["email"] == "hero@example.com"

    # ------------------------------------------------------------------
    # 2. Load initial game state (GET /saves)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_02_load_game_state(self, client: AsyncClient) -> None:
        """GET /saves should return saved game data."""
        fake_game_data = MagicMock()
        fake_game_data.model_dump.return_value = {
            "save_version": 1,
            "player_id": PLAYER_UUID,
            "player_name": "Hero",
        }

        with (
            patch(
                "elements_rpg.api.routers.saves.get_player_by_supabase_id",
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

    # ------------------------------------------------------------------
    # 3. View bestiary (GET /monsters/bestiary)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_03_view_bestiary(self, client: AsyncClient) -> None:
        """GET /monsters/bestiary should list all species (no auth needed)."""
        response = await client.get("/monsters/bestiary")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)
        assert len(body["data"]) >= 1
        # Each entry should have basic species fields
        first = body["data"][0]
        assert "species_id" in first
        assert "name" in first

    # ------------------------------------------------------------------
    # 4. Create a team (POST /teams)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_04_create_team(self, client: AsyncClient) -> None:
        """POST /teams should create a new team."""
        fake_team = {
            "team_id": "fake-team-id",
            "name": "Alpha Squad",
            "monsters": [],
        }

        with (
            patch(
                "elements_rpg.api.routers.teams.player_service.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.teams.team_service.create_team",
                new_callable=AsyncMock,
                return_value=fake_team,
            ),
        ):
            response = await client.post(
                "/teams/",
                json={"name": "Alpha Squad", "monster_ids": []},
            )

        assert response.status_code == 201
        body = response.json()
        assert body["success"] is True
        assert body["data"]["name"] == "Alpha Squad"

    # ------------------------------------------------------------------
    # 5. Start combat (POST /combat/start)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_05_start_combat(self, client: AsyncClient) -> None:
        """POST /combat/start should create a combat session."""
        response = await client.post(
            "/combat/start",
            json={"enemy_species_ids": ["species_leaflet"], "enemy_level": 1},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["success"] is True
        assert "session_id" in body["data"]
        assert body["data"]["state"]["round"] == 0
        assert body["data"]["state"]["is_finished"] is False

    # ------------------------------------------------------------------
    # 6. Execute combat rounds until finished
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_06_execute_combat_rounds(self, client: AsyncClient) -> None:
        """Combat rounds should execute until one side wins."""
        start_resp = await client.post(
            "/combat/start",
            json={"enemy_species_ids": ["species_leaflet"], "enemy_level": 1},
        )
        session_id = start_resp.json()["data"]["session_id"]

        finished = False
        for _ in range(100):
            resp = await client.post(f"/combat/{session_id}/round")
            assert resp.status_code == 200
            state = resp.json()["data"]["state"]
            if state["is_finished"]:
                finished = True
                break

        assert finished, "Combat did not finish within 100 rounds"

        # Finish and get rewards
        finish_resp = await client.post(f"/combat/{session_id}/finish")
        assert finish_resp.status_code == 200
        finish_body = finish_resp.json()
        assert finish_body["data"]["finished"] is True
        assert finish_body["data"]["rounds"] >= 1

    # ------------------------------------------------------------------
    # 7. Calculate taming chance (POST /taming/calculate)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_07_calculate_taming_chance(self, client: AsyncClient) -> None:
        """POST /taming/calculate should return taming probability."""
        fake_result = {
            "species_id": "species_leaflet",
            "base_chance": 0.15,
            "food_bonus": 0.05,
            "skill_bonus": 0.0,
            "pity_bonus": 0.0,
            "total_chance": 0.20,
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
                return_value=fake_result,
            ),
        ):
            response = await client.post(
                "/taming/calculate",
                json={
                    "species_id": "species_leaflet",
                    "food_bonus": 0.05,
                    "skill_bonus": 0.0,
                },
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["total_chance"] == 0.20

    # ------------------------------------------------------------------
    # 8. Attempt to tame a monster (POST /taming/attempt)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_08_attempt_taming(self, client: AsyncClient) -> None:
        """POST /taming/attempt should return success/fail + pity state."""
        fake_result = {
            "success": True,
            "species_id": "species_leaflet",
            "roll": 0.05,
            "threshold": 0.20,
            "pity_counter": 0,
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
                return_value=fake_result,
            ),
        ):
            response = await client.post(
                "/taming/attempt",
                json={
                    "species_id": "species_leaflet",
                    "food_bonus": 0.05,
                    "skill_bonus": 0.0,
                },
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["success"] is True

    # ------------------------------------------------------------------
    # 9. Check economy balance (GET /economy/balance)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_09_check_economy_balance(self, client: AsyncClient) -> None:
        """GET /economy/balance should return gold and gems."""
        fake_balance = {"gold": 500, "gems": 10}

        with (
            patch(
                "elements_rpg.api.routers.economy.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.economy.service_get_balance",
                new_callable=AsyncMock,
                return_value=fake_balance,
            ),
        ):
            response = await client.get("/economy/balance")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["gold"] == 500
        assert body["data"]["gems"] == 10

    # ------------------------------------------------------------------
    # 10. Earn gold (POST /economy/gold/earn)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_10_earn_gold(self, client: AsyncClient) -> None:
        """POST /economy/gold/earn should increase gold balance."""
        fake_balance = {"gold": 600, "gems": 10}

        with (
            patch(
                "elements_rpg.api.routers.economy.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.economy.service_earn_gold",
                new_callable=AsyncMock,
                return_value=fake_balance,
            ),
        ):
            response = await client.post(
                "/economy/gold/earn",
                json={"amount": 100, "reason": "combat_reward"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["gold"] == 600

    # ------------------------------------------------------------------
    # 11. View crafting recipes (GET /crafting/recipes)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_11_view_crafting_recipes(self, client: AsyncClient) -> None:
        """GET /crafting/recipes should return available recipes."""
        fake_recipes = [
            {"recipe_id": "health_potion", "name": "Health Potion", "materials": {}},
        ]

        with patch(
            "elements_rpg.api.routers.crafting.service_get_recipes",
            new_callable=AsyncMock,
            return_value=fake_recipes,
        ):
            response = await client.get("/crafting/recipes")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)
        assert len(body["data"]) >= 1

    # ------------------------------------------------------------------
    # 12. Check idle tracker (GET /idle/tracker)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_12_check_idle_tracker(self, client: AsyncClient) -> None:
        """GET /idle/tracker should return BRPM and idle metrics."""
        fake_tracker = {
            "best_clear_time": 120.0,
            "brpm": 5.0,
            "idle_rate": 0.85,
            "areas": {},
        }

        with (
            patch(
                "elements_rpg.api.routers.idle.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.idle.idle_service.get_tracker",
                new_callable=AsyncMock,
                return_value=fake_tracker,
            ),
        ):
            response = await client.get("/idle/tracker")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["idle_rate"] == 0.85

    # ------------------------------------------------------------------
    # 13. View skill catalog (GET /skills/catalog)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_13_view_skill_catalog(self, client: AsyncClient) -> None:
        """GET /skills/catalog should list all available skills."""
        response = await client.get("/skills/catalog")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)
        assert len(body["data"]) >= 1

    # ------------------------------------------------------------------
    # 14. Check premium packages (GET /premium/packages)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_14_check_premium_packages(self, client: AsyncClient) -> None:
        """GET /premium/packages should list gem packages."""
        response = await client.get("/premium/packages")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)
        assert len(body["data"]) >= 1
        # Each package should have amount and price
        first = body["data"][0]
        assert "gem_amount" in first or "gems" in first or "amount" in first

    # ------------------------------------------------------------------
    # 15. Save game state (POST /saves)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_15_save_game_state(self, client: AsyncClient) -> None:
        """POST /saves should persist game state and return version."""
        fake_db_state = MagicMock()
        fake_db_state.version = 3
        fake_db_state.updated_at = datetime(2026, 3, 5, 14, 0, 0, tzinfo=UTC)

        save_body = {
            "player": {
                "player_id": PLAYER_UUID,
                "username": "HeroPlayer",
            },
        }

        with (
            patch(
                "elements_rpg.api.routers.saves.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.saves.save_game_state",
                new_callable=AsyncMock,
                return_value=fake_db_state,
            ),
        ):
            response = await client.post("/saves/", json=save_body)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["version"] == 3


# ===================================================================
# Cross-cutting concerns
# ===================================================================


class TestCrossCuttingConcerns:
    """Verify API-wide behaviors that apply across all endpoints."""

    @pytest.mark.asyncio
    async def test_health_check_no_auth(self, client: AsyncClient) -> None:
        """GET /health should work without auth."""
        response = await client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_auth_required_on_protected_endpoints(
        self,
        app,
        test_settings: Settings,
    ) -> None:
        """Protected endpoints should reject requests without JWT."""
        app.dependency_overrides.pop(get_current_user, None)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as unauthed:
            protected_endpoints = [
                ("GET", "/saves/"),
                ("GET", "/economy/balance"),
                ("GET", "/idle/tracker"),
                ("GET", "/teams/"),
            ]

            for method, url in protected_endpoints:
                if method == "GET":
                    resp = await unauthed.get(url)
                else:
                    resp = await unauthed.post(url, json={})
                assert resp.status_code in (401, 403), (
                    f"{method} {url} returned {resp.status_code}, expected 401/403"
                )

    @pytest.mark.asyncio
    async def test_public_endpoints_no_auth(self, client: AsyncClient) -> None:
        """Public endpoints should work without auth."""
        public_endpoints = [
            "/health",
            "/monsters/bestiary",
            "/skills/catalog",
            "/skills/strategies",
            "/crafting/recipes",
            "/premium/packages",
            "/premium/upgrades",
            "/premium/subscriptions/plans",
            "/economy/areas",
        ]

        for url in public_endpoints:
            resp = await client.get(url)
            assert resp.status_code == 200, f"GET {url} returned {resp.status_code}, expected 200"

    @pytest.mark.asyncio
    async def test_error_response_is_structured_json(
        self,
        client: AsyncClient,
    ) -> None:
        """Unknown routes should return structured error JSON, not stack traces."""
        response = await client.get("/nonexistent/route")
        assert response.status_code in (404, 405)
        body = response.json()
        # FastAPI returns {"detail": ...} for unmatched routes
        assert "detail" in body or "error" in body

    @pytest.mark.asyncio
    async def test_invalid_json_returns_422(self, client: AsyncClient) -> None:
        """Malformed request bodies should return 422 with validation detail."""
        response = await client.post(
            "/combat/start",
            content="not valid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_success_response_envelope(self, client: AsyncClient) -> None:
        """Successful responses should use the SuccessResponse envelope."""
        response = await client.get("/monsters/bestiary")
        body = response.json()
        assert "success" in body
        assert "data" in body
        assert "timestamp" in body
        assert body["success"] is True
