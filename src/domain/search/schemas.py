"""Pydantic v2 schemas for semantic search endpoints."""
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from src.domain.product.schemas import ProductResponse


class SearchFilters(BaseModel):
    """Optional filters to narrow the vector search space."""

    status: str = Field(default="ACTIVE", pattern="^(ACTIVE|INACTIVE|DRAFT|DISCONTINUED)$")
    category_id: Optional[str] = None
    brand_id: Optional[str] = None
    is_featured: Optional[bool] = None
    min_price: Optional[Decimal] = Field(None, ge=Decimal("0"))
    max_price: Optional[Decimal] = Field(None, ge=Decimal("0"))


class SearchRequest(BaseModel):
    """Request body for semantic product search."""

    query: str = Field(..., min_length=1, max_length=1000, description="Natural language query")
    limit: int = Field(default=10, ge=1, le=100)
    threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="Min cosine similarity")
    filters: SearchFilters = Field(default_factory=SearchFilters)


class SearchResult(ProductResponse):
    """Product with an additional similarity score from vector search."""

    similarity_score: float = Field(..., description="Cosine similarity (0–1)")


class SearchResponse(BaseModel):
    """Response from semantic search endpoint."""

    query: str
    results: list[SearchResult]
    total: int
    limit: int
    embedding_model: str
