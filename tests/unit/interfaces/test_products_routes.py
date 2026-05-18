"""Interfaces: product HTTP routes."""
from unittest.mock import AsyncMock, MagicMock

from src.domain.shared.exceptions import ConflictError, NotFoundError


def test_create_product_returns_201(client, product_service) -> None:
    response = client.post(
        "/api/v1/products",
        json={
            "sku": "NEW-001",
            "name": "Widget",
            "price": "29.99",
            "status": "ACTIVE",
        },
    )
    assert response.status_code == 201
    assert response.json()["sku"] == "TEST-SKU-001"


def test_create_product_conflict_returns_409(client, test_app, product_service) -> None:
    product_service.create = AsyncMock(side_effect=ConflictError("duplicate SKU"))
    response = client.post(
        "/api/v1/products",
        json={"sku": "DUP", "name": "X", "price": "10", "status": "ACTIVE"},
    )
    assert response.status_code == 409


def test_get_product_not_found_returns_404(client, test_app, product_service) -> None:
    product_service.get_by_id = AsyncMock(side_effect=NotFoundError("Product", "missing"))
    response = client.get("/api/v1/products/missing-id")
    assert response.status_code == 404


def test_list_products_returns_paginated(client) -> None:
    response = client.get("/api/v1/products?limit=10&offset=0")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1


def test_get_product_by_sku(client) -> None:
    response = client.get("/api/v1/products/sku/TEST-SKU-001")
    assert response.status_code == 200
    assert response.json()["sku"] == "TEST-SKU-001"


def test_update_product(client) -> None:
    response = client.patch(
        "/api/v1/products/prod-abc123",
        json={"name": "Updated"},
    )
    assert response.status_code == 200


def test_delete_product_returns_204(client) -> None:
    response = client.delete("/api/v1/products/prod-abc123")
    assert response.status_code == 204
