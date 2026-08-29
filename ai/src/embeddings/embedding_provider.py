"""Embedding Provider abstraction layer.

Wraps embedding models (BAAI/bge-m3 default) behind a unified interface.
Guarantees consistent embedding output dimension (1024 for bge-m3) across batch
and single-query embedding operations.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional
import os


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    def __init__(self, model_name: str, dimension: int = 1024):
        self.model_name = model_name
        self.dimension = dimension

    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate dense vector embeddings for a list of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of float vector lists, each having length `self.dimension`.
        """
        pass

    def embed_query(self, text: str) -> List[float]:
        """Generate dense vector embedding for a single query text.

        Args:
            text: Query string to embed.

        Returns:
            List of floats of length `self.dimension`.
        """
        results = self.embed([text])
        if not results:
            return [0.0] * self.dimension
        return results[0]


class BGEM3EmbeddingProvider(EmbeddingProvider):
    """Concrete embedding provider for BAAI/bge-m3 multilingual dense embeddings."""

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        dimension: int = 1024,
        device: Optional[str] = None,
        normalize_embeddings: bool = True,
    ):
        super().__init__(model_name=model_name, dimension=dimension)
        if device is None:
            try:
                import torch
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                self.device = "cpu"
        else:
            self.device = device
        self.normalize_embeddings = normalize_embeddings
        self._model = None

    def _get_model(self):
        if self._model is not None:
            return self._model

        try:
            from sentence_transformers import SentenceTransformer
            kwargs = {}
            if self.device:
                kwargs["device"] = self.device
            self._model = SentenceTransformer(self.model_name, **kwargs)
            return self._model
        except ImportError as e:
            raise ImportError(
                "sentence-transformers is required for BGEM3EmbeddingProvider. "
                "Install with: pip install sentence-transformers"
            ) from e

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        model = self._get_model()
        # SentenceTransformer.encode returns numpy ndarray or torch tensor
        embeddings = model.encode(
            texts,
            normalize_embeddings=self.normalize_embeddings,
            show_progress_bar=False,
        )

        # Convert to standard Python float list
        if hasattr(embeddings, "tolist"):
            return embeddings.tolist()
        return [list(vec) for vec in embeddings]


def get_embedding_provider(
    model_name: Optional[str] = None,
    dimension: int = 1024,
) -> EmbeddingProvider:
    """Factory function returning the configured EmbeddingProvider.

    Reads `EMBEDDING_MODEL` from environment if model_name is not passed.
    Default: BAAI/bge-m3 (1024-dimensional).
    """
    model = model_name or os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
    return BGEM3EmbeddingProvider(model_name=model, dimension=dimension)
