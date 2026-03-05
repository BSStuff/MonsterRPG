"""Supabase JWT verification and user authentication."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from elements_rpg.api.config import Settings, get_settings

logger = logging.getLogger(__name__)

security = HTTPBearer()


def _decode_supabase_jwt(token: str, settings: Settings) -> dict[str, Any]:
    """Decode and verify a Supabase JWT token.

    Args:
        token: Raw JWT string from the Authorization header.
        settings: Application settings containing the JWT secret.

    Returns:
        Decoded JWT payload dictionary.

    Raises:
        HTTPException: If token is invalid, expired, or has wrong audience.
    """
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except JWTError as e:
        logger.warning("JWT verification failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """FastAPI dependency: extract and verify the current user from JWT.

    Returns the decoded JWT payload containing at minimum:
        - sub: Supabase user ID
        - email: User email
        - role: "authenticated"
    """
    payload = _decode_supabase_jwt(credentials.credentials, settings)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user ID",
        )
    return payload
