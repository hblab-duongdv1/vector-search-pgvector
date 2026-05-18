"""FastAPI dependency injection — wires ports to application services."""
from typing import Annotated, Any

from fastapi import Depends, Request

from src.application.product.service import ProductService
from src.application.search.service import SearchService
from src.core.config import Settings, get_settings
from src.infrastructure.database.client import get_prisma
from src.infrastructure.database.repositories.product import PrismaProductRepository
from src.infrastructure.database.repositories.search import PrismaVectorSearchRepository
from prisma import Prisma


def get_db() -> Prisma:
    return get_prisma()


def get_embedding_model(request: Request) -> Any:
    from sentence_transformers import SentenceTransformer

    model = getattr(request.app.state, "model", None)
    if model is None:
        settings = get_settings()
        model = SentenceTransformer(settings.embedding_model)
    return model


def get_product_service(db: Annotated[Prisma, Depends(get_db)]) -> ProductService:
    return ProductService(PrismaProductRepository(db))


def get_search_service(
    db: Annotated[Prisma, Depends(get_db)],
    model: Annotated[Any, Depends(get_embedding_model)],
) -> SearchService:
    from src.infrastructure.ml.embedding_encoder import SentenceTransformerEncoder

    settings = get_settings()
    encoder = SentenceTransformerEncoder(model)
    return SearchService(
        PrismaVectorSearchRepository(db),
        encoder,
        settings.embedding_model,
    )


SettingsDep = Annotated[Settings, Depends(get_settings)]
DbDep = Annotated[Prisma, Depends(get_db)]
ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]
SearchServiceDep = Annotated[SearchService, Depends(get_search_service)]
