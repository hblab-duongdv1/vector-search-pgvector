"""Common Pydantic v2 response models shared across the API."""
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated list response."""

    items: list[T]
    total: int
    limit: int
    offset: int


class ErrorResponse(BaseModel):
    """Standard error response body."""

    detail: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    database: str
    embedding_worker: str
    version: str
