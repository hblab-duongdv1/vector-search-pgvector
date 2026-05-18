"""Product application service — orchestrates use cases via repository port."""
import logging
from typing import Any

from src.application.product.mappers import to_product_response
from src.domain.product.repository import ProductRepository
from src.domain.product.schemas import (
    ProductCreate,
    ProductFilters,
    ProductResponse,
    ProductUpdate,
)
from src.domain.shared.exceptions import ConflictError, NotFoundError

logger = logging.getLogger(__name__)


class ProductService:
    """Product CRUD use cases."""

    def __init__(self, repository: ProductRepository) -> None:
        self._repo = repository

    async def create(self, data: ProductCreate) -> ProductResponse:
        logger.info("Creating product sku=%s", data.sku)
        try:
            product = await self._repo.create(self._create_payload(data))
        except ConflictError:
            raise
        logger.info("Product created id=%s sku=%s", product.id, product.sku)
        return to_product_response(product)

    async def get_by_id(self, product_id: str) -> ProductResponse:
        product = await self._repo.find_by_id(product_id)
        if not product:
            raise NotFoundError("Product", product_id)
        return to_product_response(product)

    async def get_by_sku(self, sku: str) -> ProductResponse:
        product = await self._repo.find_by_sku(sku)
        if not product:
            raise NotFoundError("Product", sku)
        return to_product_response(product)

    async def list(self, filters: ProductFilters) -> tuple[list[ProductResponse], int]:
        products, total = await self._repo.find_many(filters)
        return [to_product_response(p) for p in products], total

    async def update(self, product_id: str, data: ProductUpdate) -> ProductResponse:
        existing = await self._repo.find_by_id(product_id)
        if not existing:
            raise NotFoundError("Product", product_id)

        update_data = self._update_payload(data)
        if not update_data:
            return to_product_response(existing)

        logger.info("Updating product id=%s", product_id)
        try:
            product = await self._repo.update(product_id, update_data)
        except ConflictError:
            raise
        return to_product_response(product)

    async def delete(self, product_id: str) -> None:
        existing = await self._repo.find_by_id(product_id)
        if not existing:
            raise NotFoundError("Product", product_id)
        await self._repo.delete(product_id)
        logger.info("Product deleted id=%s", product_id)

    @staticmethod
    def _create_payload(data: ProductCreate) -> dict[str, Any]:
        return {
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
        }

    @staticmethod
    def _update_payload(data: ProductUpdate) -> dict[str, Any]:
        return {
            k: v
            for k, v in {
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
