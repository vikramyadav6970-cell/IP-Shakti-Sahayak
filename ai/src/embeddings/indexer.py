"""Qdrant Cloud vector indexer for the 5-collection legal/regulatory corpus.

Manages collection provisioning, batch vector embedding, payload flattening,
and upserts into Qdrant Cloud collections.
"""

from typing import Any, Dict, List, Optional, Sequence
import logging
import os
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams

from src.embeddings.embedding_provider import EmbeddingProvider, get_embedding_provider
from src.ingestion.chunker import Chunk

logger = logging.getLogger(__name__)

# Authoritative list of 5 Qdrant Cloud collections
ALL_COLLECTIONS = [
    "legal_statutory",
    "standards_formulations",
    "case_law_prior_art",
    "procedural_forms",
    "international_export",
]


class QdrantIndexer:
    """Vector indexer managing the 5 Qdrant Cloud collections."""

    def __init__(
        self,
        client: Optional[QdrantClient] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        dimension: int = 1024,
    ):
        """Initialize QdrantIndexer.

        Args:
            client: Optional pre-configured QdrantClient (useful for in-memory unit tests).
            embedding_provider: Optional EmbeddingProvider instance (defaults to BAAI/bge-m3).
            url: Qdrant cluster URL. If None, reads from QDRANT_URL env var.
            api_key: Qdrant API key. If None, reads from QDRANT_API_KEY env var.
            dimension: Vector dimension (must match embedding model, default 1024).
        """
        self.dimension = dimension
        self.embedding_provider = embedding_provider or get_embedding_provider(dimension=self.dimension)

        if client is not None:
            self.client = client
        else:
            try:
                from src.config import settings
                default_url = getattr(settings, "qdrant_url", None)
                default_key = getattr(settings, "qdrant_api_key", None)
            except Exception:
                default_url = None
                default_key = None

            qdrant_url = url or os.getenv("QDRANT_URL") or default_url
            qdrant_api_key = api_key or os.getenv("QDRANT_API_KEY") or default_key

            if not qdrant_url:
                logger.warning("No QDRANT_URL provided. Initializing in-memory Qdrant instance.")
                self.client = QdrantClient(":memory:")
            else:
                self.client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, timeout=120.0)

    def ensure_collections(
        self,
        collections: Optional[Sequence[str]] = None,
        dimension: Optional[int] = None,
        distance: Distance = Distance.COSINE,
    ) -> List[str]:
        """Ensure that the 5 collections exist in Qdrant; create any missing ones idempotently.

        Args:
            collections: List of collection names to verify/create. Defaults to ALL_COLLECTIONS.
            dimension: Vector size (default 1024).
            distance: Distance metric (default Cosine).

        Returns:
            List of confirmed collection names.
        """
        target_collections = collections or ALL_COLLECTIONS
        dim = dimension or self.dimension

        existing_info = self.client.get_collections()
        existing_names = {col.name for col in existing_info.collections}

        created = []
        for col_name in target_collections:
            if col_name not in existing_names:
                logger.info("Creating Qdrant collection '%s' (dim=%d, distance=%s)", col_name, dim, distance)
                self.client.create_collection(
                    collection_name=col_name,
                    vectors_config=VectorParams(size=dim, distance=distance),
                )
                created.append(col_name)
            else:
                logger.debug("Qdrant collection '%s' already exists.", col_name)

        return list(target_collections)

    def index_chunks(
        self,
        chunks: List[Chunk],
        batch_size: int = 64,
        max_retries: int = 3,
    ) -> Dict[str, int]:
        """Embed and upsert chunks into their respective Qdrant collections.

        Chunks are grouped by `corpus_collection` and batch-embedded via
        the configured EmbeddingProvider.

        Args:
            chunks: List of Chunk objects from T1.3.
            batch_size: Number of chunks per embedding/upsert batch.
            max_retries: Maximum retry attempts on network/timeout errors.

        Returns:
            Dictionary mapping collection name to number of indexed points.
        """
        import time

        if not chunks:
            return {}

        self.ensure_collections()

        # Group chunks by collection
        chunks_by_collection: Dict[str, List[Chunk]] = {}
        for chunk in chunks:
            col = chunk.corpus_collection
            if col not in chunks_by_collection:
                chunks_by_collection[col] = []
            chunks_by_collection[col].append(chunk)

        results: Dict[str, int] = {}

        for col_name, col_chunks in chunks_by_collection.items():
            total_indexed = 0
            logger.info("Indexing %d chunks into collection '%s'...", len(col_chunks), col_name)

            for i in range(0, len(col_chunks), batch_size):
                batch = col_chunks[i : i + batch_size]
                texts = [c.text for c in batch]

                # Generate dense vectors
                embeddings = self.embedding_provider.embed(texts)

                # Prepare Qdrant PointStructs
                points: List[models.PointStruct] = []
                for chunk, vector in zip(batch, embeddings):
                    # Deterministic UUID5 based on chunk_id for idempotency
                    point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.chunk_id))

                    # Flatten all payload fields directly for filtering
                    payload: Dict[str, Any] = {
                        "chunk_id": chunk.chunk_id,
                        "document_id": chunk.document_id,
                        "corpus_collection": chunk.corpus_collection,
                        "text": chunk.text,
                        "token_count": chunk.token_count,
                        "jurisdiction": chunk.jurisdiction,
                        "parent_chunk_id": chunk.parent_chunk_id,
                        **chunk.metadata,
                    }

                    points.append(
                        models.PointStruct(
                            id=point_id,
                            vector=vector,
                            payload=payload,
                        )
                    )

                # Upsert batch into Qdrant with retry loop
                for attempt in range(1, max_retries + 1):
                    try:
                        self.client.upsert(
                            collection_name=col_name,
                            points=points,
                        )
                        total_indexed += len(points)
                        logger.info("  [%s] Upserted batch %d-%d / %d", col_name, i + 1, i + len(points), len(col_chunks))
                        break
                    except Exception as exc:
                        if attempt == max_retries:
                            logger.error("Failed to upsert batch into %s after %d attempts: %s", col_name, max_retries, exc)
                            raise
                        wait_sec = attempt * 2
                        logger.warning("Upsert into %s failed (attempt %d/%d): %s. Retrying in %ds...", col_name, attempt, max_retries, exc, wait_sec)
                        time.sleep(wait_sec)

            results[col_name] = total_indexed
            logger.info("Completed collection '%s': %d total points indexed.", col_name, total_indexed)

        return results


    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        query_filter: Optional[models.Filter] = None,
        score_threshold: Optional[float] = None,
    ) -> List[models.ScoredPoint]:
        """Perform dense vector search against a single Qdrant collection.

        Args:
            collection_name: Target collection name.
            query_vector: 1024-dim dense query vector.
            limit: Maximum points to return.
            query_filter: Qdrant Filter for payload metadata (e.g. jurisdiction).
            score_threshold: Minimum similarity threshold.

        Returns:
            List of ScoredPoint objects ordered by similarity.
        """
        # Supports query_points (qdrant-client >= 1.10) or search
        try:
            return self.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=limit,
                query_filter=query_filter,
                score_threshold=score_threshold,
            ).points
        except (AttributeError, TypeError):
            return self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=query_filter,
                score_threshold=score_threshold,
            )

    def get_collection_stats(self) -> Dict[str, int]:
        """Return point count for all 5 collections."""
        stats: Dict[str, int] = {}
        for col in ALL_COLLECTIONS:
            try:
                info = self.client.get_collection(col)
                stats[col] = info.points_count or 0
            except Exception:
                stats[col] = 0
        return stats
