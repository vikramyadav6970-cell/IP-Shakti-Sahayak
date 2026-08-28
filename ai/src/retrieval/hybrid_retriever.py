"""Hybrid retriever combining Qdrant dense vector search, BM25 keyword search, and RRF.

Core retrieval primitive executed asynchronously in parallel for each decomposed sub-task query.
Applies hard jurisdiction filtering at the Qdrant query level per context.md §2 and coding conventions.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence
import asyncio
import logging
import os

from qdrant_client.http import models

from src.embeddings.embedding_provider import EmbeddingProvider, get_embedding_provider
from src.embeddings.indexer import QdrantIndexer, ALL_COLLECTIONS
from src.retrieval.keyword_search import BM25Index, KeywordSearchResult, legal_tokenize

logger = logging.getLogger(__name__)


@dataclass
class EvidenceChunk:
    """Represents a validated evidence chunk with dense, sparse, and fusion scores."""

    chunk_id: str
    document_id: str
    corpus_collection: str
    text: str
    score: float
    jurisdiction: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    dense_score: Optional[float] = None
    sparse_score: Optional[float] = None
    rrf_score: Optional[float] = None
    rerank_score: Optional[float] = None


class HybridRetriever:
    """Hybrid multi-collection retriever implementing Qdrant dense + BM25 sparse + RRF fusion."""

    def __init__(
        self,
        indexer: Optional[QdrantIndexer] = None,
        bm25_index: Optional[BM25Index] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        cohere_api_key: Optional[str] = None,
        rrf_k: int = 60,
    ):
        """Initialize HybridRetriever.

        Args:
            indexer: QdrantIndexer instance.
            bm25_index: BM25Index instance for keyword retrieval.
            embedding_provider: EmbeddingProvider for query vectorization.
            cohere_api_key: Optional Cohere API key for semantic reranking.
            rrf_k: Reciprocal Rank Fusion smoothing parameter (standard default 60).
        """
        self.indexer = indexer or QdrantIndexer()
        self.bm25_index = bm25_index
        self.embedding_provider = embedding_provider or self.indexer.embedding_provider
        self.cohere_api_key = cohere_api_key or os.getenv("COHERE_API_KEY")
        self.rrf_k = rrf_k

    async def retrieve(
        self,
        query: str,
        collections: Sequence[str],
        jurisdiction: str,
        top_k: int = 8,
    ) -> List[EvidenceChunk]:
        """Retrieve evidence chunks across specified collections with hard jurisdiction filtering.

        Args:
            query: Natural language question or decomposed sub-task query.
            collections: List of target Qdrant collection names.
            jurisdiction: Target jurisdiction (e.g. 'INDIA', 'INTERNATIONAL', 'EU', 'USA').
            top_k: Maximum evidence chunks to return.

        Returns:
            List of EvidenceChunk objects sorted by fused relevance score.
        """
        if not query or not collections:
            return []

        # Run synchronous vector search and BM25 search in an async executor thread
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self._retrieve_sync,
            query,
            list(collections),
            jurisdiction,
            top_k,
        )

    def _retrieve_sync(
        self,
        query: str,
        collections: List[str],
        jurisdiction: str,
        top_k: int,
    ) -> List[EvidenceChunk]:
        """Synchronous retrieval execution."""
        # 1. Embed query
        query_vector = self.embedding_provider.embed_query(query)

        # 2. Hard Qdrant payload filter for jurisdiction
        # Treat INTERNATIONAL and specific jurisdiction appropriately
        jurisdiction_upper = jurisdiction.upper()
        if jurisdiction_upper in ["INDIA", "EU", "USA"]:
            # Match specific jurisdiction or universal INTERNATIONAL entries
            filter_conditions = [
                models.FieldCondition(
                    key="jurisdiction",
                    match=models.MatchAny(any=[jurisdiction_upper, "INTERNATIONAL"]),
                )
            ]
        else:
            filter_conditions = [
                models.FieldCondition(
                    key="jurisdiction",
                    match=models.MatchValue(value=jurisdiction_upper),
                )
            ]
        qdrant_filter = models.Filter(must=filter_conditions)

        # 3. Dense search across all specified collections
        dense_results: Dict[str, Dict[str, Any]] = {}
        for col in collections:
            if col not in ALL_COLLECTIONS:
                continue
            try:
                hits = self.indexer.search(
                    collection_name=col,
                    query_vector=query_vector,
                    limit=top_k * 2,
                    query_filter=qdrant_filter,
                )
                for rank, hit in enumerate(hits):
                    chunk_id = hit.payload.get("chunk_id", str(hit.id))
                    # Validate hard filter in payload
                    hit_jur = hit.payload.get("jurisdiction", "").upper()
                    if hit_jur and hit_jur != jurisdiction_upper and hit_jur != "INTERNATIONAL":
                        continue

                    dense_results[chunk_id] = {
                        "rank": rank + 1,
                        "score": hit.score,
                        "chunk_id": chunk_id,
                        "document_id": hit.payload.get("document_id", "doc_unknown"),
                        "corpus_collection": col,
                        "text": hit.payload.get("text", ""),
                        "jurisdiction": hit.payload.get("jurisdiction", jurisdiction),
                        "metadata": hit.payload,
                    }
            except Exception as e:
                logger.warning("Error querying Qdrant collection '%s': %s", col, e)

        # 4. Sparse BM25 search across specified collections
        sparse_results: Dict[str, Dict[str, Any]] = {}
        if self.bm25_index:
            for col in collections:
                bm25_hits = self.bm25_index.search(
                    query=query,
                    collection=col,
                    top_k=top_k * 2,
                )
                for rank, hit in enumerate(bm25_hits):
                    hit_jur = hit.jurisdiction.upper()
                    if hit_jur and hit_jur != jurisdiction_upper and hit_jur != "INTERNATIONAL":
                        continue

                    sparse_results[hit.chunk_id] = {
                        "rank": rank + 1,
                        "score": hit.score,
                        "chunk_id": hit.chunk_id,
                        "document_id": hit.document_id,
                        "corpus_collection": col,
                        "text": hit.text,
                        "jurisdiction": hit.jurisdiction,
                        "metadata": hit.metadata,
                    }

        # 5. Reciprocal Rank Fusion (RRF)
        all_chunk_ids = set(dense_results.keys()) | set(sparse_results.keys())
        if not all_chunk_ids:
            return []

        candidates: List[EvidenceChunk] = []

        for cid in all_chunk_ids:
            d_hit = dense_results.get(cid)
            s_hit = sparse_results.get(cid)

            # Metadata and content source
            source = d_hit or s_hit
            if not source:
                continue

            # Compute RRF score
            rrf_score = 0.0
            dense_score = None
            sparse_score = None

            if d_hit:
                dense_rank = d_hit["rank"]
                dense_score = d_hit["score"]
                rrf_score += 1.0 / (self.rrf_k + dense_rank)

            if s_hit:
                sparse_rank = s_hit["rank"]
                sparse_score = s_hit["score"]
                rrf_score += 1.0 / (self.rrf_k + sparse_rank)

            candidates.append(
                EvidenceChunk(
                    chunk_id=cid,
                    document_id=source["document_id"],
                    corpus_collection=source["corpus_collection"],
                    text=source["text"],
                    score=rrf_score,
                    jurisdiction=source["jurisdiction"],
                    metadata=source["metadata"],
                    dense_score=dense_score,
                    sparse_score=sparse_score,
                    rrf_score=rrf_score,
                )
            )

        # Sort by RRF score descending
        candidates.sort(key=lambda c: c.score, reverse=True)
        top_candidates = candidates[: top_k * 2]

        # 6. Semantic Reranking (Cohere Rerank if available)
        reranked = self._rerank_with_cohere_or_passthrough(query, top_candidates, top_k)
        return reranked

    def _rerank_with_cohere_or_passthrough(
        self,
        query: str,
        candidates: List[EvidenceChunk],
        top_k: int,
    ) -> List[EvidenceChunk]:
        """Apply Cohere Rerank if configured; otherwise return top candidates by RRF score."""
        if not self.cohere_api_key or len(candidates) <= 1 or "your-cohere" in self.cohere_api_key:
            return candidates[:top_k]

        try:
            import cohere

            co = cohere.ClientV2(api_key=self.cohere_api_key)
            doc_texts = [c.text for c in candidates]
            response = co.rerank(
                model="rerank-v3.5",
                query=query,
                documents=doc_texts,
                top_n=top_k,
            )

            reranked_chunks: List[EvidenceChunk] = []
            for item in response.results:
                chunk = candidates[item.index]
                chunk.rerank_score = float(item.relevance_score)
                chunk.score = chunk.rerank_score  # Update final score with rerank score
                reranked_chunks.append(chunk)

            return reranked_chunks
        except Exception as e:
            logger.warning("Cohere rerank failed or unavailable (%s); using RRF ranking.", e)
            return candidates[:top_k]


# Module-level default retriever instance
default_retriever = HybridRetriever()


async def retrieve(
    query: str,
    collections: Sequence[str],
    jurisdiction: str = "INDIA",
    top_k: int = 8,
) -> List[EvidenceChunk]:
    """Retrieve evidence chunks asynchronously across collections with hard jurisdiction filter."""
    return await default_retriever.retrieve(
        query=query,
        collections=collections,
        jurisdiction=jurisdiction,
        top_k=top_k,
    )
