"""Unit tests for the Composite Confidence Scorer."""

import pytest

from src.citations.validator import CitationValidationResult
from src.confidence.scorer import (
    ConfidenceBreakdown,
    ConfidenceScorer,
    compute_confidence,
)
from src.reasoning.query_pipeline import Citation
from src.retrieval.hybrid_retriever import EvidenceChunk


@pytest.fixture
def valid_evidence():
    return [
        EvidenceChunk(
            chunk_id="chunk_patents_sec3p",
            document_id="doc_patents_act_1970",
            corpus_collection="legal_statutory",
            text="Section 3(p) excludes traditional knowledge from patentability.",
            score=0.95,
            jurisdiction="INDIA",
            metadata={"act": "Patents Act 1970", "section": "3(p)"},
        ),
        EvidenceChunk(
            chunk_id="chunk_bda_sec6",
            document_id="doc_bda_2002",
            corpus_collection="legal_statutory",
            text="Section 6 requires mandatory NBA approval.",
            score=0.90,
            jurisdiction="INDIA",
            metadata={"act": "Biological Diversity Act 2002", "section": "6"},
        ),
    ]


@pytest.fixture
def valid_validation_result():
    return CitationValidationResult(
        cleaned_answer="Under Patents Act [chunk_patents_sec3p] and BDA [chunk_bda_sec6].",
        valid_citations=[
            Citation(
                chunk_id="chunk_patents_sec3p",
                document_id="doc_patents_act_1970",
                collection="legal_statutory",
                jurisdiction="INDIA",
                title="Patents Act 1970",
            ),
            Citation(
                chunk_id="chunk_bda_sec6",
                document_id="doc_bda_2002",
                collection="legal_statutory",
                jurisdiction="INDIA",
                title="Biological Diversity Act 2002",
            ),
        ],
        invalid_citations=[],
        unsupported_sentences=[],
        is_valid=True,
        abstention_triggered=False,
    )


def test_confidence_high_grounded(valid_evidence, valid_validation_result):
    """High retrieval score, 100% valid citations, exact jurisdiction, 100% subtask coverage yields HIGH confidence."""
    res: ConfidenceBreakdown = compute_confidence(
        evidence_chunks=valid_evidence,
        validation_result=valid_validation_result,
        total_sub_tasks=2,
        sub_tasks_with_evidence=2,
        jurisdiction_mismatch=False,
        raw_answer="Under Patents Act [chunk_patents_sec3p] and BDA [chunk_bda_sec6].",
    )

    assert res.composite_score >= 0.80
    assert res.confidence_label == "HIGH"
    assert res.requires_human_review is False
    assert res.sub_task_coverage == 1.0
    assert "High" in res.explanation or "HIGH" in res.explanation


def test_confidence_low_mismatch_and_partial_subtasks(valid_evidence):
    """Jurisdiction mismatch and 50% subtasks with evidence triggers human review."""
    partial_validation = CitationValidationResult(
        cleaned_answer="Mixed unverified response [chunk_fake_id].",
        valid_citations=[],
        invalid_citations=["chunk_fake_id"],
        unsupported_sentences=[],
        is_valid=False,
        abstention_triggered=False,
    )

    res: ConfidenceBreakdown = compute_confidence(
        evidence_chunks=valid_evidence,
        validation_result=partial_validation,
        total_sub_tasks=4,
        sub_tasks_with_evidence=2,
        jurisdiction_mismatch=True,
        raw_answer="Some answer text.",
    )

    assert res.composite_score < 0.70
    assert res.requires_human_review is True
    assert res.jurisdiction_match_score < 0.50
    assert res.sub_task_coverage == 0.50


def test_confidence_abstention_on_empty_or_triggered():
    """Empty evidence returns composite score 0.0 with ABSTAIN label."""
    res: ConfidenceBreakdown = compute_confidence(
        evidence_chunks=[],
        validation_result=None,
    )

    assert res.composite_score == 0.0
    assert res.confidence_label == "ABSTAIN"
    assert res.requires_human_review is True
