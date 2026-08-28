"""Composite Confidence Scorer.

Encodes coding_conventions.md Rule 4:
Computes an explainable, deterministic composite confidence score between 0.0 and 1.0
combining 6 grounded factors:

Formula & Weights:
  Composite Score = (
      0.20 * retrieval_score +
      0.25 * citation_score +
      0.15 * source_authority_score +
      0.15 * jurisdiction_match_score +
      0.10 * answer_evidence_coverage +
      0.15 * sub_task_coverage
  )

Thresholds:
  - HIGH:    score >= 0.80 (Highly authoritative and grounded)
  - MEDIUM:  0.50 <= score < 0.80 (Adequately grounded with minor gaps)
  - LOW:     0.00 < score < 0.50 (Requires human review)
  - ABSTAIN: score == 0.00 (Insufficient evidence or unverified citations)

Human Review Trigger:
  - requires_human_review = True whenever composite_score < 0.70 or jurisdiction mismatch detected.
"""

from dataclasses import dataclass, field
import logging
import re
from typing import Any, Dict, List, Optional, Sequence

from src.citations.validator import CitationValidationResult
from src.retrieval.hybrid_retriever import EvidenceChunk

logger = logging.getLogger(__name__)

# Weight constants
WEIGHT_RETRIEVAL = 0.20
WEIGHT_CITATION = 0.25
WEIGHT_SOURCE_AUTHORITY = 0.15
WEIGHT_JURISDICTION = 0.15
WEIGHT_EVIDENCE_COVERAGE = 0.10
WEIGHT_SUBTASK_COVERAGE = 0.15

# Review threshold
HUMAN_REVIEW_THRESHOLD = 0.70

# Source Authority Hierarchy Map
AUTHORITY_WEIGHTS: Dict[str, float] = {
    "legal_statutory": 1.00,        # Principal Statutes & Acts (Patents Act, BDA, Drugs Act)
    "international_export": 0.95,  # International Treaties & Directives (TRIPS, Nagoya, EU THMPD)
    "standards_formulations": 0.95, # Official Pharmacopoeias & Treatises (API, AFI, Charaka)
    "procedural_forms": 0.85,       # Statutory Regulatory Forms (NBA Form I/III, Form 24D)
    "case_law_prior_art": 0.85,     # CSIR TKDL Landmark Precedents
    "secondary_guideline": 0.65,    # General administrative circulars / secondary FAQs
    "general": 0.50,
}


@dataclass
class ConfidenceBreakdown:
    """Detailed explainability breakdown of composite confidence score."""

    composite_score: float
    confidence_label: str  # "HIGH" | "MEDIUM" | "LOW" | "ABSTAIN"
    requires_human_review: bool
    retrieval_score: float
    citation_score: float
    source_authority_score: float
    jurisdiction_match_score: float
    answer_evidence_coverage: float
    sub_task_coverage: float
    explanation: str
    factor_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "retrieval": WEIGHT_RETRIEVAL,
            "citation": WEIGHT_CITATION,
            "source_authority": WEIGHT_SOURCE_AUTHORITY,
            "jurisdiction": WEIGHT_JURISDICTION,
            "evidence_coverage": WEIGHT_EVIDENCE_COVERAGE,
            "subtask_coverage": WEIGHT_SUBTASK_COVERAGE,
        }
    )


class ConfidenceScorer:
    """Computes explainable composite confidence scores for pipeline query results."""

    def __init__(self, review_threshold: float = HUMAN_REVIEW_THRESHOLD):
        self.review_threshold = review_threshold

    def score(
        self,
        evidence_chunks: Sequence[EvidenceChunk],
        validation_result: Optional[CitationValidationResult] = None,
        total_sub_tasks: int = 1,
        sub_tasks_with_evidence: int = 1,
        jurisdiction_mismatch: bool = False,
        is_export_cross_border: bool = False,
        raw_answer: str = "",
    ) -> ConfidenceBreakdown:
        """Compute grounded composite confidence score."""
        # 1. Total Abstention check
        if not evidence_chunks or (validation_result and validation_result.abstention_triggered):
            return ConfidenceBreakdown(
                composite_score=0.0,
                confidence_label="ABSTAIN",
                requires_human_review=True,
                retrieval_score=0.0,
                citation_score=0.0,
                source_authority_score=0.0,
                jurisdiction_match_score=0.0,
                answer_evidence_coverage=0.0,
                sub_task_coverage=0.0,
                explanation="Abstention: No verified evidence chunks or citation validation triggered safety shutdown.",
            )

        # 2. Retrieval Score (Top 3 mean retrieval score normalized)
        top_chunks = list(evidence_chunks)[:3]
        retrieval_score = sum(max(0.0, min(1.0, c.score)) for c in top_chunks) / len(top_chunks)

        # 3. Citation Score (Validated citations / total citation attempts)
        if validation_result:
            total_citations = len(validation_result.valid_citations) + len(validation_result.invalid_citations)
            if total_citations > 0:
                citation_score = len(validation_result.valid_citations) / total_citations
            else:
                # If no citations were embedded, penalize citation score
                citation_score = 0.50 if len(evidence_chunks) > 0 else 0.0
        else:
            citation_score = 0.80

        # 4. Source Authority Score
        collection_scores = [
            AUTHORITY_WEIGHTS.get(c.corpus_collection, 0.70)
            for c in evidence_chunks[:4]
        ]
        source_authority_score = sum(collection_scores) / len(collection_scores) if collection_scores else 0.70

        # 5. Jurisdiction Match Score
        if jurisdiction_mismatch:
            jurisdiction_match_score = 0.45  # Penalize mismatch (e.g. asking US FDA while UI set to India)
        elif is_export_cross_border:
            jurisdiction_match_score = 0.90  # Multi-jurisdiction cross-border harmonization
        else:
            jurisdiction_match_score = 1.00  # Exact domestic match

        # 6. Answer Evidence Coverage (fraction of informative sentences with citations)
        answer_evidence_coverage = self._compute_evidence_coverage(raw_answer)

        # 7. Sub-task Coverage (fraction of decomposed queries that returned results)
        total_sub_tasks = max(1, total_sub_tasks)
        sub_task_coverage = min(1.0, max(0.0, sub_tasks_with_evidence / total_sub_tasks))

        # Composite Score Calculation
        composite = (
            (WEIGHT_RETRIEVAL * retrieval_score) +
            (WEIGHT_CITATION * citation_score) +
            (WEIGHT_SOURCE_AUTHORITY * source_authority_score) +
            (WEIGHT_JURISDICTION * jurisdiction_match_score) +
            (WEIGHT_EVIDENCE_COVERAGE * answer_evidence_coverage) +
            (WEIGHT_SUBTASK_COVERAGE * sub_task_coverage)
        )

        composite_score = round(max(0.0, min(1.0, composite)), 2)

        # Confidence Label & Human Review Flag
        if composite_score >= 0.80:
            confidence_label = "HIGH"
        elif composite_score >= 0.50:
            confidence_label = "MEDIUM"
        else:
            confidence_label = "LOW"

        requires_human_review = (
            composite_score < self.review_threshold
            or jurisdiction_mismatch
            or (validation_result is not None and not validation_result.is_valid)
        )

        explanation = (
            f"Confidence: {confidence_label} ({int(composite_score * 100)}%). "
            f"Retrieval: {int(retrieval_score * 100)}%, "
            f"Citations: {int(citation_score * 100)}%, "
            f"Authority: {int(source_authority_score * 100)}%, "
            f"Jurisdiction: {int(jurisdiction_match_score * 100)}%, "
            f"Sub-task Coverage: {sub_tasks_with_evidence}/{total_sub_tasks}."
        )

        return ConfidenceBreakdown(
            composite_score=composite_score,
            confidence_label=confidence_label,
            requires_human_review=requires_human_review,
            retrieval_score=round(retrieval_score, 2),
            citation_score=round(citation_score, 2),
            source_authority_score=round(source_authority_score, 2),
            jurisdiction_match_score=round(jurisdiction_match_score, 2),
            answer_evidence_coverage=round(answer_evidence_coverage, 2),
            sub_task_coverage=round(sub_task_coverage, 2),
            explanation=explanation,
        )

    def _compute_evidence_coverage(self, text: str) -> float:
        """Estimate fraction of substantive sentences anchored by citations."""
        if not text.strip():
            return 0.0

        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 15]
        if not sentences:
            return 0.50

        cited_count = sum(1 for s in sentences if re.search(r"\[[a-zA-Z0-9_\-\.\:\/]+\]", s))
        return min(1.0, max(0.20, cited_count / len(sentences)))


# Module-level convenience scorer instance
default_confidence_scorer = ConfidenceScorer()


def compute_confidence(
    evidence_chunks: Sequence[EvidenceChunk],
    validation_result: Optional[CitationValidationResult] = None,
    total_sub_tasks: int = 1,
    sub_tasks_with_evidence: int = 1,
    jurisdiction_mismatch: bool = False,
    is_export_cross_border: bool = False,
    raw_answer: str = "",
) -> ConfidenceBreakdown:
    """Compute explainable composite confidence score."""
    return default_confidence_scorer.score(
        evidence_chunks=evidence_chunks,
        validation_result=validation_result,
        total_sub_tasks=total_sub_tasks,
        sub_tasks_with_evidence=sub_tasks_with_evidence,
        jurisdiction_mismatch=jurisdiction_mismatch,
        is_export_cross_border=is_export_cross_border,
        raw_answer=raw_answer,
    )
