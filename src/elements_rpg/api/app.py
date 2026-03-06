"""FastAPI application factory for ElementsRPG."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from elements_rpg.api.config import get_settings
from elements_rpg.api.routers import ALL_ROUTERS

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns a fully configured FastAPI instance with:
        - CORS middleware from settings (restrictive origins)
        - All available domain routers (including health check)
        - Global exception handlers (no stack traces in production)
        - Startup validation for required settings
        - Docs disabled in production
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "ElementsRPG Backend API -- hybrid active/idle monster survival RPG "
            "with monster collection, skill progression, and convenience monetization."
        ),
        # Disable debug mode in production to prevent stack trace leaks
        debug=settings.debug,
        # Disable docs in production for security
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    _register_cors(app)
    _register_exception_handlers(app)
    _register_routers(app)
    _register_startup_events(app)

    return app


# ---------------------------------------------------------------------------
# Startup events
# ---------------------------------------------------------------------------


def _register_startup_events(app: FastAPI) -> None:
    """Register startup events to validate configuration."""

    @app.on_event("startup")
    async def validate_settings() -> None:
        """Validate required settings and log warnings for missing ones."""
        settings = get_settings()
        missing = settings.validate_required_for_production()
        if missing:
            for var_name in missing:
                logger.warning(
                    "Required setting %s is not configured. This will cause errors in production.",
                    var_name,
                )
            if not settings.debug:
                logger.error(
                    "Missing required settings in production mode: %s",
                    ", ".join(missing),
                )


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------


def _register_cors(app: FastAPI) -> None:
    """Add CORS middleware configured from settings.

    Origins are restricted to configured values (never wildcard "*" in production).
    Methods and headers are limited to what the API actually uses.
    """
    settings = get_settings()

    if "*" in settings.cors_origins:
        logger.warning(
            "CORS allow_origins contains '*' — this is insecure for production. "
            "Set ELEMENTS_CORS_ORIGINS to specific domains."
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
    )


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


def _register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers that return structured JSON."""

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        logger.warning("ValueError on %s %s: %s", request.method, request.url.path, exc)
        return JSONResponse(
            status_code=400,
            content=_error_body("bad_request", "Invalid request"),
        )

    @app.exception_handler(PermissionError)
    async def permission_error_handler(request: Request, exc: PermissionError) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content=_error_body("forbidden", str(exc)),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content=_error_body(
                "internal_error",
                "An unexpected error occurred. Please try again later.",
            ),
        )


def _error_body(code: str, message: str) -> dict[str, Any]:
    """Build a consistent error response envelope."""
    return {
        "error": {
            "code": code,
            "message": message,
            "timestamp": datetime.now(UTC).isoformat(),
        },
    }


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------


def _register_routers(app: FastAPI) -> None:
    """Include all domain routers from the routers package.

    Each router defines its own prefix and tags via APIRouter(),
    so no additional prefix/tag overrides are needed here.
    """
    for router in ALL_ROUTERS:
        app.include_router(router)

    logger.info("Registered %d domain routers", len(ALL_ROUTERS))
