"""Product repository port (infrastructure implements this)."""
from typing import Any, Optional, Protocol

from src.domain.product.schemas import ProductFilters


class ProductRepository(Protocol):
    """Persistence port for product aggregate CRUD."""

    async def create(self, data: dict[str, Any]) -> Any:
        """Create a product. Raises ConflictError on duplicate SKU."""

    async def find_by_id(self, product_id: str) -> Optional[Any]:
        """Return product with category/brand includes, or None."""

    async def find_by_sku(self, sku: str) -> Optional[Any]:
        """Return product with category/brand includes, or None."""

    async def find_many(self, filters: ProductFilters) -> tuple[list[Any], int]:
        """Return (products, total_count) for paginated listing."""

    async def update(self, product_id: str, data: dict[str, Any]) -> Any:
        """Update product. Raises ConflictError on duplicate SKU."""

    async def delete(self, product_id: str) -> None:
        """Delete product by ID."""
