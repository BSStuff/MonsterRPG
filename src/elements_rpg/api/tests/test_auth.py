"""Integration tests for the auth flow — JWT verification, endpoints, player service.

All external calls (Supabase Auth REST, database sessions, JWT decode) are mocked
so tests run without any live infrastructure.
"""

from __future__ import annotations

import uuid
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from jose import JWTError

from elements_rpg.api.auth import _decode_supabase_jwt, get_current_user
from elements_rpg.api.config import Settings, get_settings

if TYPE_CHECKING:
    from fastapi import FastAPI

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


@pytest.fixture
def app(test_settings: Settings) -> FastAPI:
    """Create a FastAPI app with overridden settings."""
    with patch("elements_rpg.api.app.get_settings", return_value=test_settings):
        application = create_app()
    application.dependency_overrides[get_settings] = lambda: test_settings
    return application


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# Lazy import to avoid load-order issues with settings
def create_app() -> FastAPI:
    from elements_rpg.api.app import create_app as _create

    return _create()


VALID_JWT_PAYLOAD: dict[str, Any] = {
    "sub": "supabase-uid-123",
    "email": "hero@example.com",
    "role": "authenticated",
    "aud": "authenticated",
    "exp": 9999999999,
}

SUPABASE_SIGNUP_RESPONSE: dict[str, Any] = {
    "access_token": "access-tok",
    "refresh_token": "refresh-tok",
    "expires_in": 3600,
    "user": {"id": "supabase-uid-123", "email": "hero@example.com"},
}

SUPABASE_TOKEN_RESPONSE: dict[str, Any] = {
    "access_token": "access-tok-2",
    "refresh_token": "refresh-tok-2",
    "expires_in": 3600,
    "user": {"id": "supabase-uid-123", "email": "hero@example.com"},
}


# ===================================================================
# 1. JWT Verification Unit Tests
# ===================================================================


class TestDecodeSupabaseJwt:
    """Tests for _decode_supabase_jwt helper."""

    def test_valid_jwt_decodes(self, test_settings: Settings) -> None:
        """A valid JWT should return its payload dict."""
        with patch("elements_rpg.api.auth.jwt.decode", return_value=VALID_JWT_PAYLOAD):
            result = _decode_supabase_jwt("fake.jwt.token", test_settings)
        assert result == VALID_JWT_PAYLOAD
        assert result["sub"] == "supabase-uid-123"

    def test_expired_jwt_raises_401(self, test_settings: Settings) -> None:
        """An expired or invalid JWT should raise HTTPException 401."""
        with patch(
            "elements_rpg.api.auth.jwt.decode",
            side_effect=JWTError("Token expired"),
        ):
            with pytest.raises(Exception) as exc_info:
                _decode_supabase_jwt("expired.jwt.token", test_settings)
            assert exc_info.value.status_code == 401  # type: ignore[union-attr]
            assert "Invalid or expired token" in str(exc_info.value.detail)  # type: ignore[union-attr]

    def test_missing_sub_in_payload(self, test_settings: Settings) -> None:
        """A JWT without 'sub' should decode successfully — the sub check is upstream."""
        payload_no_sub = {"email": "hero@example.com", "role": "authenticated"}
        with patch("elements_rpg.api.auth.jwt.decode", return_value=payload_no_sub):
            result = _decode_supabase_jwt("no-sub.jwt.token", test_settings)
            assert "sub" not in result

    @pytest.mark.asyncio
    async def test_get_current_user_rejects_missing_sub(
        self,
        test_settings: Settings,
    ) -> None:
        """get_current_user should raise 401 when payload has no 'sub'."""
        payload_no_sub = {"email": "hero@example.com", "role": "authenticated"}
        mock_creds = MagicMock()
        mock_creds.credentials = "no-sub.jwt.token"

        with patch("elements_rpg.api.auth.jwt.decode", return_value=payload_no_sub):
            with pytest.raises(Exception) as exc_info:
                await get_current_user(credentials=mock_creds, settings=test_settings)
            assert exc_info.value.status_code == 401  # type: ignore[union-attr]
            assert "missing user id" in str(exc_info.value.detail).lower()  # type: ignore[union-attr]


# ===================================================================
# Helpers for endpoint tests
# ===================================================================


def _mock_db_session() -> AsyncMock:
    """Create a mock async DB session."""
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    return session


def _make_httpx_response(
    status_code: int = 200,
    json_data: dict[str, Any] | None = None,
) -> MagicMock:
    """Build a mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {"content-type": "application/json"}
    resp.json.return_value = json_data or {}
    resp.text = str(json_data)
    return resp


@contextmanager
def _patch_httpx(mock_resp: MagicMock):
    """Context manager that patches httpx.AsyncClient to return mock_resp."""
    mock_client_inst = AsyncMock()
    mock_client_inst.post = AsyncMock(return_value=mock_resp)

    with patch("elements_rpg.api.routers.auth.httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client_inst)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        yield mock_cls


def _override_db(app: FastAPI) -> AsyncMock:
    """Override the get_db dependency with a mock session and return it."""
    from elements_rpg.db.session import get_db

    mock_db = _mock_db_session()

    async def _fake_db():
        yield mock_db

    app.dependency_overrides[get_db] = _fake_db
    return mock_db


# ===================================================================
# 2. Auth Endpoint Tests
# ===================================================================


class TestRegisterEndpoint:
    """POST /auth/register."""

    @pytest.mark.asyncio
    async def test_register_success(self, app: FastAPI, client: AsyncClient) -> None:
        """Successful registration creates player and returns tokens."""
        _override_db(app)
        mock_resp = _make_httpx_response(200, SUPABASE_SIGNUP_RESPONSE)

        with (
            _patch_httpx(mock_resp),
            patch(
                "elements_rpg.api.routers.auth.create_player",
                new_callable=AsyncMock,
            ) as mock_create,
        ):
            response = await client.post(
                "/auth/register",
                json={
                    "email": "hero@example.com",
                    "password": "strongpass123",
                    "username": "HeroPlayer",
                },
            )

        assert response.status_code == 201
        body = response.json()
        assert body["success"] is True
        assert body["data"]["access_token"] == "access-tok"
        assert body["data"]["refresh_token"] == "refresh-tok"
        assert body["data"]["user"]["email"] == "hero@example.com"
        assert body["data"]["user"]["username"] == "HeroPlayer"
        mock_create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_register_short_password_returns_422(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        """Password shorter than 8 chars should return 422 validation error."""
        _override_db(app)
        response = await client.post(
            "/auth/register",
            json={
                "email": "hero@example.com",
                "password": "short",
                "username": "HeroPlayer",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_email_returns_422(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        """Invalid email format should return 422."""
        _override_db(app)
        response = await client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "password": "strongpass123",
                "username": "HeroPlayer",
            },
        )
        assert response.status_code == 422


class TestLoginEndpoint:
    """POST /auth/login."""

    @pytest.mark.asyncio
    async def test_login_success(self, app: FastAPI, client: AsyncClient) -> None:
        """Successful login returns tokens from Supabase."""
        mock_resp = _make_httpx_response(200, SUPABASE_TOKEN_RESPONSE)

        with _patch_httpx(mock_resp):
            response = await client.post(
                "/auth/login",
                json={"email": "hero@example.com", "password": "strongpass123"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["access_token"] == "access-tok-2"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        """Supabase returning 400 should propagate as 400 to the caller."""
        error_detail = {
            "error": "invalid_grant",
            "error_description": "Invalid credentials",
        }
        mock_resp = _make_httpx_response(400, error_detail)

        with _patch_httpx(mock_resp):
            response = await client.post(
                "/auth/login",
                json={"email": "hero@example.com", "password": "wrongpass"},
            )

        assert response.status_code == 400


class TestRefreshEndpoint:
    """POST /auth/refresh."""

    @pytest.mark.asyncio
    async def test_refresh_success(self, app: FastAPI, client: AsyncClient) -> None:
        """Valid refresh token returns new tokens."""
        refresh_response = {
            "access_token": "new-access-tok",
            "refresh_token": "new-refresh-tok",
            "expires_in": 3600,
            "user": {"id": "supabase-uid-123", "email": "hero@example.com"},
        }
        mock_resp = _make_httpx_response(200, refresh_response)

        with _patch_httpx(mock_resp):
            response = await client.post(
                "/auth/refresh",
                json={"refresh_token": "old-refresh-tok"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["access_token"] == "new-access-tok"
        assert body["data"]["refresh_token"] == "new-refresh-tok"


class TestMeEndpoint:
    """GET /auth/me."""

    @pytest.mark.asyncio
    async def test_me_with_valid_token(self, app: FastAPI, client: AsyncClient) -> None:
        """A valid Bearer token should return user info."""
        app.dependency_overrides[get_current_user] = lambda: VALID_JWT_PAYLOAD

        response = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer fake.valid.token"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["user_id"] == "supabase-uid-123"
        assert body["data"]["email"] == "hero@example.com"
        assert body["data"]["role"] == "authenticated"

        app.dependency_overrides.pop(get_current_user, None)

    @pytest.mark.asyncio
    async def test_me_without_token_returns_error(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        """Missing Authorization header should return 401 or 403."""
        app.dependency_overrides.pop(get_current_user, None)

        response = await client.get("/auth/me")
        # HTTPBearer returns 403 by default, but some configurations return 401
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_me_with_invalid_token_returns_401(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        """An invalid JWT should return 401."""
        app.dependency_overrides.pop(get_current_user, None)

        with patch(
            "elements_rpg.api.auth.jwt.decode",
            side_effect=JWTError("Invalid token"),
        ):
            response = await client.get(
                "/auth/me",
                headers={"Authorization": "Bearer invalid.jwt.token"},
            )

        assert response.status_code == 401


# ===================================================================
# 3. Player Service Tests
# ===================================================================


class TestPlayerService:
    """Tests for player_service CRUD functions with a mocked DB session."""

    @pytest.mark.asyncio
    async def test_create_player_creates_player_and_game_state(self) -> None:
        """create_player should add a PlayerDB and a GameStateDB to the session."""
        from elements_rpg.services.player_service import create_player

        mock_db = _mock_db_session()

        player = await create_player(
            mock_db,
            supabase_user_id="sup-uid-abc",
            username="TestHero",
        )

        assert player.username == "TestHero"
        assert player.supabase_user_id == "sup-uid-abc"
        assert player.level == 1
        assert player.experience == 0
        # PlayerDB + GameStateDB = 2 add() calls
        assert mock_db.add.call_count == 2
        mock_db.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_get_player_by_supabase_id(self) -> None:
        """get_player_by_supabase_id should query with the correct filter."""
        from elements_rpg.db.models.player import PlayerDB
        from elements_rpg.services.player_service import get_player_by_supabase_id

        fake_player = PlayerDB(
            id=uuid.uuid4(),
            supabase_user_id="sup-uid-xyz",
            username="Finder",
            level=5,
            experience=100,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fake_player

        mock_db = _mock_db_session()
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await get_player_by_supabase_id(mock_db, "sup-uid-xyz")

        assert result is not None
        assert result.username == "Finder"
        assert result.supabase_user_id == "sup-uid-xyz"
        mock_db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_player_by_supabase_id_not_found(self) -> None:
        """get_player_by_supabase_id returns None when player not found."""
        from elements_rpg.services.player_service import get_player_by_supabase_id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db = _mock_db_session()
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await get_player_by_supabase_id(mock_db, "nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_player_by_id(self) -> None:
        """get_player_by_id should query with the correct UUID filter."""
        from elements_rpg.db.models.player import PlayerDB
        from elements_rpg.services.player_service import get_player_by_id

        player_id = uuid.uuid4()
        fake_player = PlayerDB(
            id=player_id,
            supabase_user_id="sup-uid-999",
            username="IdLookup",
            level=10,
            experience=500,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fake_player

        mock_db = _mock_db_session()
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await get_player_by_id(mock_db, player_id)

        assert result is not None
        assert result.id == player_id
        assert result.username == "IdLookup"
        mock_db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_player_by_id_not_found(self) -> None:
        """get_player_by_id returns None when player not found."""
        from elements_rpg.services.player_service import get_player_by_id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db = _mock_db_session()
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await get_player_by_id(mock_db, uuid.uuid4())
        assert result is None
