"""Map search query rows to SearchResult DTOs."""
from typing import Any

from src.domain.product.schemas import BrandBasic, CategoryBasic
from src.domain.search.schemas import SearchResult


def to_search_result(row: dict[str, Any]) -> SearchResult:
    """Convert a raw SQL row to SearchResult."""
    brand = None
    if row.get("brandId"):
        brand = BrandBasic(
            id=row["brandId"],
            name=row.get("brand_name") or "",
            slug=row.get("brand_slug") or "",
        )
    category = None
    if row.get("categoryId"):
        category = CategoryBasic(
            id=row["categoryId"],
            name=row.get("category_name") or "",
            slug=row.get("category_slug") or "",
        )

    return SearchResult(
        id=row["id"],
        sku=row["sku"],
        name=row["name"],
        description=row.get("description"),
        price=row["price"],
        compare_at_price=row.get("compareAtPrice"),
        cost_price=row.get("costPrice"),
        category_id=row.get("categoryId"),
        sub_category_id=row.get("subCategoryId"),
        brand_id=row.get("brandId"),
        stock_qty=row.get("stockQty", 0),
        low_stock_threshold=row.get("lowStockThreshold", 5),
        weight=row.get("weight"),
        weight_unit=row.get("weightUnit", "kg"),
        width=row.get("width"),
        height=row.get("height"),
        depth=row.get("depth"),
        dimension_unit=row.get("dimensionUnit", "cm"),
        tags=row.get("tags") or [],
        image_urls=row.get("imageUrls") or [],
        status=str(row.get("status", "ACTIVE")),
        is_digital=row.get("isDigital", False),
        is_featured=row.get("isFeatured", False),
        meta_title=row.get("metaTitle"),
        meta_description=row.get("metaDescription"),
        created_at=str(row.get("createdAt", "")),
        updated_at=str(row.get("updatedAt", "")),
        brand=brand,
        category=category,
        similarity_score=float(row.get("similarity_score", 0)),
    )
