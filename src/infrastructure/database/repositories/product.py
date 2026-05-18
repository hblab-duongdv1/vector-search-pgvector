"""Prisma implementation of ProductRepository."""
from typing import Any

from prisma import Prisma
from prisma.errors import UniqueViolationError

from src.domain.product.repository import ProductRepository
from src.domain.product.schemas import ProductFilters
from src.domain.shared.exceptions import ConflictError


class PrismaProductRepository:
    """Product persistence via Prisma ORM."""

    def __init__(self, db: Prisma) -> None:
        self._db = db

    async def create(self, data: dict[str, Any]) -> Any:
        try:
            return await self._db.product.create(
                data=data,
                include={"category": True, "brand": True},
            )
        except UniqueViolationError as exc:
            sku = data.get("sku", "")
            raise ConflictError(f"Product with SKU '{sku}' already exists") from exc

    async def find_by_id(self, product_id: str) -> Any | None:
        return await self._db.product.find_unique(
            where={"id": product_id},
            include={"category": True, "brand": True},
        )

    async def find_by_sku(self, sku: str) -> Any | None:
        return await self._db.product.find_unique(
            where={"sku": sku},
            include={"category": True, "brand": True},
        )

    async def find_many(self, filters: ProductFilters) -> tuple[list[Any], int]:
        where: dict[str, Any] = {}
        if filters.status:
            where["status"] = filters.status
        if filters.category_id:
            where["categoryId"] = filters.category_id
        if filters.brand_id:
            where["brandId"] = filters.brand_id
        if filters.is_featured is not None:
            where["isFeatured"] = filters.is_featured
        if filters.min_price is not None or filters.max_price is not None:
            price_filter: dict[str, Any] = {}
            if filters.min_price is not None:
                price_filter["gte"] = filters.min_price
            if filters.max_price is not None:
                price_filter["lte"] = filters.max_price
            where["price"] = price_filter

        total = await self._db.product.count(where=where)
        products = await self._db.product.find_many(
            where=where,
            include={"category": True, "brand": True},
            skip=filters.offset,
            take=filters.limit,
            order={"createdAt": "desc"},
        )
        return products, total

    async def update(self, product_id: str, data: dict[str, Any]) -> Any:
        try:
            return await self._db.product.update(
                where={"id": product_id},
                data=data,  # type: ignore[arg-type]
                include={"category": True, "brand": True},
            )
        except UniqueViolationError as exc:
            sku = data.get("sku", "")
            raise ConflictError(f"Product with SKU '{sku}' already exists") from exc

    async def delete(self, product_id: str) -> None:
        await self._db.product.delete(where={"id": product_id})
