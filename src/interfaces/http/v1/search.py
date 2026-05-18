"""HTTP adapter: semantic product search."""
from fastapi import APIRouter, status

from src.core.deps import SearchServiceDep
from src.domain.search.schemas import SearchRequest, SearchResponse

router = APIRouter(tags=["Search"])


@router.post(
    "/products/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic product search",
    description=(
        "Search products using natural language. "
        "Returns top-K results ordered by cosine similarity (pgvector)."
    ),
)
async def search_products(
    body: SearchRequest,
    service: SearchServiceDep,
) -> SearchResponse:
    return await service.search(body)
