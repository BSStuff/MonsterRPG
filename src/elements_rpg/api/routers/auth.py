"""Authentication router — register, login, refresh, and user info endpoints.

Proxies authentication requests to the Supabase Auth REST API and manages
player profile creation in the local database.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from elements_rpg.api.auth import get_current_user

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
from elements_rpg.api.config import Settings, get_settings
from elements_rpg.api.schemas import SuccessResponse
from elements_rpg.db.session import get_db
from elements_rpg.services.player_service import create_player

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    """Payload for new player registration."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    username: str = Field(..., min_length=3, max_length=30)


class LoginRequest(BaseModel):
    """Payload for email/password login."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class RefreshRequest(BaseModel):
    """Payload for token refresh."""

    refresh_token: str


class AuthResponse(BaseModel):
    """Tokens returned by Supabase Auth."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict[str, Any]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SUPABASE_TIMEOUT = 10.0  # seconds


def _supabase_headers(settings: Settings) -> dict[str, str]:
    """Return common headers for Supabase Auth REST calls."""
    return {
        "apikey": settings.supabase_key,
        "Content-Type": "application/json",
    }


async def _supabase_post(
    path: str,
    *,
    json_body: dict[str, Any],
    settings: Settings,
    params: dict[str, str] | None = None,
) -> dict[str, Any]:
    """POST to a Supabase Auth endpoint and return the JSON response.

    Raises HTTPException on non-2xx responses.
    """
    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/{path.lstrip('/')}"
    async with httpx.AsyncClient(timeout=_SUPABASE_TIMEOUT) as client:
        resp = await client.post(
            url,
            json=json_body,
            headers=_supabase_headers(settings),
            params=params,
        )

    if resp.status_code >= 400:
        content_type = resp.headers.get("content-type", "")
        raw_detail = resp.json() if content_type.startswith("application/json") else resp.text
        # Log full error server-side for debugging
        logger.warning("Supabase auth error (%s %s): %s", resp.status_code, path, raw_detail)
        # Sanitize error detail — only forward safe, user-facing messages.
        # Never expose internal Supabase error structures to clients.
        safe_messages: dict[int, str] = {
            400: "Invalid request. Please check your input.",
            401: "Invalid credentials.",
            403: "Access denied.",
            409: "An account with this email already exists.",
            422: "Invalid request format.",
            429: "Too many requests. Please try again later.",
        }
        detail = safe_messages.get(resp.status_code, "Authentication service error.")
        raise HTTPException(
            status_code=resp.status_code,
            detail=detail,
        )

    return resp.json()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/register", response_model=SuccessResponse[AuthResponse], status_code=201)
async def register(
    body: RegisterRequest,
    settings: Settings = Depends(get_settings),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[AuthResponse]:
    """Register a new player account via Supabase Auth.

    1. Creates a Supabase Auth user (email + password).
    2. Creates a PlayerDB row in the local database.
    3. Returns access and refresh tokens.
    """
    data = await _supabase_post(
        "signup",
        json_body={"email": body.email, "password": body.password},
        settings=settings,
    )

    # Supabase returns the user object at top level for signup
    user_info: dict[str, Any] = data.get("user", data)
    supabase_uid: str = user_info.get("id", "")

    if not supabase_uid:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase signup did not return a user ID",
        )

    # Create local player profile + initial game save
    await create_player(db, supabase_user_id=supabase_uid, username=body.username)

    auth_resp = AuthResponse(
        access_token=data.get("access_token", ""),
        refresh_token=data.get("refresh_token", ""),
        token_type="bearer",
        expires_in=data.get("expires_in", 3600),
        user={
            "id": supabase_uid,
            "email": body.email,
            "username": body.username,
        },
    )
    return SuccessResponse(data=auth_resp)


@router.post("/login", response_model=SuccessResponse[AuthResponse])
async def login(
    body: LoginRequest,
    settings: Settings = Depends(get_settings),
) -> SuccessResponse[AuthResponse]:
    """Authenticate player and return JWT tokens."""
    data = await _supabase_post(
        "token",
        json_body={"email": body.email, "password": body.password},
        settings=settings,
        params={"grant_type": "password"},
    )

    user_info = data.get("user", {})
    auth_resp = AuthResponse(
        access_token=data.get("access_token", ""),
        refresh_token=data.get("refresh_token", ""),
        token_type="bearer",
        expires_in=data.get("expires_in", 3600),
        user=user_info,
    )
    return SuccessResponse(data=auth_resp)


@router.post("/refresh", response_model=SuccessResponse[AuthResponse])
async def refresh(
    body: RefreshRequest,
    settings: Settings = Depends(get_settings),
) -> SuccessResponse[AuthResponse]:
    """Refresh an expired JWT access token."""
    data = await _supabase_post(
        "token",
        json_body={"refresh_token": body.refresh_token},
        settings=settings,
        params={"grant_type": "refresh_token"},
    )

    user_info = data.get("user", {})
    auth_resp = AuthResponse(
        access_token=data.get("access_token", ""),
        refresh_token=data.get("refresh_token", ""),
        token_type="bearer",
        expires_in=data.get("expires_in", 3600),
        user=user_info,
    )
    return SuccessResponse(data=auth_resp)


@router.get("/me", response_model=SuccessResponse[dict[str, Any]])
async def me(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> SuccessResponse[dict[str, Any]]:
    """Return current user info from the verified JWT."""
    return SuccessResponse(
        data={
            "user_id": current_user.get("sub"),
            "email": current_user.get("email"),
            "role": current_user.get("role"),
        },
    )
