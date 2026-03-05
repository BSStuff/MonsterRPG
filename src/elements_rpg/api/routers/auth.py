"""Authentication router — register, login, and token refresh endpoints."""

from http import HTTPStatus

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def register() -> JSONResponse:
    """Register a new player account via Supabase Auth."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Register new player account"},
    )


@router.post("/login", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def login() -> JSONResponse:
    """Authenticate player and return JWT tokens."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Login with credentials"},
    )


@router.post("/refresh", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def refresh() -> JSONResponse:
    """Refresh an expired JWT access token."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Refresh JWT token"},
    )
