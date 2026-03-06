"""Integration tests for the teams router endpoints.

All endpoints require authentication. DB and service calls are mocked.
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
FAKE_TEAM_ID = str(uuid.uuid4())
FAKE_MONSTER_IDS = [str(uuid.uuid4()) for _ in range(3)]


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


def _fake_team_response(
    team_id: str = FAKE_TEAM_ID,
    name: str = "Alpha Squad",
    members: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a fake team response dict."""
    if members is None:
        members = [
            {
                "member_id": str(uuid.uuid4()),
                "monster_id": mid,
                "role": None,
                "position": i,
            }
            for i, mid in enumerate(FAKE_MONSTER_IDS[:2])
        ]
    return {
        "team_id": team_id,
        "player_id": FAKE_PLAYER_ID,
        "name": name,
        "created_at": "2026-03-05T12:00:00+00:00",
        "members": members,
    }


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
# 1. GET /teams -- list teams
# ===================================================================


class TestListTeams:
    """GET /teams."""

    @pytest.mark.asyncio
    async def test_list_teams_success(self, client: AsyncClient) -> None:
        """Should return list of teams."""
        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.teams.team_service.get_teams",
                new_callable=AsyncMock,
                return_value=[_fake_team_response()],
            ),
        ):
            response = await client.get("/teams/")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert len(body["data"]) == 1
        assert body["data"][0]["name"] == "Alpha Squad"

    @pytest.mark.asyncio
    async def test_list_teams_empty(self, client: AsyncClient) -> None:
        """Should return empty list when no teams."""
        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.teams.team_service.get_teams",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            response = await client.get("/teams/")

        assert response.status_code == 200
        assert response.json()["data"] == []

    @pytest.mark.asyncio
    async def test_list_teams_no_auth(self, app, test_settings: Settings) -> None:
        """Should return 401/403 without auth."""
        app.dependency_overrides.pop(get_current_user, None)
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as unauthed:
            response = await unauthed.get("/teams/")
        assert response.status_code in (401, 403)


# ===================================================================
# 2. POST /teams -- create team
# ===================================================================


class TestCreateTeam:
    """POST /teams."""

    @pytest.mark.asyncio
    async def test_create_team_success(self, client: AsyncClient) -> None:
        """Should create team and return 201."""
        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.teams.team_service.create_team",
                new_callable=AsyncMock,
                return_value=_fake_team_response(),
            ),
        ):
            response = await client.post(
                "/teams/",
                json={
                    "name": "Alpha Squad",
                    "monster_ids": FAKE_MONSTER_IDS[:2],
                },
            )

        assert response.status_code == 201
        body = response.json()
        assert body["success"] is True
        assert body["data"]["name"] == "Alpha Squad"

    @pytest.mark.asyncio
    async def test_create_team_too_many_monsters_returns_422(self, client: AsyncClient) -> None:
        """Should return 422 when more than 6 monsters (Pydantic max_length)."""
        seven_ids = [str(uuid.uuid4()) for _ in range(7)]
        with patch(
            "elements_rpg.api.dependencies.get_player_by_supabase_id",
            new_callable=AsyncMock,
            return_value=_mock_player(),
        ):
            response = await client.post(
                "/teams/",
                json={"name": "Big Team", "monster_ids": seven_ids},
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_team_validation_error_returns_400(self, client: AsyncClient) -> None:
        """Should return 400 when service rejects (e.g., unowned monsters)."""
        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.teams.team_service.create_team",
                new_callable=AsyncMock,
                side_effect=ValueError("Monsters not owned by player"),
            ),
        ):
            response = await client.post(
                "/teams/",
                json={"name": "Bad Team", "monster_ids": [str(uuid.uuid4())]},
            )

        assert response.status_code == 400


# ===================================================================
# 3. PUT /teams/{team_id} -- update team
# ===================================================================


class TestUpdateTeam:
    """PUT /teams/{team_id}."""

    @pytest.mark.asyncio
    async def test_update_team_success(self, client: AsyncClient) -> None:
        """Should update team name and/or composition."""
        updated = _fake_team_response(name="Beta Squad")

        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.teams.team_service.update_team",
                new_callable=AsyncMock,
                return_value=updated,
            ),
        ):
            response = await client.put(
                f"/teams/{FAKE_TEAM_ID}",
                json={"name": "Beta Squad"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["name"] == "Beta Squad"

    @pytest.mark.asyncio
    async def test_update_team_not_found_returns_400(self, client: AsyncClient) -> None:
        """Should return 400 when team not found or not owned."""
        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.teams.team_service.update_team",
                new_callable=AsyncMock,
                side_effect=ValueError("Team not found"),
            ),
        ):
            response = await client.put(
                f"/teams/{FAKE_TEAM_ID}",
                json={"name": "Ghost Team"},
            )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_update_team_invalid_uuid_returns_400(self, client: AsyncClient) -> None:
        """Should return 400 for invalid team UUID."""
        with patch(
            "elements_rpg.api.dependencies.get_player_by_supabase_id",
            new_callable=AsyncMock,
            return_value=_mock_player(),
        ):
            response = await client.put(
                "/teams/not-a-uuid",
                json={"name": "Test"},
            )

        assert response.status_code == 400


# ===================================================================
# 4. DELETE /teams/{team_id}
# ===================================================================


class TestDeleteTeam:
    """DELETE /teams/{team_id}."""

    @pytest.mark.asyncio
    async def test_delete_team_success(self, client: AsyncClient) -> None:
        """Should delete team and return confirmation."""
        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.teams.team_service.delete_team",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            response = await client.delete(f"/teams/{FAKE_TEAM_ID}")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["deleted"] == FAKE_TEAM_ID

    @pytest.mark.asyncio
    async def test_delete_team_not_found_returns_404(self, client: AsyncClient) -> None:
        """Should return 404 when team not found."""
        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.teams.team_service.delete_team",
                new_callable=AsyncMock,
                side_effect=ValueError("Team not found"),
            ),
        ):
            response = await client.delete(f"/teams/{FAKE_TEAM_ID}")

        assert response.status_code == 404


# ===================================================================
# 5. PUT /teams/{team_id}/reorder
# ===================================================================


class TestReorderTeam:
    """PUT /teams/{team_id}/reorder."""

    @pytest.mark.asyncio
    async def test_reorder_success(self, client: AsyncClient) -> None:
        """Should reorder members and return updated team."""
        reordered = _fake_team_response()

        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.teams.team_service.reorder_team",
                new_callable=AsyncMock,
                return_value=reordered,
            ),
        ):
            response = await client.put(
                f"/teams/{FAKE_TEAM_ID}/reorder",
                json={"ordered_monster_ids": list(reversed(FAKE_MONSTER_IDS[:2]))},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert "members" in body["data"]

    @pytest.mark.asyncio
    async def test_reorder_mismatch_returns_400(self, client: AsyncClient) -> None:
        """Should return 400 when IDs don't match current members."""
        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.teams.team_service.reorder_team",
                new_callable=AsyncMock,
                side_effect=ValueError("Reorder IDs must exactly match"),
            ),
        ):
            response = await client.put(
                f"/teams/{FAKE_TEAM_ID}/reorder",
                json={"ordered_monster_ids": [str(uuid.uuid4())]},
            )

        assert response.status_code == 400


# ===================================================================
# 6. PUT /teams/{team_id}/roles
# ===================================================================


class TestAssignRoles:
    """PUT /teams/{team_id}/roles."""

    @pytest.mark.asyncio
    async def test_assign_roles_success(self, client: AsyncClient) -> None:
        """Should assign roles and return updated team."""
        updated = _fake_team_response()
        updated["members"][0]["role"] = "tank"

        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.teams.team_service.assign_roles",
                new_callable=AsyncMock,
                return_value=updated,
            ),
        ):
            response = await client.put(
                f"/teams/{FAKE_TEAM_ID}/roles",
                json={
                    "role_assignments": {FAKE_MONSTER_IDS[0]: "tank"},
                },
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True

    @pytest.mark.asyncio
    async def test_assign_roles_monster_not_on_team_returns_400(self, client: AsyncClient) -> None:
        """Should return 400 when monster is not on the team."""
        with (
            patch(
                "elements_rpg.api.dependencies.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.teams.team_service.assign_roles",
                new_callable=AsyncMock,
                side_effect=ValueError("Monster is not on team"),
            ),
        ):
            response = await client.put(
                f"/teams/{FAKE_TEAM_ID}/roles",
                json={
                    "role_assignments": {str(uuid.uuid4()): "healer"},
                },
            )

        assert response.status_code == 400
