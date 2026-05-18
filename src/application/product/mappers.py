"""Map persistence records to API response DTOs."""
from typing import Any

from src.domain.product.schemas import BrandBasic, CategoryBasic, ProductResponse


def to_product_response(p: Any) -> ProductResponse:
    """Convert a Prisma Product record to ProductResponse."""
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
