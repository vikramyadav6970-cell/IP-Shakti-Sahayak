"""Retrieval module — keyword BM25, dense vector search, hybrid retriever and RRF."""

from src.retrieval.keyword_search import (
    BM25Index,
    KeywordSearchResult,
    legal_tokenize,
    build_index,
    load_index,
    search as bm25_search,
)
from src.retrieval.hybrid_retriever import (
    EvidenceChunk,
    HybridRetriever,
    retrieve,
)

__all__ = [
    "BM25Index",
    "KeywordSearchResult",
    "legal_tokenize",
    "build_index",
    "load_index",
    "bm25_search",
    "EvidenceChunk",
    "HybridRetriever",
    "retrieve",
]
