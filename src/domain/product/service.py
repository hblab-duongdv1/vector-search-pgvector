"""Product business logic service — all CRUD operations."""
import logging
from decimal import Decimal
from typing import Any, Optional

from fastapi import HTTPException, status
from prisma import Prisma
from prisma.errors import UniqueViolationError

from src.domain.product.schemas import (
    CategoryBasic,
    BrandBasic,
    ProductCreate,
    ProductFilters,
    ProductResponse,
    ProductUpdate,
)

logger = logging.getLogger(__name__)


def _to_response(p: Any) -> ProductResponse:
    """Convert a Prisma Product model to ProductResponse."""
    category = None
    if getattr(p, "category", None):
        category = CategoryBasic(id=p.category.id, name=p.category.name, slug=p.category.slug)
    brand = None
    if getattr(p, "brand", None):
        brand = BrandBasic(id=p.brand.id, name=p.brand.name, slug=p.brand.slug)

    return ProductResponse(
        id=p.id,
        sku=p.sku,
        name=p.name,
        description=p.description,
        price=p.price,
        compare_at_price=p.compareAtPrice,
        cost_price=p.costPrice,
        category_id=p.categoryId,
        sub_category_id=p.subCategoryId,
        brand_id=p.brandId,
        stock_qty=p.stockQty,
        low_stock_threshold=p.lowStockThreshold,
        weight=p.weight,
        weight_unit=p.weightUnit,
        width=p.width,
        height=p.height,
        depth=p.depth,
        dimension_unit=p.dimensionUnit,
        tags=p.tags,
        image_urls=p.imageUrls,
        status=p.status.value if hasattr(p.status, "value") else str(p.status),
        is_digital=p.isDigital,
        is_featured=p.isFeatured,
        meta_title=p.metaTitle,
        meta_description=p.metaDescription,
        created_at=p.createdAt.isoformat(),
        updated_at=p.updatedAt.isoformat(),
        category=category,
        brand=brand,
    )


class ProductService:
    """Handles all product CRUD business logic using Prisma."""

    def __init__(self, db: Prisma) -> None:
        self.db = db

    async def create(self, data: ProductCreate) -> ProductResponse:
        """Create a new product. Raises 409 on duplicate SKU."""
        logger.info("Creating product sku=%s", data.sku)
        try:
            product = await self.db.product.create(
                data={
                    "sku": data.sku,
                    "name": data.name,
                    "description": data.description,
                    "price": data.price,
                    "compareAtPrice": data.compare_at_price,
                    "costPrice": data.cost_price,
                    "categoryId": data.category_id,
                    "subCategoryId": data.sub_category_id,
                    "brandId": data.brand_id,
                    "stockQty": data.stock_qty,
                    "lowStockThreshold": data.low_stock_threshold,
                    "weight": data.weight,
                    "weightUnit": data.weight_unit,
                    "width": data.width,
                    "height": data.height,
                    "depth": data.depth,
                    "dimensionUnit": data.dimension_unit,
                    "tags": data.tags,
                    "imageUrls": data.image_urls,
                    "status": data.status,
                    "isDigital": data.is_digital,
                    "isFeatured": data.is_featured,
                    "metaTitle": data.meta_title,
                    "metaDescription": data.meta_description,
                },
                include={"category": True, "brand": True},
            )
        except UniqueViolationError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with SKU '{data.sku}' already exists",
            )
        logger.info("Product created id=%s sku=%s", product.id, product.sku)
        return _to_response(product)

    async def get_by_id(self, product_id: str) -> ProductResponse:
        """Get a product by ID. Raises 404 if not found."""
        product = await self.db.product.find_unique(
            where={"id": product_id},
            include={"category": True, "brand": True},
        )
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        return _to_response(product)

    async def get_by_sku(self, sku: str) -> ProductResponse:
        """Get a product by SKU. Raises 404 if not found."""
        product = await self.db.product.find_unique(
            where={"sku": sku},
            include={"category": True, "brand": True},
        )
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        return _to_response(product)

    async def list(
        self, filters: ProductFilters
    ) -> tuple[list[ProductResponse], int]:
        """Return paginated products with optional filters."""
        where: Any = {}
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

        total = await self.db.product.count(where=where)
        products = await self.db.product.find_many(
            where=where,
            include={"category": True, "brand": True},
            skip=filters.offset,
            take=filters.limit,
            order={"createdAt": "desc"},
        )
        return [_to_response(p) for p in products], total

    async def update(self, product_id: str, data: ProductUpdate) -> ProductResponse:
        """Update a product. Raises 404 or 409."""
        existing = await self.db.product.find_unique(where={"id": product_id})
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )

        update_data = {
            k: v for k, v in {
                "sku": data.sku,
                "name": data.name,
                "description": data.description,
                "price": data.price,
                "compareAtPrice": data.compare_at_price,
                "costPrice": data.cost_price,
                "categoryId": data.category_id,
                "subCategoryId": data.sub_category_id,
                "brandId": data.brand_id,
                "stockQty": data.stock_qty,
                "lowStockThreshold": data.low_stock_threshold,
                "weight": data.weight,
                "weightUnit": data.weight_unit,
                "width": data.width,
                "height": data.height,
                "depth": data.depth,
                "dimensionUnit": data.dimension_unit,
                "tags": data.tags,
                "imageUrls": data.image_urls,
                "status": data.status,
                "isDigital": data.is_digital,
                "isFeatured": data.is_featured,
                "metaTitle": data.meta_title,
                "metaDescription": data.meta_description,
            }.items()
            if v is not None
        }

        if not update_data:
            return _to_response(existing)

        logger.info("Updating product id=%s", product_id)
        try:
            product = await self.db.product.update(
                where={"id": product_id},
                data=update_data,  # type: ignore[arg-type]
                include={"category": True, "brand": True},
            )
        except UniqueViolationError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with SKU '{data.sku}' already exists",
            )
        return _to_response(product)

    async def delete(self, product_id: str) -> None:
        """Delete a product. Raises 404 if not found."""
        existing = await self.db.product.find_unique(where={"id": product_id})
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        await self.db.product.delete(where={"id": product_id})
        logger.info("Product deleted id=%s", product_id)
