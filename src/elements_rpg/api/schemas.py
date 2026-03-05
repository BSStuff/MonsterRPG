"""Shared API request/response schemas for ElementsRPG."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success envelope."""

    success: bool = True
    data: T
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class ErrorDetail(BaseModel):
    """Error detail object."""

    code: str
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    success: bool = False
    error: ErrorDetail


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    success: bool = True
    data: list[T]
    total: int
    page: int = 1
    page_size: int = 50
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class PaginationParams(BaseModel):
    """Common pagination query parameters."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
