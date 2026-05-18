"""Sentence-transformers adapter for EmbeddingEncoder port."""
from sentence_transformers import SentenceTransformer

from src.domain.search.ports import EmbeddingEncoder


class SentenceTransformerEncoder:
    """Wraps SentenceTransformer for the EmbeddingEncoder port."""

    def __init__(self, model: SentenceTransformer) -> None:
        self._model = model

    def encode(self, text: str) -> list[float]:
        return self._model.encode(
            text,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()
