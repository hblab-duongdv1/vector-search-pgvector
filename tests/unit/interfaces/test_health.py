"""Interfaces: health check endpoint."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import create_app


@pytest.fixture
def health_client(monkeypatch: pytest.MonkeyPatch):
    """App + client with mocked startup (no real DB/model/worker)."""
    monkeypatch.setattr("src.main.connect_db", AsyncMock())
    monkeypatch.setattr("src.main.disconnect_db", AsyncMock())
    monkeypatch.setattr(
        "sentence_transformers.SentenceTransformer", lambda *_a, **_k: MagicMock()
    )
    worker_instance = MagicMock()
    worker_instance.start = AsyncMock()
    worker_instance.stop = AsyncMock()
    monkeypatch.setattr(
        "src.infrastructure.workers.embedding_worker.EmbeddingWorker",
        MagicMock(return_value=worker_instance),
    )

    async def _noop(_worker: object) -> None:
        return None

    monkeypatch.setattr("src.main._keep_worker_alive", _noop)

    app = create_app()
    with TestClient(app) as client:
        yield app, client


@patch("src.interfaces.http.health.get_prisma")
def test_health_ok_when_db_and_worker_running(
    mock_get_prisma: MagicMock, health_client: tuple
) -> None:
    app, client = health_client
    prisma = MagicMock()
    prisma.is_connected.return_value = True
    prisma.query_raw = AsyncMock(return_value=[{"?column?": 1}])
    mock_get_prisma.return_value = prisma
    app.state.embedding_worker_running = True

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"
    assert body["embedding_worker"] == "running"


@patch("src.interfaces.http.health.get_prisma")
def test_health_unhealthy_when_db_disconnected(
    mock_get_prisma: MagicMock, health_client: tuple
) -> None:
    _app, client = health_client
    prisma = MagicMock()
    prisma.is_connected.return_value = False
    mock_get_prisma.return_value = prisma

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["status"] == "unhealthy"
