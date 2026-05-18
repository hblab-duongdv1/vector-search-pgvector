"""Interfaces: semantic search HTTP routes."""
def test_search_products_returns_results(client) -> None:
    response = client.post(
        "/api/v1/products/search",
        json={"query": "running shoes", "limit": 5},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "running shoes"
    assert body["total"] == 1
    assert body["embedding_model"] == "test-model"
    assert body["results"][0]["similarity_score"] == 0.87


def test_search_validation_error_on_empty_query(client) -> None:
    response = client.post(
        "/api/v1/products/search",
        json={"query": "", "limit": 5},
    )
    assert response.status_code == 422
