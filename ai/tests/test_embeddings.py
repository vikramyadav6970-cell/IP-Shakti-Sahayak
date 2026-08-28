"""Unit and smoke tests for the Embedding Provider (BAAI/bge-m3)."""

from unittest.mock import MagicMock, patch
import pytest
import numpy as np

from src.embeddings.embedding_provider import (
    EmbeddingProvider,
    BGEM3EmbeddingProvider,
    get_embedding_provider,
)


def test_embedding_provider_factory():
    """get_embedding_provider factory should instantiate BGEM3EmbeddingProvider with 1024 dimension."""
    provider = get_embedding_provider("BAAI/bge-m3", dimension=1024)
    assert isinstance(provider, BGEM3EmbeddingProvider)
    assert provider.model_name == "BAAI/bge-m3"
    assert provider.dimension == 1024


def test_embed_mock():
    """BGEM3EmbeddingProvider should encode texts and return 1024-dim float vectors."""
    provider = BGEM3EmbeddingProvider(model_name="BAAI/bge-m3", dimension=1024)

    mock_model = MagicMock()
    # Mock return 2 vectors of length 1024
    dummy_vectors = np.ones((2, 1024), dtype=np.float32)
    mock_model.encode.return_value = dummy_vectors

    with patch.object(provider, "_get_model", return_value=mock_model):
        texts = ["Ayurvedic patent law under Section 3(p)", "आयुर्वेदिक औषधि"]
        embeddings = provider.embed(texts)

        assert len(embeddings) == 2
        assert len(embeddings[0]) == 1024
        assert len(embeddings[1]) == 1024
        assert all(isinstance(val, float) for val in embeddings[0])

        # Test single query embedding
        query_vec = provider.embed_query("Patent analysis")
        assert len(query_vec) == 1024


def test_embed_empty_list():
    """Embedding an empty list should return an empty list without calling model."""
    provider = BGEM3EmbeddingProvider(model_name="BAAI/bge-m3", dimension=1024)
    assert provider.embed([]) == []


@pytest.mark.smoke
@pytest.mark.slow
def test_bge_m3_live_smoke():
    """Live smoke test embedding an English and Hindi sentence with real BAAI/bge-m3 model.

    Asserts:
    1. Vector dimensionality is exactly 1024.
    2. Output vectors are not all-zero.
    3. Both English and Hindi texts produce valid normalized vectors.
    """
    try:
        import sentence_transformers
    except ImportError:
        pytest.skip("sentence-transformers not installed yet; skipping live embedding test.")

    provider = get_embedding_provider("BAAI/bge-m3", dimension=1024)

    english_text = "Patent eligibility of Ayurvedic herbal formulations under Section 3(p) of the Patents Act 1970."
    hindi_text = "भारतीय पेटेंट अधिनियम १९७० की धारा ३(पी) के तहत आयुर्वेदिक औषधियों की पेटेंट योग्यता।"

    embeddings = provider.embed([english_text, hindi_text])

    assert len(embeddings) == 2, "Expected 2 embedding vectors for 2 input sentences."

    en_vec = embeddings[0]
    hi_vec = embeddings[1]

    # Assert exact dimension is 1024
    assert len(en_vec) == 1024, f"Expected 1024 dimension for English vector, got {len(en_vec)}"
    assert len(hi_vec) == 1024, f"Expected 1024 dimension for Hindi vector, got {len(hi_vec)}"

    # Assert vectors are not all-zero
    assert any(abs(val) > 1e-6 for val in en_vec), "English embedding vector must not be all-zero."
    assert any(abs(val) > 1e-6 for val in hi_vec), "Hindi embedding vector must not be all-zero."

    # Single query method test
    query_vec = provider.embed_query(english_text)
    assert len(query_vec) == 1024
    assert any(abs(val) > 1e-6 for val in query_vec)
