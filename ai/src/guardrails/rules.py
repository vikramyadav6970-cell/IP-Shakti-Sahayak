"""Guardrails and Abstention Rules module.

Enforces trust, safety, and compliance rules:
1. Minimum evidence abstention threshold (Rule 6).
2. TKDL guardrail: Prevents claiming direct/full private TKDL database access (context.md §5).
3. Jurisdiction separation guardrail: Ensures multi-jurisdiction responses are clearly segmented.
4. Mandatory statutory legal disclaimer appended at pipeline level.
"""

from dataclasses import dataclass, field
import logging
import re
from typing import List, Optional, Sequence, Set

from src.retrieval.hybrid_retriever import EvidenceChunk

logger = logging.getLogger(__name__)

MANDATORY_DISCLAIMER = (
    "\n\n---\n"
    "**Statutory Advisory Notice**: *IP-Shakti Sahayak provides informational and regulatory guidance "
    "derived from public statutory enactments and official pharmacopoeias. This synthesis does not "
    "constitute formal legal counsel or substitute for an accredited Patent Agent / AYUSH regulatory consultant.*"
)

TKDL_POLICY_NOTICE = (
    "\n\n> **CSIR-TKDL Access Notice**: The Traditional Knowledge Digital Library (TKDL) is a proprietary "
    "repository accessible to International Patent Offices under bilateral non-disclosure agreements and limited "
    "CSIR research frameworks. Analysis is based on First-Schedule classical treatises and public CSIR revocation dossiers."
)


@dataclass
class GuardrailResult:
    """Outcome of safety, compliance, and structural guardrail evaluation."""

    sanitized_answer: str
    is_abstaining: bool
    guardrails_triggered: List[str]
    disclaimer_appended: bool = True


class GuardrailEngine:
    """Evaluates and enforces regulatory compliance and safety guardrails."""

    def __init__(self, min_evidence_threshold: int = 1):
        self.min_evidence_threshold = min_evidence_threshold

    def apply(
        self,
        raw_answer: str,
        evidence_chunks: Sequence[EvidenceChunk],
        jurisdictions: Sequence[str] = ("INDIA",),
    ) -> GuardrailResult:
        """Apply full guardrail suite to raw synthesized answer."""
        guardrails_triggered: List[str] = []

        # 1. Minimum Evidence Abstention Guardrail
        if len(evidence_chunks) < self.min_evidence_threshold:
            guardrails_triggered.append("GUARDRAIL_INSUFFICIENT_EVIDENCE_ABSTENTION")
            abstain_text = (
                "The authoritative legal and pharmacopoeial corpus does not contain sufficient verified "
                "evidence to answer this inquiry with regulatory certainty. "
                "Please refine your query or consult an accredited AYUSH regulatory advisor."
            )
            return GuardrailResult(
                sanitized_answer=abstain_text + MANDATORY_DISCLAIMER,
                is_abstaining=True,
                guardrails_triggered=guardrails_triggered,
                disclaimer_appended=True,
            )

        sanitized = raw_answer

        # 2. TKDL Database Access Guardrail
        tkdl_triggered = False
        tkdl_hallucination_patterns = [
            r"\bsearched the full tkdl database\b",
            r"\bqueried the private tkdl database\b",
            r"\bdirect access to tkdl database\b",
            r"\bcomplete tkdl repository search\b",
        ]
        for p in tkdl_hallucination_patterns:
            if re.search(p, sanitized, re.IGNORECASE):
                tkdl_triggered = True
                guardrails_triggered.append("GUARDRAIL_TKDL_ACCESS_RESTRICTION")
                sanitized = re.sub(p, "searched the First-Schedule classical literature and public CSIR prior art dossiers", sanitized, flags=re.IGNORECASE)

        # If question/answer touches TKDL or triggered restriction, ensure statutory access notice is attached
        if (tkdl_triggered or re.search(r"\btkdl\b", raw_answer, re.IGNORECASE)) and "CSIR-TKDL Access Notice" not in sanitized:
            sanitized += TKDL_POLICY_NOTICE

        # 3. Multi-Jurisdiction Structural Separation Guardrail
        distinct_jurisdictions: Set[str] = {
            c.jurisdiction.upper().strip() for c in evidence_chunks if c.jurisdiction
        }
        if len(distinct_jurisdictions) > 1 or ("EU" in jurisdictions and "INDIA" in jurisdictions):
            # Check if headers for distinct jurisdictions are already present
            has_india_header = bool(re.search(r"(###|\*\*).*?(India|Domestic|Ayush)", sanitized, re.IGNORECASE))
            has_foreign_header = bool(re.search(r"(###|\*\*).*?(EU|European|USA|FDA|International|Export)", sanitized, re.IGNORECASE))

            if not (has_india_header and has_foreign_header):
                guardrails_triggered.append("GUARDRAIL_JURISDICTION_SEPARATION_ENFORCED")
                # Wrap or annotate with clear structural note
                if "--- Cross-Border Harmonization ---" not in sanitized:
                    sanitized = (
                        "### 🌐 Multi-Jurisdiction Regulatory Summary\n\n"
                        + sanitized
                    )

        # 4. Mandatory Disclaimer Guardrail
        if "Statutory Advisory Notice" not in sanitized:
            sanitized += MANDATORY_DISCLAIMER
            disclaimer_appended = True
        else:
            disclaimer_appended = False

        return GuardrailResult(
            sanitized_answer=sanitized,
            is_abstaining=False,
            guardrails_triggered=guardrails_triggered,
            disclaimer_appended=disclaimer_appended,
        )


# Module-level convenience engine
default_guardrail_engine = GuardrailEngine()


def apply_guardrails(
    raw_answer: str,
    evidence_chunks: Sequence[EvidenceChunk],
    jurisdictions: Sequence[str] = ("INDIA",),
) -> GuardrailResult:
    """Apply safety and compliance guardrails to answer."""
    return default_guardrail_engine.apply(
        raw_answer=raw_answer,
        evidence_chunks=evidence_chunks,
        jurisdictions=jurisdictions,
    )
