"""FastAPI router for semantic product search."""
from fastapi import APIRouter, Request, status

from src.core.deps import DbDep
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
    request: Request,
    db: DbDep,
) -> SearchResponse:
    """Encode query with sentence-transformers and perform cosine similarity search."""
    from sentence_transformers import SentenceTransformer
    from src.domain.search.service import SearchService
    from src.core.config import get_settings

    settings = get_settings()

    # Re-use the model loaded at startup (stored on app.state)
    model: SentenceTransformer | None = getattr(request.app.state, "model", None)
    if model is None:
        model = SentenceTransformer(settings.embedding_model)

    return await SearchService(db, model, settings.embedding_model).search(body)
