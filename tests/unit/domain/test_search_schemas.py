"""Domain: search request/response schemas."""
import pytest
from pydantic import ValidationError

from src.domain.search.schemas import SearchFilters, SearchRequest


def test_search_filters_status_optional_by_default() -> None:
    filters = SearchFilters()
    assert filters.status is None


def test_search_filters_accepts_valid_status() -> None:
    filters = SearchFilters(status="INACTIVE")
    assert filters.status == "INACTIVE"


def test_search_filters_rejects_invalid_status() -> None:
    with pytest.raises(ValidationError):
        SearchFilters(status="DELETED")


def test_search_request_defaults() -> None:
    req = SearchRequest(query="winter jacket")
    assert req.limit == 10
    assert req.threshold == 0.0
    assert req.filters.status is None
