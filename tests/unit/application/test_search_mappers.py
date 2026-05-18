"""Application: search result mappers."""
from typing import Any

from src.application.search.mappers import to_search_result


def test_to_search_result_maps_sql_row(search_row: dict[str, Any]) -> None:
    result = to_search_result(search_row)
    assert result.id == "prod-abc123"
    assert result.sku == "TEST-SKU-001"
    assert result.similarity_score == 0.87
    assert result.brand is not None
    assert result.brand.name == "Apple"
    assert result.category is not None
    assert result.category.slug == "electronics"


def test_to_search_result_minimal_row() -> None:
    row = {
        "id": "p1",
        "sku": "S1",
        "name": "Item",
        "price": 10,
        "similarity_score": 0.5,
    }
    result = to_search_result(row)
    assert result.brand is None
    assert result.category is None
    assert result.tags == []
    assert result.similarity_score == 0.5
