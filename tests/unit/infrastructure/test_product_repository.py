"""Infrastructure: Prisma product repository."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from prisma.errors import UniqueViolationError

from src.domain.product.schemas import ProductFilters
from src.domain.shared.exceptions import ConflictError
from src.infrastructure.database.repositories.product import PrismaProductRepository


@pytest.fixture
def prisma() -> MagicMock:
    db = MagicMock()
    db.product = MagicMock()
    db.product.create = AsyncMock()
    db.product.find_unique = AsyncMock()
    db.product.find_many = AsyncMock(return_value=[])
    db.product.count = AsyncMock(return_value=0)
    db.product.update = AsyncMock()
    db.product.delete = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_create_success(prisma: MagicMock) -> None:
    prisma.product.create.return_value = {"id": "p1"}
    repo = PrismaProductRepository(prisma)
    result = await repo.create({"sku": "A-1", "name": "A"})
    assert result["id"] == "p1"
    prisma.product.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_raises_conflict_on_duplicate_sku(prisma: MagicMock) -> None:
    prisma.product.create.side_effect = UniqueViolationError({})
    repo = PrismaProductRepository(prisma)
    with pytest.raises(ConflictError, match="SKU 'DUP-1'"):
        await repo.create({"sku": "DUP-1"})


@pytest.mark.asyncio
async def test_find_by_id(prisma: MagicMock) -> None:
    prisma.product.find_unique.return_value = {"id": "p1"}
    repo = PrismaProductRepository(prisma)
    result = await repo.find_by_id("p1")
    assert result["id"] == "p1"


@pytest.mark.asyncio
async def test_find_many_builds_where_clause(prisma: MagicMock) -> None:
    prisma.product.count.return_value = 2
    prisma.product.find_many.return_value = [{"id": "p1"}, {"id": "p2"}]
    repo = PrismaProductRepository(prisma)
    filters = ProductFilters(status="ACTIVE", brand_id="b1", min_price=10, max_price=100)
    products, total = await repo.find_many(filters)
    assert len(products) == 2
    assert total == 2
    where = prisma.product.find_many.await_args.kwargs["where"]
    assert where["status"] == "ACTIVE"
    assert where["brandId"] == "b1"
    assert where["price"]["gte"] == 10
    assert where["price"]["lte"] == 100


@pytest.mark.asyncio
async def test_update_raises_conflict(prisma: MagicMock) -> None:
    prisma.product.update.side_effect = UniqueViolationError({})
    repo = PrismaProductRepository(prisma)
    with pytest.raises(ConflictError):
        await repo.update("p1", {"sku": "X"})


@pytest.mark.asyncio
async def test_delete(prisma: MagicMock) -> None:
    repo = PrismaProductRepository(prisma)
    await repo.delete("p1")
    prisma.product.delete.assert_awaited_once_with(where={"id": "p1"})
