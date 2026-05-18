"""Search bounded-context ports."""
from typing import Any, Protocol

from src.domain.search.schemas import SearchRequest


class VectorSearchRepository(Protocol):
    """Persistence port for pgvector semantic search."""

    async def search_by_vector(
        self, vector_str: str, request: SearchRequest
    ) -> list[dict[str, Any]]:
        """Run cosine similarity query; return raw row dicts."""


class EmbeddingEncoder(Protocol):
    """Port for encoding text into a normalized embedding vector."""

    def encode(self, text: str) -> list[float]:
        """Encode text to a float vector."""
