"""Shared pytest fixtures for all layers."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.application.product.service import ProductService
from src.application.search.service import SearchService
from src.core.deps import get_product_service, get_search_service
from src.domain.product.schemas import ProductCreate, ProductResponse
from src.main import create_app


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def product_record() -> SimpleNamespace:
    """Minimal Prisma-like product record for mapper/service tests."""
    now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    return SimpleNamespace(
        id="prod-abc123",
        sku="TEST-SKU-001",
        name="Test Product",
        description="A test product description",
        price=Decimal("99.99"),
        compareAtPrice=None,
        costPrice=None,
        categoryId="cat-001",
        subCategoryId=None,
        brandId="brand-001",
        stockQty=10,
        lowStockThreshold=5,
        weight=None,
        weightUnit="kg",
        width=None,
        height=None,
        depth=None,
        dimensionUnit="cm",
        tags=["test", "sample"],
        imageUrls=[],
        status=SimpleNamespace(value="ACTIVE"),
        isDigital=False,
        isFeatured=False,
        metaTitle=None,
        metaDescription=None,
        createdAt=now,
        updatedAt=now,
        category=SimpleNamespace(id="cat-001", name="Electronics", slug="electronics"),
        brand=SimpleNamespace(id="brand-001", name="Apple", slug="apple"),
    )


@pytest.fixture
def search_row() -> dict[str, Any]:
    """Raw SQL row dict for search mapper tests."""
    return {
        "id": "prod-abc123",
        "sku": "TEST-SKU-001",
        "name": "Test Product",
        "description": "A test product description",
        "price": Decimal("99.99"),
        "compareAtPrice": None,
        "costPrice": None,
        "categoryId": "cat-001",
        "subCategoryId": None,
        "brandId": "brand-001",
        "stockQty": 10,
        "lowStockThreshold": 5,
        "weight": None,
        "weightUnit": "kg",
        "width": None,
        "height": None,
        "depth": None,
        "dimensionUnit": "cm",
        "tags": ["test"],
        "imageUrls": [],
        "status": "ACTIVE",
        "isDigital": False,
        "isFeatured": False,
        "metaTitle": None,
        "metaDescription": None,
        "createdAt": "2026-01-15T12:00:00+00:00",
        "updatedAt": "2026-01-15T12:00:00+00:00",
        "brand_name": "Apple",
        "brand_slug": "apple",
        "category_name": "Electronics",
        "category_slug": "electronics",
        "similarity_score": 0.87,
    }


@pytest.fixture
def product_create() -> ProductCreate:
    return ProductCreate(
        sku="NEW-SKU-001",
        name="New Product",
        description="Brand new",
        price=Decimal("49.99"),
        status="ACTIVE",
        tags=["new"],
    )


@pytest.fixture
def mock_product_repository(product_record: SimpleNamespace) -> MagicMock:
    repo = MagicMock()
    repo.create = AsyncMock(return_value=product_record)
    repo.find_by_id = AsyncMock(return_value=product_record)
    repo.find_by_sku = AsyncMock(return_value=product_record)
    repo.find_many = AsyncMock(return_value=([product_record], 1))
    repo.update = AsyncMock(return_value=product_record)
    repo.delete = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_search_repository(search_row: dict[str, Any]) -> MagicMock:
    repo = MagicMock()
    repo.search_by_vector = AsyncMock(return_value=[search_row])
    return repo


@pytest.fixture
def mock_encoder() -> MagicMock:
    encoder = MagicMock()
    encoder.encode = MagicMock(return_value=[0.1, 0.2, 0.3])
    return encoder


@pytest.fixture
def product_service(mock_product_repository: MagicMock) -> ProductService:
    return ProductService(mock_product_repository)


@pytest.fixture
def search_service(
    mock_search_repository: MagicMock, mock_encoder: MagicMock
) -> SearchService:
    return SearchService(mock_search_repository, mock_encoder, "test-model")


@pytest.fixture
def test_app(
    product_service: ProductService,
    search_service: SearchService,
    monkeypatch: pytest.MonkeyPatch,
) -> Any:
    """FastAPI app with mocked lifespan (no real DB/model/worker)."""
    monkeypatch.setattr("src.main.connect_db", AsyncMock())
    monkeypatch.setattr("src.main.disconnect_db", AsyncMock())

    mock_model = MagicMock()
    monkeypatch.setattr(
        "sentence_transformers.SentenceTransformer", lambda *_a, **_k: mock_model
    )

    worker_instance = MagicMock()
    worker_instance.start = AsyncMock()
    worker_instance.stop = AsyncMock()
    mock_worker_cls = MagicMock(return_value=worker_instance)
    monkeypatch.setattr(
        "src.infrastructure.workers.embedding_worker.EmbeddingWorker", mock_worker_cls
    )

    async def _noop_keepalive(_worker: object) -> None:
        return None

    monkeypatch.setattr("src.main._keep_worker_alive", _noop_keepalive)

    application = create_app()
    application.dependency_overrides[get_product_service] = lambda: product_service
    application.dependency_overrides[get_search_service] = lambda: search_service
    yield application
    application.dependency_overrides.clear()


@pytest.fixture
def client(test_app: Any) -> TestClient:
    with TestClient(test_app) as test_client:
        yield test_client
