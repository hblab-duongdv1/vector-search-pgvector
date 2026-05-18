"""Interfaces: domain exception → HTTP mapping."""
import pytest
from fastapi import HTTPException

from src.domain.shared.exceptions import ConflictError, DomainError, NotFoundError
from src.interfaces.http.exceptions import raise_http_for_domain


def test_not_found_maps_to_404() -> None:
    with pytest.raises(HTTPException) as exc_info:
        raise_http_for_domain(NotFoundError("Product", "id-1"))
    assert exc_info.value.status_code == 404
    assert "Product not found" in exc_info.value.detail


def test_conflict_maps_to_409() -> None:
    with pytest.raises(HTTPException) as exc_info:
        raise_http_for_domain(ConflictError("SKU taken"))
    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "SKU taken"


def test_generic_domain_error_maps_to_500() -> None:
    with pytest.raises(HTTPException) as exc_info:
        raise_http_for_domain(DomainError("unexpected"))
    assert exc_info.value.status_code == 500
