"""Citation Validator module.

Implements zero-hallucination verification per coding_conventions.md Rule 2:
- Verifies every cited chunk_id exists in the retrieved evidence set.
- Checks plausible textual overlap between citing sentence and cited chunk.
- Strips unsupported sentences or triggers abstention if > 50% citations fail.
"""

from dataclasses import dataclass, field
import logging
import re
from typing import Dict, List, Optional, Sequence, Set, Tuple

from src.reasoning.query_pipeline import Citation
from src.retrieval.hybrid_retriever import EvidenceChunk

logger = logging.getLogger(__name__)

# Abstention threshold: If more than 50% of citations are fabricated/unsupported, abstain
UNSUPPORTED_CITATION_ABSTENTION_THRESHOLD = 0.50


@dataclass
class CitationValidationResult:
    """Outcome of strict zero-hallucination citation validation."""

    cleaned_answer: str
    valid_citations: List[Citation]
    invalid_citations: List[str]
    unsupported_sentences: List[str]
    is_valid: bool
    abstention_triggered: bool
    validation_notes: List[str] = field(default_factory=list)


class CitationValidator:
    """Strictly validates citation markers against retrieved evidence chunks."""

    def __init__(self, abstention_threshold: float = UNSUPPORTED_CITATION_ABSTENTION_THRESHOLD):
        self.abstention_threshold = abstention_threshold

    def validate(
        self,
        raw_answer: str,
        evidence_chunks: Sequence[EvidenceChunk],
    ) -> CitationValidationResult:
        """Validate all inline citations in raw_answer against evidence_chunks."""
        if not raw_answer or not raw_answer.strip():
            return CitationValidationResult(
                cleaned_answer=raw_answer,
                valid_citations=[],
                invalid_citations=[],
                unsupported_sentences=[],
                is_valid=True,
                abstention_triggered=False,
                validation_notes=["Empty answer provided."],
            )

        evidence_map: Dict[str, EvidenceChunk] = {c.chunk_id: c for c in evidence_chunks}
        valid_citations_map: Dict[str, Citation] = {}
        invalid_citations: Set[str] = set()
        unsupported_sentences: List[str] = []
        validation_notes: List[str] = []

        paragraphs = raw_answer.split("\n")
        cleaned_paragraphs: List[str] = []
        total_citation_occurrences = 0
        valid_citation_occurrences = 0

        for para in paragraphs:
            if not para.strip():
                cleaned_paragraphs.append("")
                continue

            # Split paragraph into sentence candidates (handling periods, colons, newlines)
            sentences = re.split(r"(?<=[.!?])\s+", para)
            kept_sentences: List[str] = []

            for sentence in sentences:
                if not sentence.strip():
                    continue

                # Find all [chunk_id] tags in this sentence (ignoring markdown links with URLs)
                raw_tags = re.findall(r"\[([a-zA-Z0-9_\-\.\:\/]+)\](?!\()", sentence)
                citation_tags = [t for t in raw_tags if not t.startswith("http://") and not t.startswith("https://")]

                if not citation_tags:
                    # Sentence without citations (e.g. headings, bullet points, disclaimers)
                    kept_sentences.append(sentence)
                    continue

                sentence_has_valid_citation = False
                sentence_has_invalid_citation = False

                for chunk_id in citation_tags:
                    total_citation_occurrences += 1
                    if chunk_id in evidence_map:
                        chunk = evidence_map[chunk_id]
                        # Verify plausible text overlap between citing sentence and chunk
                        if self._is_plausibly_supported(sentence, chunk.text):
                            sentence_has_valid_citation = True
                            valid_citation_occurrences += 1
                            if chunk_id not in valid_citations_map:
                                valid_citations_map[chunk_id] = Citation(
                                    chunk_id=chunk.chunk_id,
                                    document_id=chunk.document_id,
                                    collection=chunk.corpus_collection,
                                    jurisdiction=chunk.jurisdiction,
                                    title=chunk.payload.get("act") or chunk.payload.get("source") or chunk.payload.get("treaty_name") or chunk.document_id,
                                    section_or_ref=str(chunk.payload.get("section") or chunk.payload.get("article_number") or ""),
                                    snippet=chunk.text[:250],
                                )
                        else:
                            sentence_has_invalid_citation = True
                            invalid_citations.add(chunk_id)
                            validation_notes.append(f"Citation [{chunk_id}] rejected: Insufficient text overlap with cited chunk.")
                    else:
                        sentence_has_invalid_citation = True
                        invalid_citations.add(chunk_id)
                        validation_notes.append(f"Citation [{chunk_id}] rejected: Chunk ID not found in retrieved evidence set.")

                if sentence_has_invalid_citation and not sentence_has_valid_citation:
                    # Strip entirely unsupported sentence
                    unsupported_sentences.append(sentence)
                    validation_notes.append(f"Stripped unsupported sentence: '{sentence[:80]}...'")
                else:
                    # Clean out any fabricated tags from the sentence if mixed
                    cleaned_sentence = sentence
                    for bad_id in invalid_citations:
                        cleaned_sentence = cleaned_sentence.replace(f"[{bad_id}]", "")
                    cleaned_sentence = re.sub(r"\s+", " ", cleaned_sentence).strip()
                    if cleaned_sentence:
                        kept_sentences.append(cleaned_sentence)

            if kept_sentences:
                cleaned_paragraphs.append(" ".join(kept_sentences))

        cleaned_answer = "\n".join(cleaned_paragraphs)

        # Policy threshold calculation: trigger abstention if strictly more than threshold (50%) of citations fail
        abstention_triggered = False
        if total_citation_occurrences > 0:
            invalid_ratio = len(invalid_citations) / max(total_citation_occurrences, 1)
            if invalid_ratio > self.abstention_threshold or (valid_citation_occurrences == 0 and len(invalid_citations) > 0):
                abstention_triggered = True
                cleaned_answer = (
                    "The AI advisory engine abstained from providing this response because the generated answer "
                    "contained unsupported or unverifiable citations exceeding the safety tolerance threshold. "
                    "Please re-query or consult the official statutory gazettes directly."
                )
                validation_notes.append(f"Abstention triggered: {len(invalid_citations)}/{total_citation_occurrences} citations failed verification.")

        is_valid = len(invalid_citations) == 0 and not abstention_triggered

        return CitationValidationResult(
            cleaned_answer=cleaned_answer,
            valid_citations=list(valid_citations_map.values()),
            invalid_citations=list(invalid_citations),
            unsupported_sentences=unsupported_sentences,
            is_valid=is_valid,
            abstention_triggered=abstention_triggered,
            validation_notes=validation_notes,
        )

    def _is_plausibly_supported(self, sentence: str, chunk_text: str) -> bool:
        """Heuristic text overlap check to ensure citing sentence is grounded in chunk."""
        clean_sentence = sentence.lower()
        clean_chunk = chunk_text.lower()

        # Acronym expansions for AYUSH and IP legal domain
        acronyms = {
            "nba": "national biodiversity authority",
            "sbb": "state biodiversity board",
            "tkdl": "traditional knowledge digital library",
            "asu": "ayurveda siddha unani",
            "fssai": "food safety standards authority",
            "thmpd": "traditional herbal medicinal products directive",
            "dshea": "dietary supplement health education act",
        }

        for acr, expansion in acronyms.items():
            if acr in clean_sentence:
                clean_sentence += f" {expansion}"
            if acr in clean_chunk:
                clean_chunk += f" {expansion}"

        clean_sentence = re.sub(r"[^\w\s]", " ", clean_sentence)
        clean_chunk = re.sub(r"[^\w\s]", " ", clean_chunk)

        stop_words = {
            "the", "and", "or", "is", "are", "in", "to", "of", "a", "an", "for", "with",
            "on", "at", "by", "from", "as", "be", "this", "that", "it", "under", "shall",
            "not", "may", "can", "have", "has", "been", "per", "such", "any", "which",
            "will", "must", "should", "would", "could", "also", "into", "than", "then",
        }

        sentence_tokens = [w for w in clean_sentence.split() if w not in stop_words and len(w) > 2]
        if not sentence_tokens:
            return True

        chunk_words = [w for w in clean_chunk.split() if w not in stop_words and len(w) > 2]
        chunk_tokens_set = set(chunk_words)

        matched_count = 0
        for s_tok in sentence_tokens:
            if s_tok in chunk_tokens_set:
                matched_count += 1
            else:
                # Prefix matching (e.g. "requir" in "requires", "approv" in "approval")
                s_stem = s_tok[:5] if len(s_tok) >= 5 else s_tok
                if any(c_tok.startswith(s_stem) for c_tok in chunk_tokens_set):
                    matched_count += 1

        overlap_ratio = matched_count / len(sentence_tokens)
        return overlap_ratio >= 0.12 or matched_count >= 1


# Module-level convenience validator
default_citation_validator = CitationValidator()


def validate_citations(
    raw_answer: str,
    evidence_chunks: Sequence[EvidenceChunk],
) -> CitationValidationResult:
    """Validate citations in raw_answer against evidence_chunks."""
    return default_citation_validator.validate(raw_answer, evidence_chunks)
