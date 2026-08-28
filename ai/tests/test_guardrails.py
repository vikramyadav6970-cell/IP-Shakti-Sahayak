"""Unit tests for safety, compliance, and hallucination guardrails."""

import pytest

from src.guardrails.rules import (
    GuardrailResult,
    GuardrailEngine,
    apply_guardrails,
    MANDATORY_DISCLAIMER,
)
from src.retrieval.hybrid_retriever import EvidenceChunk


@pytest.fixture
def indian_evidence():
    return [
        EvidenceChunk(
            chunk_id="chunk_patents_01",
            document_id="doc_patents_1970",
            corpus_collection="legal_statutory",
            text="Section 3(p) excludes traditional knowledge.",
            score=0.95,
            jurisdiction="INDIA",
        )
    ]


def test_guardrail_insufficient_evidence_abstention():
    """Empty evidence list triggers immediate abstention with statutory advisory disclaimer."""
    res: GuardrailResult = apply_guardrails(
        raw_answer="Some hallucinated claim.",
        evidence_chunks=[],
        jurisdictions=["INDIA"],
    )

    assert res.is_abstaining is True
    assert "GUARDRAIL_INSUFFICIENT_EVIDENCE_ABSTENTION" in res.guardrails_triggered
    assert "does not contain sufficient verified evidence" in res.sanitized_answer
    assert "Statutory Advisory Notice" in res.sanitized_answer


def test_guardrail_tkdl_access_sanitization(indian_evidence):
    """Claims of direct/full private TKDL database access are sanitized to public CSIR framework."""
    raw_answer = "We have searched the full TKDL database and confirmed no prior art conflicts."

    res: GuardrailResult = apply_guardrails(
        raw_answer=raw_answer,
        evidence_chunks=indian_evidence,
        jurisdictions=["INDIA"],
    )

    assert "full TKDL database" not in res.sanitized_answer
    assert "First-Schedule classical literature" in res.sanitized_answer
    assert "CSIR-TKDL Access Notice" in res.sanitized_answer
    assert "GUARDRAIL_TKDL_ACCESS_RESTRICTION" in res.guardrails_triggered


def test_guardrail_jurisdiction_separation():
    """Multi-jurisdiction evidence (India + EU) triggers structural separation header."""
    mixed_evidence = [
        EvidenceChunk(
            chunk_id="chunk_ind_01",
            document_id="doc_patents_1970",
            corpus_collection="legal_statutory",
            text="Indian Patents Act Section 3(p).",
            score=0.95,
            jurisdiction="INDIA",
        ),
        EvidenceChunk(
            chunk_id="chunk_eu_01",
            document_id="doc_eu_thmpd",
            corpus_collection="international_export",
            text="EU THMPD Directive 2004/24/EC.",
            score=0.90,
            jurisdiction="EU",
        ),
    ]
    raw_answer = "Herbal supplements require both Indian and European clearances."

    res: GuardrailResult = apply_guardrails(
        raw_answer=raw_answer,
        evidence_chunks=mixed_evidence,
        jurisdictions=["INDIA", "EU"],
    )

    assert "Multi-Jurisdiction Regulatory Summary" in res.sanitized_answer
    assert "GUARDRAIL_JURISDICTION_SEPARATION_ENFORCED" in res.guardrails_triggered


def test_guardrail_mandatory_disclaimer(indian_evidence):
    """Every synthesized answer carries the mandatory statutory advisory notice."""
    raw_answer = "Under the Drugs and Cosmetics Act, Form 24D is required for manufacturing."

    res: GuardrailResult = apply_guardrails(
        raw_answer=raw_answer,
        evidence_chunks=indian_evidence,
        jurisdictions=["INDIA"],
    )

    assert "Statutory Advisory Notice" in res.sanitized_answer
    assert res.disclaimer_appended is True
