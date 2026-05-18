"""Domain: shared exceptions."""
from src.domain.shared.exceptions import ConflictError, DomainError, NotFoundError


def test_not_found_error_attributes() -> None:
    exc = NotFoundError("Product", "abc-123")
    assert exc.resource == "Product"
    assert exc.identifier == "abc-123"
    assert "Product not found" in str(exc)
    assert isinstance(exc, DomainError)


def test_conflict_error_message() -> None:
    exc = ConflictError("SKU already exists")
    assert exc.message == "SKU already exists"
    assert isinstance(exc, DomainError)
