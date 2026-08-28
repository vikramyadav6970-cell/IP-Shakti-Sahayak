"""Unit tests for the zero-hallucination Citation Validator."""

import pytest

from src.citations.validator import (
    CitationValidationResult,
    CitationValidator,
    validate_citations,
)
from src.retrieval.hybrid_retriever import EvidenceChunk


@pytest.fixture
def sample_evidence():
    return [
        EvidenceChunk(
            chunk_id="chunk_patents_sec3p",
            document_id="doc_patents_act_1970",
            corpus_collection="legal_statutory",
            text="Section 3(p) excludes traditional knowledge and mere aggregations from patentability.",
            score=0.95,
            jurisdiction="INDIA",
            metadata={"act": "Patents Act 1970", "section": "3(p)"},
        ),
        EvidenceChunk(
            chunk_id="chunk_bda_sec6",
            document_id="doc_bda_2002",
            corpus_collection="legal_statutory",
            text="Section 6 requires mandatory prior approval of National Biodiversity Authority for IPR.",
            score=0.90,
            jurisdiction="INDIA",
            metadata={"act": "Biological Diversity Act 2002", "section": "6"},
        ),
    ]


def test_validation_all_valid(sample_evidence):
    """When all cited chunk IDs exist and have valid text overlap, validation passes unchanged."""
    raw_answer = (
        "Under the Patents Act, traditional knowledge is excluded from patentability [chunk_patents_sec3p]. "
        "Additionally, NBA approval is mandatory before filing patent applications [chunk_bda_sec6]."
    )

    res: CitationValidationResult = validate_citations(raw_answer, sample_evidence)

    assert res.is_valid is True
    assert res.abstention_triggered is False
    assert len(res.valid_citations) == 2
    assert len(res.invalid_citations) == 0
    assert "Patents Act" in res.cleaned_answer
    assert "NBA approval" in res.cleaned_answer


def test_validation_fabricated_citation_caught(sample_evidence):
    """Fabricated chunk ID in a mixed answer is stripped while valid sentences are retained."""
    raw_answer = (
        "Under Section 3(p) traditional knowledge cannot be patented [chunk_patents_sec3p]. "
        "Inventors can bypass the law completely using secret methods [chunk_fabricated_fake_id]. "
        "Biological resources require NBA clearance [chunk_bda_sec6]."
    )

    res: CitationValidationResult = validate_citations(raw_answer, sample_evidence)

    assert res.is_valid is False
    assert "chunk_fabricated_fake_id" in res.invalid_citations
    assert len(res.valid_citations) == 2
    assert res.abstention_triggered is False
    # Unsupported sentence should be stripped
    assert "bypass the law" not in res.cleaned_answer
    assert "traditional knowledge cannot be patented" in res.cleaned_answer
    assert "NBA clearance" in res.cleaned_answer


def test_validation_high_hallucination_triggers_abstention(sample_evidence):
    """When all or majority of citations are fabricated, abstention is triggered."""
    raw_answer = (
        "You can patent Turmeric easily in the US without disclosure [chunk_fake_01]. "
        "NBA clearance is completely unnecessary for commercial exports [chunk_fake_02]."
    )

    res: CitationValidationResult = validate_citations(raw_answer, sample_evidence)

    assert res.abstention_triggered is True
    assert res.is_valid is False
    assert len(res.invalid_citations) == 2
    assert len(res.valid_citations) == 0
    assert "abstained" in res.cleaned_answer.lower()
