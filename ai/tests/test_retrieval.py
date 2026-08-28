"""Unit tests for keyword search, BM25 indexing, legal tokenization, and hybrid retrieval."""

from pathlib import Path
from unittest.mock import MagicMock
import asyncio
import pytest
from qdrant_client import QdrantClient

from src.embeddings.embedding_provider import EmbeddingProvider
from src.embeddings.indexer import QdrantIndexer
from src.retrieval.keyword_search import (
    BM25Index,
    KeywordSearchResult,
    legal_tokenize,
    build_index,
    load_index,
    search as bm25_search,
)
from src.retrieval.hybrid_retriever import EvidenceChunk, HybridRetriever
from src.ingestion.chunker import Chunk


def test_legal_tokenize_parentheticals_and_sections():
    """legal_tokenize must preserve legal parentheticals like 3(p) and 10(4)(d)(ii) as single tokens."""
    text = "Section 3(p) of the Patents Act, 1970 excludes traditional knowledge."
    tokens = legal_tokenize(text)

    assert "3(p)" in tokens
    assert "section_3(p)" in tokens or "3(p)" in tokens
    assert "patents" in tokens
    assert "traditional" in tokens


def test_legal_tokenize_complex_subsections():
    """legal_tokenize must preserve deep nested clauses like 10(4)(d)(ii)."""
    text = "Mandatory disclosure under Section 10(4)(d)(ii) for biological resources."
    tokens = legal_tokenize(text)

    assert "10(4)(d)(ii)" in tokens
    assert "biological" in tokens
    assert "resources" in tokens


def test_legal_tokenize_devanagari_and_botanicals():
    """legal_tokenize must preserve Devanagari script and botanical names."""
    text = "Ashwagandha (Withania somnifera Dunal.) - आयुर्वेदिक औषधि"
    tokens = legal_tokenize(text)

    assert "ashwagandha" in tokens
    assert "withania" in tokens
    assert "somnifera" in tokens
    assert "आयुर्वेदिक" in tokens or any("आयुर्वेद" in t for t in tokens)


def test_bm25_section_3p_retrieval():
    """BM25 search for 'Section 3(p)' must retrieve Section 3(p) chunk as top result."""
    chunks = [
        Chunk(
            chunk_id="doc_patents#sec_3_p",
            document_id="doc_patents",
            corpus_collection="legal_statutory",
            text="Section 3(p) What are not inventions: an invention which in effect is traditional knowledge or aggregation of known properties of traditionally known components.",
            token_count=25,
            jurisdiction="INDIA",
            metadata={"section": "3", "subsection": "p"},
        ),
        Chunk(
            chunk_id="doc_patents#sec_3_d",
            document_id="doc_patents",
            corpus_collection="legal_statutory",
            text="Section 3(d) What are not inventions: the mere discovery of a new form of a known substance which does not result in enhancement of efficacy.",
            token_count=26,
            jurisdiction="INDIA",
            metadata={"section": "3", "subsection": "d"},
        ),
        Chunk(
            chunk_id="doc_patents#sec_10_4",
            document_id="doc_patents",
            corpus_collection="legal_statutory",
            text="Section 10(4)(d)(ii) Contents of specification: disclose the source and geographical origin of the biological material.",
            token_count=18,
            jurisdiction="INDIA",
            metadata={"section": "10", "subsection": "4"},
        ),
    ]

    index = build_index(chunks)
    results = bm25_search(index, query="Section 3(p)", top_k=3)

    assert len(results) >= 1
    top_result = results[0]
    assert top_result.chunk_id == "doc_patents#sec_3_p"
    assert "3(p)" in top_result.text
    assert top_result.score > 0.0


def test_bm25_collection_filter():
    """BM25 search should respect collection filter argument."""
    chunks = [
        Chunk(
            chunk_id="doc_law#1",
            document_id="doc_law",
            corpus_collection="legal_statutory",
            text="Ayurvedic medicine licensing requirements under Drugs and Cosmetics Act.",
            token_count=10,
            jurisdiction="INDIA",
            metadata={},
        ),
        Chunk(
            chunk_id="doc_std#1",
            document_id="doc_std",
            corpus_collection="standards_formulations",
            text="Ayurvedic Pharmacopoeia standards for Triphala Churna.",
            token_count=8,
            jurisdiction="INDIA",
            metadata={},
        ),
    ]

    index = build_index(chunks)

    # Search for 'Ayurvedic' in standards_formulations only
    std_results = bm25_search(index, query="Ayurvedic", collection="standards_formulations")
    assert len(std_results) == 1
    assert std_results[0].chunk_id == "doc_std#1"

    # Search for 'Ayurvedic' in procedural_forms (none exist)
    proc_results = bm25_search(index, query="Ayurvedic", collection="procedural_forms")
    assert len(proc_results) == 0


def test_bm25_save_and_load(tmp_path: Path):
    """BM25 index should serialize to disk and reload identically."""
    chunks = [
        Chunk(
            chunk_id="doc_wipo#art_3",
            document_id="doc_wipo",
            corpus_collection="international_export",
            text="Article 3 Mandatory patent disclosure of genetic resources origin.",
            token_count=10,
            jurisdiction="INTERNATIONAL",
            metadata={"article_number": "3"},
        )
    ]

    index = build_index(chunks)
    save_path = tmp_path / "bm25_index.pkl"
    index.save(save_path)

    assert save_path.exists()

    loaded_index = load_index(save_path)
    results = loaded_index.search("genetic resources mandatory disclosure")

    assert len(results) == 1
    assert results[0].chunk_id == "doc_wipo#art_3"


@pytest.mark.asyncio
async def test_hybrid_retriever_hard_jurisdiction_filtering():
    """HybridRetriever must enforce HARD jurisdiction filter at query time."""
    client = QdrantClient(":memory:")
    mock_embedder = MagicMock(spec=EmbeddingProvider)
    mock_embedder.dimension = 1024
    mock_embedder.embed.side_effect = lambda texts: [[0.05] * 1024 for _ in texts]
    mock_embedder.embed_query.return_value = [0.05] * 1024

    indexer = QdrantIndexer(client=client, embedding_provider=mock_embedder, dimension=1024)

    # 4 chunks across 2 collections and 3 jurisdictions (INDIA, USA, INTERNATIONAL)
    chunks = [
        Chunk(
            chunk_id="chunk_india_sec3p",
            document_id="doc_in_patents",
            corpus_collection="legal_statutory",
            text="Section 3(p) excludes Indian traditional knowledge inventions from patenting.",
            token_count=12,
            jurisdiction="INDIA",
            metadata={"jurisdiction": "INDIA", "act": "Patents Act 1970"},
        ),
        Chunk(
            chunk_id="chunk_india_drugs",
            document_id="doc_in_drugs",
            corpus_collection="legal_statutory",
            text="Ayurvedic drug manufacturing licensing rules in India.",
            token_count=10,
            jurisdiction="INDIA",
            metadata={"jurisdiction": "INDIA", "act": "Drugs Act 1940"},
        ),
        Chunk(
            chunk_id="chunk_usa_dshea",
            document_id="doc_us_dshea",
            corpus_collection="international_export",
            text="US FDA DSHEA regulations for botanical dietary supplements sold in the USA.",
            token_count=13,
            jurisdiction="USA",
            metadata={"jurisdiction": "USA", "act": "DSHEA 1994"},
        ),
        Chunk(
            chunk_id="chunk_wipo_gratk",
            document_id="doc_wipo_gratk",
            corpus_collection="international_export",
            text="WIPO Treaty on Intellectual Property and Genetic Resources international disclosure standard.",
            token_count=14,
            jurisdiction="INTERNATIONAL",
            metadata={"jurisdiction": "INTERNATIONAL", "treaty": "WIPO GRATK"},
        ),
    ]

    indexer.index_chunks(chunks)
    bm25 = build_index(chunks)
    retriever = HybridRetriever(indexer=indexer, bm25_index=bm25, embedding_provider=mock_embedder)

    # Retrieve with jurisdiction="INDIA" across both collections
    india_evidence = await retriever.retrieve(
        query="dietary supplements and traditional knowledge patenting",
        collections=["legal_statutory", "international_export"],
        jurisdiction="INDIA",
        top_k=5,
    )

    # Assert that USA chunk is NEVER returned
    for ev in india_evidence:
        assert ev.jurisdiction in ["INDIA", "INTERNATIONAL"]
        assert ev.jurisdiction != "USA"
        assert ev.chunk_id != "chunk_usa_dshea"

    assert len(india_evidence) > 0


@pytest.mark.asyncio
async def test_hybrid_retriever_parallel_gather():
    """HybridRetriever must support parallel retrieval across decomposed sub-tasks via asyncio.gather."""
    client = QdrantClient(":memory:")
    mock_embedder = MagicMock(spec=EmbeddingProvider)
    mock_embedder.dimension = 1024
    mock_embedder.embed.side_effect = lambda texts: [[0.05] * 1024 for _ in texts]
    mock_embedder.embed_query.return_value = [0.05] * 1024

    indexer = QdrantIndexer(client=client, embedding_provider=mock_embedder, dimension=1024)

    chunks = [
        Chunk(
            chunk_id="c1",
            document_id="d1",
            corpus_collection="legal_statutory",
            text="Patents Act Section 3(p)",
            token_count=5,
            jurisdiction="INDIA",
        ),
        Chunk(
            chunk_id="c2",
            document_id="d2",
            corpus_collection="standards_formulations",
            text="Ashwagandha root monograph API",
            token_count=5,
            jurisdiction="INDIA",
        ),
    ]
    indexer.index_chunks(chunks)
    bm25 = build_index(chunks)
    retriever = HybridRetriever(indexer=indexer, bm25_index=bm25, embedding_provider=mock_embedder)

    # Simulate sub-tasks executed in parallel
    task_a = retriever.retrieve(query="Section 3(p) patent", collections=["legal_statutory"], jurisdiction="INDIA")
    task_b = retriever.retrieve(query="Ashwagandha botanical API", collections=["standards_formulations"], jurisdiction="INDIA")

    results_a, results_b = await asyncio.gather(task_a, task_b)

    assert len(results_a) > 0
    assert results_a[0].corpus_collection == "legal_statutory"
    assert len(results_b) > 0
    assert results_b[0].corpus_collection == "standards_formulations"
