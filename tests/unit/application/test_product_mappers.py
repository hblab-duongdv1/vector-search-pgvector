"""Application: product response mappers."""
from datetime import datetime, timezone
from types import SimpleNamespace

from src.application.product.mappers import to_product_response


def test_to_product_response_maps_prisma_record(product_record: SimpleNamespace) -> None:
    response = to_product_response(product_record)
    assert response.id == "prod-abc123"
    assert response.sku == "TEST-SKU-001"
    assert response.status == "ACTIVE"
    assert response.category is not None
    assert response.category.name == "Electronics"
    assert response.brand is not None
    assert response.brand.slug == "apple"


def test_to_product_response_without_relations() -> None:
    record = SimpleNamespace(
        id="p1",
        sku="S1",
        name="Solo",
        description=None,
        price=10,
        compareAtPrice=None,
        costPrice=None,
        categoryId=None,
        subCategoryId=None,
        brandId=None,
        stockQty=0,
        lowStockThreshold=5,
        weight=None,
        weightUnit="kg",
        width=None,
        height=None,
        depth=None,
        dimensionUnit="cm",
        tags=[],
        imageUrls=[],
        status="DRAFT",
        isDigital=False,
        isFeatured=False,
        metaTitle=None,
        metaDescription=None,
        createdAt=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updatedAt=datetime(2026, 1, 1, tzinfo=timezone.utc),
        category=None,
        brand=None,
    )
    response = to_product_response(record)
    assert response.category is None
    assert response.brand is None
    assert response.status == "DRAFT"
