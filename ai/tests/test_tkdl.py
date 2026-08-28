"""Unit tests for the deterministic TKDL Public-Information Pointer."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.classification.intent_classifier import DomainIntent
from src.reasoning.query_pipeline import QueryPipeline, QueryResult
from src.reasoning.tkdl_pointer import (
    TKDLResponse,
    generate_tkdl_response,
    OFFICIAL_TKDL_PORTAL,
)
from src.retrieval.hybrid_retriever import EvidenceChunk, HybridRetriever


@pytest.fixture
def tkdl_evidence():
    return [
        EvidenceChunk(
            chunk_id="chunk_turmeric_revocation",
            document_id="doc_turmeric_case",
            corpus_collection="case_law_prior_art",
            text="CSIR Turmeric Patent Revocation (US Patent 5,401,504) established lack of novelty based on ancient Ayurvedic texts.",
            score=0.98,
            jurisdiction="INDIA",
            metadata={"case_name": "CSIR Turmeric Revocation", "citation_ref": "US 5,401,504"},
        ),
        EvidenceChunk(
            chunk_id="chunk_api_withania",
            document_id="doc_api_vol1",
            corpus_collection="standards_formulations",
            text="Ayurvedic Pharmacopoeia of India monograph for Withania somnifera (Ashwagandha) root.",
            score=0.92,
            jurisdiction="INDIA",
            metadata={"source": "Ayurvedic Pharmacopoeia of India Part I", "section": "Ashwagandha"},
        ),
    ]


def test_generate_tkdl_response_english(tkdl_evidence):
    """Deterministic English TKDL response contains official portal, statutory notice, and public citations."""
    resp: TKDLResponse = generate_tkdl_response(
        question="Can I search the TKDL database for prior art on Ashwagandha?",
        evidence_chunks=tkdl_evidence,
        language="en",
    )

    assert OFFICIAL_TKDL_PORTAL in resp.portal_url
    assert "https://www.tkdl.res.in" in resp.answer
    assert "Non-Disclosure Access Agreements" in resp.answer
    assert "Turmeric" in resp.answer
    assert "chunk_turmeric_revocation" in resp.answer
    assert len(resp.citations) == 2


def test_generate_tkdl_response_hindi(tkdl_evidence):
    """Deterministic Hindi TKDL response contains official portal and Hindi statutory notices."""
    resp: TKDLResponse = generate_tkdl_response(
        question="क्या मैं टीकेडीएल डेटाबेस खोज सकता हूँ?",
        evidence_chunks=tkdl_evidence,
        language="hi",
    )

    assert "https://www.tkdl.res.in" in resp.answer
    assert "गैर-प्रकटीकरण पहुंच समझौतों" in resp.answer
    assert "चरक संहिता" in resp.answer


@pytest.mark.asyncio
async def test_pipeline_tkdl_intent_routing(tkdl_evidence):
    """Pipeline automatically routes queries with TKDL intent through the deterministic template."""
    mock_retriever = MagicMock(spec=HybridRetriever)
    mock_retriever.retrieve = AsyncMock(return_value=tkdl_evidence)

    pipeline = QueryPipeline(retriever=mock_retriever)

    res: QueryResult = await pipeline.query(
        question="How can our research team access the complete TKDL database?",
        domain_intent=DomainIntent.RESEARCH,
        jurisdiction="INDIA",
        language="en",
    )

    assert "tkdl.res.in" in res.answer
    assert "Non-Disclosure Access Agreements" in res.answer
    assert len(res.citations) > 0
    assert res.confidence_label in ["HIGH", "MEDIUM"]
