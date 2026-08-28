"""Embeddings module — EmbeddingProvider interface and Qdrant indexer."""

from src.embeddings.embedding_provider import (
    EmbeddingProvider,
    BGEM3EmbeddingProvider,
    get_embedding_provider,
)

__all__ = [
    "EmbeddingProvider",
    "BGEM3EmbeddingProvider",
    "get_embedding_provider",
]
