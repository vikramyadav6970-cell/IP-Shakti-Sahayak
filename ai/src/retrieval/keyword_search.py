"""Keyword search index using BM25 for legal and regulatory documents.

Provides custom legal tokenization preserving section parentheticals (e.g. '3(p)', '10(4)(d)(ii)'),
multilingual tokens, index building, persistence (joblib/pickle), and collection-filtered retrieval.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union
import logging
import pickle
import re

from rank_bm25 import BM25Okapi, BM25Plus

from src.ingestion.chunker import Chunk

logger = logging.getLogger(__name__)

# Regex pattern for legal section references like '3(p)', '10(4)(d)(ii)', '27.3(b)', '158B'
LEGAL_REF_PATTERN = re.compile(
    r"\b(?:\d+[A-Za-z]?(?:\([0-9a-zA-Z]+\))+|\d+\.\d+(?:\([0-9a-zA-Z]+\))*|\d+[A-Za-z]?)\b"
)
# General word pattern matching alphanumeric, hyphenated words, and Devanagari script
WORD_PATTERN = re.compile(r"[\w\u0900-\u097F]+(?:-[\w\u0900-\u097F]+)*")


def legal_tokenize(text: str) -> List[str]:
    """Custom tokenizer preserving legal compound tokens, parentheticals, and Devanagari words.

    Examples:
        'Section 3(p) of the Patents Act' -> ['section', '3(p)', 'section_3(p)', '3', 'p', 'patents', 'act']
        'Withania somnifera (Ashwagandha)' -> ['withania', 'somnifera', 'withania_somnifera', 'ashwagandha']
    """
    if not text:
        return []

    tokens: List[str] = []
    clean_text = text.strip()

    # 1. Extract and preserve compound legal references (e.g. "Section 3(p)", "Sec. 3(p)", "Article 27(3)")
    compound_matches = list(re.finditer(
        r"(?i)\b(section|sec|rule|article|clause|form)\s+(\d+[A-Za-z]?(?:\([0-9a-zA-Z]+\))*|\d+\.\d+|[IVXLCDM]+)",
        clean_text,
    ))
    for m in compound_matches:
        prefix = m.group(1).lower()
        ref = m.group(2).lower()
        tokens.append(f"{prefix}_{ref}")
        tokens.append(ref)

    # 2. Extract parenthetical references standalone (e.g. "3(p)", "10(4)(d)(ii)")
    for m in re.finditer(r"\b\d+[A-Za-z]?(?:\([0-9a-zA-Z]+\))+\b", clean_text):
        ref = m.group(0).lower()
        tokens.append(ref)

    # 3. Standard tokenization of words and numbers (English + Devanagari)
    words = WORD_PATTERN.findall(clean_text.lower())
    for w in words:
        if len(w) > 1 or w.isdigit() or re.match(r"[\u0900-\u097F]", w):
            tokens.append(w)

    return tokens


@dataclass
class KeywordSearchResult:
    """Represents a scored result from BM25 search."""

    chunk_id: str
    document_id: str
    corpus_collection: str
    text: str
    score: float
    token_count: int = 0
    jurisdiction: str = "INDIA"
    metadata: Dict[str, Any] = field(default_factory=dict)


class BM25Index:
    """In-memory BM25 index supporting serialization and collection filtering."""

    def __init__(
        self,
        bm25: Optional[Union[BM25Okapi, BM25Plus]] = None,
        chunks: Optional[List[Chunk]] = None,
        tokenized_corpus: Optional[List[List[str]]] = None,
    ):
        self.bm25 = bm25
        self.chunks = chunks or []
        self.tokenized_corpus = tokenized_corpus or []

    @classmethod
    def build(cls, chunks: Sequence[Chunk]) -> "BM25Index":
        """Build BM25Plus index from a sequence of Chunk objects."""
        chunk_list = list(chunks)
        if not chunk_list:
            logger.warning("Empty chunk list provided to BM25Index.build()")
            return cls(bm25=None, chunks=[], tokenized_corpus=[])

        tokenized_corpus = [legal_tokenize(c.text) for c in chunk_list]
        # BM25Plus prevents negative IDF scores on small or term-dense corpora
        bm25 = BM25Plus(tokenized_corpus)

        logger.info("Built BM25 index over %d chunks.", len(chunk_list))
        return cls(bm25=bm25, chunks=chunk_list, tokenized_corpus=tokenized_corpus)

    def search(
        self,
        query: str,
        collection: Optional[str] = None,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> List[KeywordSearchResult]:
        """Search BM25 index with optional collection filtering.

        Args:
            query: User search query or decomposed sub-task query.
            collection: Optional target collection name to filter against.
            top_k: Maximum number of top results.
            min_score: Minimum BM25 score threshold.

        Returns:
            List of KeywordSearchResult objects sorted by BM25 score descending.
        """
        if not self.bm25 or not self.chunks:
            return []

        query_tokens = legal_tokenize(query)
        if not query_tokens:
            return []

        query_token_set = set(query_tokens)
        doc_scores = self.bm25.get_scores(query_tokens)

        scored_results: List[KeywordSearchResult] = []
        for idx, score in enumerate(doc_scores):
            chunk = self.chunks[idx]
            if collection and chunk.corpus_collection != collection:
                continue

            # Only include if there is actual query token overlap or positive score
            doc_token_set = set(self.tokenized_corpus[idx])
            has_overlap = bool(query_token_set & doc_token_set)

            if not has_overlap:
                continue

            if score < min_score:
                continue

            scored_results.append(
                KeywordSearchResult(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    corpus_collection=chunk.corpus_collection,
                    text=chunk.text,
                    score=float(score),
                    token_count=chunk.token_count,
                    jurisdiction=chunk.jurisdiction,
                    metadata=dict(chunk.metadata),
                )
            )

        scored_results.sort(key=lambda r: r.score, reverse=True)
        return scored_results[:top_k]

    def save(self, path: Union[str, Path]) -> None:
        """Serialize BM25 index and chunk payload to disk."""
        target_path = Path(path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "chunks": self.chunks,
            "tokenized_corpus": self.tokenized_corpus,
        }
        with open(target_path, "wb") as f:
            pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)

        logger.info("Saved BM25 index with %d chunks to '%s'", len(self.chunks), target_path)

    @classmethod
    def load(cls, path: Union[str, Path]) -> "BM25Index":
        """Load serialized BM25 index from disk."""
        target_path = Path(path)
        if not target_path.exists():
            raise FileNotFoundError(f"BM25 index file not found at: {target_path}")

        with open(target_path, "rb") as f:
            payload = pickle.load(f)

        chunks = payload["chunks"]
        tokenized_corpus = payload["tokenized_corpus"]
        bm25 = BM25Plus(tokenized_corpus) if tokenized_corpus else None

        logger.info("Loaded BM25 index with %d chunks from '%s'", len(chunks), target_path)
        return cls(bm25=bm25, chunks=chunks, tokenized_corpus=tokenized_corpus)


# Functional API requested by prompt
def build_index(chunks: Sequence[Chunk]) -> BM25Index:
    """Build a BM25Index from chunk sequence."""
    return BM25Index.build(chunks)


def load_index(path: Union[str, Path]) -> BM25Index:
    """Load BM25Index from serialized file path."""
    return BM25Index.load(path)


def search(
    index: BM25Index,
    query: str,
    collection: Optional[str] = None,
    top_k: int = 5,
) -> List[KeywordSearchResult]:
    """Execute keyword search on BM25 index."""
    return index.search(query=query, collection=collection, top_k=top_k)
