"""Embeddings module — EmbeddingProvider interface and Qdrant indexer."""

from src.embeddings.embedding_provider import (
    EmbeddingProvider,
    BGEM3EmbeddingProvider,
    get_embedding_provider,
)
from src.embeddings.indexer import (
    QdrantIndexer,
    ALL_COLLECTIONS,
)

__all__ = [
    "EmbeddingProvider",
    "BGEM3EmbeddingProvider",
    "get_embedding_provider",
    "QdrantIndexer",
    "ALL_COLLECTIONS",
]
