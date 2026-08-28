"""Unit and smoke tests for the Embedding Provider and Qdrant Indexer."""

from unittest.mock import MagicMock, patch
import os
import pytest
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from src.embeddings.embedding_provider import (
    EmbeddingProvider,
    BGEM3EmbeddingProvider,
    get_embedding_provider,
)
from src.embeddings.indexer import QdrantIndexer, ALL_COLLECTIONS
from src.ingestion.chunker import Chunk


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
    dummy_vectors = np.ones((2, 1024), dtype=np.float32)
    mock_model.encode.return_value = dummy_vectors

    with patch.object(provider, "_get_model", return_value=mock_model):
        texts = ["Ayurvedic patent law under Section 3(p)", "आयुर्वेदिक औषधि"]
        embeddings = provider.embed(texts)

        assert len(embeddings) == 2
        assert len(embeddings[0]) == 1024
        assert len(embeddings[1]) == 1024
        assert all(isinstance(val, float) for val in embeddings[0])

        query_vec = provider.embed_query("Patent analysis")
        assert len(query_vec) == 1024


def test_embed_empty_list():
    """Embedding an empty list should return an empty list without calling model."""
    provider = BGEM3EmbeddingProvider(model_name="BAAI/bge-m3", dimension=1024)
    assert provider.embed([]) == []


def test_qdrant_ensure_collections():
    """QdrantIndexer should create all 5 named collections in memory with 1024 dimension."""
    client = QdrantClient(":memory:")
    mock_embedder = MagicMock(spec=EmbeddingProvider)
    mock_embedder.dimension = 1024

    indexer = QdrantIndexer(client=client, embedding_provider=mock_embedder, dimension=1024)
    confirmed = indexer.ensure_collections()

    assert set(confirmed) == set(ALL_COLLECTIONS)

    existing = [c.name for c in client.get_collections().collections]
    for col in ALL_COLLECTIONS:
        assert col in existing
        info = client.get_collection(col)
        assert info.config.params.vectors.size == 1024
        assert info.config.params.vectors.distance == Distance.COSINE


def test_qdrant_index_chunks_across_multiple_collections():
    """QdrantIndexer should route chunks to correct collections and preserve payload metadata."""
    client = QdrantClient(":memory:")
    mock_embedder = MagicMock(spec=EmbeddingProvider)
    mock_embedder.dimension = 1024
    # Mock return 1024-dim unit vector
    mock_embedder.embed.side_effect = lambda texts: [[0.1] * 1024 for _ in texts]

    indexer = QdrantIndexer(client=client, embedding_provider=mock_embedder, dimension=1024)

    # 3 mock chunks across 2 collections
    chunks = [
        Chunk(
            chunk_id="doc_patents#sec_3_p",
            document_id="doc_patents",
            corpus_collection="legal_statutory",
            text="Section 3(p) excludes traditional knowledge from patentability.",
            token_count=10,
            jurisdiction="INDIA",
            metadata={"act": "Patents Act 1970", "section": "3", "subsection": "p"},
        ),
        Chunk(
            chunk_id="doc_patents#sec_10_4",
            document_id="doc_patents",
            corpus_collection="legal_statutory",
            text="Section 10(4)(d)(ii) requires mandatory source disclosure of biological material.",
            token_count=12,
            jurisdiction="INDIA",
            metadata={"act": "Patents Act 1970", "section": "10", "subsection": "4"},
        ),
        Chunk(
            chunk_id="doc_api#ashwagandha",
            document_id="doc_api",
            corpus_collection="standards_formulations",
            text="Ashwagandha consists of dried roots of Withania somnifera Dunal.",
            token_count=11,
            jurisdiction="INDIA",
            metadata={
                "monograph_id": "api_001",
                "formulation_name": "Ashwagandha",
                "botanical_name": "Withania somnifera Dunal.",
                "substance_type": "SINGLE_HERB",
            },
        ),
    ]

    res = indexer.index_chunks(chunks)

    assert res["legal_statutory"] == 2
    assert res["standards_formulations"] == 1

    # Search in legal_statutory and verify payload
    legal_results = indexer.search(
        collection_name="legal_statutory",
        query_vector=[0.1] * 1024,
        limit=5,
    )
    assert len(legal_results) == 2
    sections = [p.payload["section"] for p in legal_results]
    assert "3" in sections
    assert "10" in sections

    # Search in standards_formulations and verify botanical metadata
    herbal_results = indexer.search(
        collection_name="standards_formulations",
        query_vector=[0.1] * 1024,
        limit=5,
    )
    assert len(herbal_results) == 1
    assert herbal_results[0].payload["botanical_name"] == "Withania somnifera Dunal."


@pytest.mark.smoke
@pytest.mark.slow
def test_bge_m3_live_smoke():
    """Live smoke test embedding an English and Hindi sentence with real BAAI/bge-m3 model."""
    try:
        import sentence_transformers
    except ImportError:
        pytest.skip("sentence-transformers not installed yet; skipping live embedding test.")

    provider = get_embedding_provider("BAAI/bge-m3", dimension=1024)

    english_text = "Patent eligibility of Ayurvedic herbal formulations under Section 3(p) of the Patents Act 1970."
    hindi_text = "भारतीय पेटेंट अधिनियम १९७० की धारा ३(पी) के तहत आयुर्वेदिक औषधियों की पेटेंट योग्यता।"

    embeddings = provider.embed([english_text, hindi_text])

    assert len(embeddings) == 2
    assert len(embeddings[0]) == 1024
    assert len(embeddings[1]) == 1024
    assert any(abs(val) > 1e-6 for val in embeddings[0])
    assert any(abs(val) > 1e-6 for val in embeddings[1])


@pytest.mark.smoke
def test_qdrant_cloud_live_provisioning():
    """Live smoke test verifying connection and collection provisioning on Qdrant Cloud cluster."""
    url = os.getenv("QDRANT_URL")
    key = os.getenv("QDRANT_API_KEY")

    if not url or not key or "your-cluster" in url:
        pytest.skip("No real QDRANT_URL / QDRANT_API_KEY configured; skipping cloud test.")

    indexer = QdrantIndexer(url=url, api_key=key, dimension=1024)
    confirmed = indexer.ensure_collections()
    assert set(confirmed) == set(ALL_COLLECTIONS)
