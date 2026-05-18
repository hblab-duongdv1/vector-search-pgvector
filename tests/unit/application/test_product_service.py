"""Application: ProductService use cases."""
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.product.service import ProductService
from src.domain.product.schemas import ProductCreate, ProductFilters, ProductUpdate
from src.domain.shared.exceptions import ConflictError, NotFoundError


@pytest.mark.asyncio
async def test_create_returns_product_response(
    product_service: ProductService, mock_product_repository: MagicMock, product_create: ProductCreate
) -> None:
    result = await product_service.create(product_create)
    assert result.sku == "TEST-SKU-001"
    mock_product_repository.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_propagates_conflict(
    mock_product_repository: MagicMock, product_create: ProductCreate
) -> None:
    mock_product_repository.create.side_effect = ConflictError("duplicate")
    service = ProductService(mock_product_repository)
    with pytest.raises(ConflictError):
        await service.create(product_create)


@pytest.mark.asyncio
async def test_get_by_id_not_found(mock_product_repository: MagicMock) -> None:
    mock_product_repository.find_by_id.return_value = None
    service = ProductService(mock_product_repository)
    with pytest.raises(NotFoundError):
        await service.get_by_id("missing-id")


@pytest.mark.asyncio
async def test_get_by_sku_success(product_service: ProductService) -> None:
    result = await product_service.get_by_sku("TEST-SKU-001")
    assert result.id == "prod-abc123"


@pytest.mark.asyncio
async def test_list_returns_items_and_total(product_service: ProductService) -> None:
    items, total = await product_service.list(ProductFilters())
    assert len(items) == 1
    assert total == 1


@pytest.mark.asyncio
async def test_update_not_found(mock_product_repository: MagicMock) -> None:
    mock_product_repository.find_by_id.return_value = None
    service = ProductService(mock_product_repository)
    with pytest.raises(NotFoundError):
        await service.update("missing", ProductUpdate(name="X"))


@pytest.mark.asyncio
async def test_update_empty_payload_returns_existing(
    product_service: ProductService, mock_product_repository: MagicMock, product_record: SimpleNamespace
) -> None:
    result = await product_service.update(product_record.id, ProductUpdate())
    assert result.sku == product_record.sku
    mock_product_repository.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_applies_changes(
    product_service: ProductService, mock_product_repository: MagicMock
) -> None:
    await product_service.update("prod-abc123", ProductUpdate(name="Updated Name"))
    mock_product_repository.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_not_found(mock_product_repository: MagicMock) -> None:
    mock_product_repository.find_by_id.return_value = None
    service = ProductService(mock_product_repository)
    with pytest.raises(NotFoundError):
        await service.delete("missing")


@pytest.mark.asyncio
async def test_delete_success(
    product_service: ProductService, mock_product_repository: MagicMock
) -> None:
    await product_service.delete("prod-abc123")
    mock_product_repository.delete.assert_awaited_once_with("prod-abc123")


def test_create_payload_maps_camel_case_fields(product_create: ProductCreate) -> None:
    payload = ProductService._create_payload(product_create)
    assert payload["sku"] == "NEW-SKU-001"
    assert payload["compareAtPrice"] is None
    assert payload["categoryId"] is None
    assert payload["isDigital"] is False


def test_update_payload_omits_none_fields() -> None:
    payload = ProductService._update_payload(ProductUpdate(name="Only Name", price=Decimal("10")))
    assert payload == {"name": "Only Name", "price": Decimal("10")}
