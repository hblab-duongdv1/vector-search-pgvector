"""Infrastructure: SentenceTransformer encoder adapter."""
import sys
from unittest.mock import MagicMock

import numpy as np

# Avoid loading sentence_transformers / transformers at import time in CI/sandbox.
sys.modules.setdefault("sentence_transformers", MagicMock())

from src.infrastructure.ml.embedding_encoder import SentenceTransformerEncoder


def test_encode_returns_normalized_vector_list() -> None:
    model = MagicMock()
    model.encode.return_value = np.array([0.5, 0.5, 0.0])
    encoder = SentenceTransformerEncoder(model)

    result = encoder.encode("hello world")

    assert result == [0.5, 0.5, 0.0]
    model.encode.assert_called_once_with(
        "hello world",
        normalize_embeddings=True,
        show_progress_bar=False,
    )
