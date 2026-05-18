"""Search application service — semantic search use case."""
import asyncio
import logging

from src.application.search.mappers import to_search_result
from src.domain.search.ports import EmbeddingEncoder, VectorSearchRepository
from src.domain.search.schemas import SearchRequest, SearchResponse, SearchResult

logger = logging.getLogger(__name__)


class SearchService:
    """Semantic product search use case."""

    def __init__(
        self,
        repository: VectorSearchRepository,
        encoder: EmbeddingEncoder,
        model_name: str,
    ) -> None:
        self._repo = repository
        self._encoder = encoder
        self._model_name = model_name

    async def search(self, request: SearchRequest) -> SearchResponse:
        logger.info(
            "Semantic search: query='%s' limit=%d threshold=%.2f",
            request.query,
            request.limit,
            request.threshold,
        )

        loop = asyncio.get_event_loop()
        vector = await loop.run_in_executor(
            None, lambda: self._encoder.encode(request.query)
        )

        vector_str = "[" + ",".join(str(v) for v in vector) + "]"
        rows = await self._repo.search_by_vector(vector_str, request)
        results: list[SearchResult] = [to_search_result(row) for row in rows]

        logger.info("Search returned %d results for query='%s'", len(results), request.query)
        return SearchResponse(
            query=request.query,
            results=results,
            total=len(results),
            limit=request.limit,
            embedding_model=self._model_name,
        )
