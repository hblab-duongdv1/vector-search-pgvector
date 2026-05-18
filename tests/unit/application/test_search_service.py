"""Application: SearchService use cases."""
from unittest.mock import MagicMock

import pytest

from src.application.search.service import SearchService
from src.domain.search.schemas import SearchFilters, SearchRequest


@pytest.mark.asyncio
async def test_search_encodes_query_and_calls_repository(
    search_service: SearchService,
    mock_encoder: MagicMock,
    mock_search_repository: MagicMock,
) -> None:
    request = SearchRequest(query="running shoes", limit=5)
    response = await search_service.search(request)

    mock_encoder.encode.assert_called_once_with("running shoes")
    mock_search_repository.search_by_vector.assert_awaited_once()
    vector_arg = mock_search_repository.search_by_vector.await_args[0][0]
    assert vector_arg == "[0.1,0.2,0.3]"

    assert response.query == "running shoes"
    assert response.total == 1
    assert len(response.results) == 1
    assert response.results[0].similarity_score == 0.87
    assert response.embedding_model == "test-model"


@pytest.mark.asyncio
async def test_search_empty_results(
    mock_search_repository: MagicMock, mock_encoder: MagicMock
) -> None:
    mock_search_repository.search_by_vector.return_value = []
    service = SearchService(mock_search_repository, mock_encoder, "m")
    response = await service.search(SearchRequest(query="nothing"))
    assert response.total == 0
    assert response.results == []


@pytest.mark.asyncio
async def test_search_passes_filters_to_repository(
    search_service: SearchService, mock_search_repository: MagicMock
) -> None:
    request = SearchRequest(
        query="phone",
        filters=SearchFilters(status="INACTIVE", brand_id="brand-001"),
    )
    await search_service.search(request)
    passed_request = mock_search_repository.search_by_vector.await_args[0][1]
    assert passed_request.filters.status == "INACTIVE"
    assert passed_request.filters.brand_id == "brand-001"
