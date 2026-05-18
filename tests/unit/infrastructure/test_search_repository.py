"""Infrastructure: Prisma vector search repository."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.search.schemas import SearchFilters, SearchRequest
from src.infrastructure.database.repositories.search import PrismaVectorSearchRepository


@pytest.fixture
def prisma() -> MagicMock:
    db = MagicMock()
    db.query_raw = AsyncMock(return_value=[{"id": "p1", "sku": "S1", "similarity_score": 0.9}])
    return db


@pytest.mark.asyncio
async def test_search_without_status_filter_uses_true_where(prisma: MagicMock) -> None:
    repo = PrismaVectorSearchRepository(prisma)
    request = SearchRequest(query="jacket", limit=3)
    rows = await repo.search_by_vector("[0.1,0.2]", request)

    assert len(rows) == 1
    sql = prisma.query_raw.await_args[0][0]
    assert "WHERE TRUE" in sql
    params = prisma.query_raw.await_args[0][1:]
    assert params[0] == "[0.1,0.2]"
    assert params[1] == 3


@pytest.mark.asyncio
async def test_search_with_status_filter(prisma: MagicMock) -> None:
    repo = PrismaVectorSearchRepository(prisma)
    request = SearchRequest(
        query="inactive",
        limit=5,
        filters=SearchFilters(status="INACTIVE"),
    )
    await repo.search_by_vector("[0.1]", request)

    sql = prisma.query_raw.await_args[0][0]
    assert 'p.status = $3::"ProductStatus"' in sql
    params = prisma.query_raw.await_args[0][1:]
    assert params[2] == "INACTIVE"


@pytest.mark.asyncio
async def test_search_with_threshold_and_price_filters(prisma: MagicMock) -> None:
    repo = PrismaVectorSearchRepository(prisma)
    request = SearchRequest(
        query="shoes",
        limit=10,
        threshold=0.5,
        filters=SearchFilters(min_price=50, max_price=200, is_featured=True),
    )
    await repo.search_by_vector("[0.1]", request)

    sql = prisma.query_raw.await_args[0][0]
    assert "pe.embedding <=> $1::vector" in sql
    assert "p.price >=" in sql
    assert "p.price <=" in sql
    assert '"isFeatured"' in sql
