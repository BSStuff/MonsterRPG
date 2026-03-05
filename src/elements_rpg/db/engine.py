"""Async SQLAlchemy engine factory."""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from elements_rpg.api.config import get_settings


@lru_cache
def get_engine() -> AsyncEngine:
    """Create and cache an async SQLAlchemy engine.

    Uses the database_url from Settings (Supabase PostgreSQL).
    Format: postgresql+asyncpg://postgres:[password]@[host]:5432/postgres
    """
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_size=5,
        max_overflow=10,
    )
