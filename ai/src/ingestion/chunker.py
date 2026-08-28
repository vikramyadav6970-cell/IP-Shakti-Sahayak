"""Collection-aware document chunker.

Dispatches documents to one of 5 collection-specific chunking strategies:
1. LegalStatutoryChunker (legal_statutory)
2. StandardsFormulationsChunker (standards_formulations)
3. CaseLawChunker (case_law_prior_art)
4. ProceduralFormsChunker (procedural_forms)
5. InternationalExportChunker (international_export)

Encodes coding_conventions.md Rule 7 & Rule 12: chunking respects both legal
hierarchy and target collection schema.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type
import re
import uuid

from src.ingestion.parser import ParsedDocument, ParsedSection


@dataclass
class Chunk:
    """Represents a chunk prepared for vector embedding and keyword indexing."""

    chunk_id: str
    document_id: str
    corpus_collection: str
    text: str
    token_count: int
    jurisdiction: str
    parent_chunk_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


def estimate_tokens(text: str) -> int:
    """Rough token estimation (approx 4 chars per token for English/Latin, 2-3 for Devanagari)."""
    return max(1, len(text.split()))


class BaseChunkingStrategy(ABC):
    """Abstract base class for collection-specific chunking strategies."""

    @abstractmethod
    def chunk(self, document: ParsedDocument) -> List[Chunk]:
        """Chunk a parsed document into typed Chunks with collection-specific metadata."""
        pass


class LegalStatutoryChunker(BaseChunkingStrategy):
    """Chunking strategy for `legal_statutory` collection.

    Hierarchy: Act -> Chapter -> Section -> Subsection -> Clause.
    Target chunk size: 200–800 tokens. Never splits mid-clause.
    Metadata: {document_id, corpus_collection, act, chapter, section, subsection, jurisdiction, document_version, text}
    """

    SUBSECTION_REGEX = re.compile(
        r"^\(([0-9a-zA-Z]+)\)\s*(.*?)(?=\n\([0-9a-zA-Z]+\)|\Z)", re.DOTALL | re.MULTILINE
    )
    CLAUSE_LETTER_REGEX = re.compile(
        r"^\(([a-z]+)\)\s*(.*?)(?=\n\([a-z]+\)|\Z)", re.DOTALL | re.MULTILINE
    )

    def chunk(self, document: ParsedDocument) -> List[Chunk]:
        chunks: List[Chunk] = []
        act_name = document.metadata.get("title", document.title)
        current_chapter: Optional[str] = document.metadata.get("chapter")

        for sec_idx, sec in enumerate(document.sections):
            heading_upper = sec.heading.upper()
            if "CHAPTER" in heading_upper or "PART" in heading_upper:
                current_chapter = sec.heading
                continue

            sec_num = sec.section_number or self._extract_sec_number(sec.heading)
            sec_text = sec.text.strip()
            if not sec_text:
                continue

            # Check if section text contains distinct clauses/subsections (e.g. (a), (d), (p) in Section 3)
            clauses = self._extract_subsections_or_clauses(sec_text)

            if clauses and len(sec_text) > 400:
                # Create parent section chunk or standalone clause chunks
                for sub_id, sub_text in clauses:
                    sub_clean = sub_text.strip()
                    if not sub_clean:
                        continue
                    full_chunk_text = f"{act_name}\n{sec.heading}\n({sub_id}) {sub_clean}".strip()
                    chunk_id = f"{document.document_id}#sec_{sec_num or sec_idx}_{sub_id}"
                    
                    chunks.append(
                        Chunk(
                            chunk_id=chunk_id,
                            document_id=document.document_id,
                            corpus_collection="legal_statutory",
                            text=full_chunk_text,
                            token_count=estimate_tokens(full_chunk_text),
                            jurisdiction=document.jurisdiction,
                            metadata={
                                "document_id": document.document_id,
                                "corpus_collection": "legal_statutory",
                                "act": act_name,
                                "chapter": current_chapter or "General",
                                "section": str(sec_num) if sec_num else None,
                                "subsection": str(sub_id),
                                "jurisdiction": document.jurisdiction,
                                "document_version": document.metadata.get("version", "1.0"),
                                "authority": document.metadata.get("authority", "Govt of India"),
                            },
                        )
                    )
            else:
                # Single chunk for the whole section
                full_chunk_text = f"{act_name}\n{sec.heading}\n{sec_text}".strip()
                chunk_id = f"{document.document_id}#sec_{sec_num or sec_idx}"
                chunks.append(
                    Chunk(
                        chunk_id=chunk_id,
                        document_id=document.document_id,
                        corpus_collection="legal_statutory",
                        text=full_chunk_text,
                        token_count=estimate_tokens(full_chunk_text),
                        jurisdiction=document.jurisdiction,
                        metadata={
                            "document_id": document.document_id,
                            "corpus_collection": "legal_statutory",
                            "act": act_name,
                            "chapter": current_chapter or "General",
                            "section": str(sec_num) if sec_num else None,
                            "subsection": None,
                            "jurisdiction": document.jurisdiction,
                            "document_version": document.metadata.get("version", "1.0"),
                            "authority": document.metadata.get("authority", "Govt of India"),
                        },
                    )
                )

        if not chunks and document.raw_text:
            chunks.append(
                Chunk(
                    chunk_id=f"{document.document_id}#0",
                    document_id=document.document_id,
                    corpus_collection="legal_statutory",
                    text=f"{act_name}\n{document.raw_text}",
                    token_count=estimate_tokens(document.raw_text),
                    jurisdiction=document.jurisdiction,
                    metadata={
                        "document_id": document.document_id,
                        "corpus_collection": "legal_statutory",
                        "act": act_name,
                        "chapter": "General",
                        "section": None,
                        "subsection": None,
                        "jurisdiction": document.jurisdiction,
                    },
                )
            )

        return chunks

    def _extract_sec_number(self, heading: str) -> Optional[str]:
        match = re.search(r"(?:Section|Rule|Sec\.?)\s*(\d+[A-Za-z]?)", heading, re.I)
        if match:
            return match.group(1)
        match_digits = re.match(r"^(\d+[A-Za-z]?)\.", heading)
        if match_digits:
            return match_digits.group(1)
        return None

    def _extract_subsections_or_clauses(self, text: str) -> List[tuple[str, str]]:
        """Extract individual clauses e.g. (a), (b), (p) or (1), (2)."""
        items: List[tuple[str, str]] = []
        matches = list(re.finditer(r"(?:\n|^)\s*\(([a-zA-Z0-9]+)\)\s*", text))
        if len(matches) < 2:
            return []

        for i, match in enumerate(matches):
            clause_id = match.group(1)
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            clause_content = text[start_pos:end_pos].strip()
            if clause_content:
                items.append((clause_id, clause_content))

        return items


class StandardsFormulationsChunker(BaseChunkingStrategy):
    """Chunking strategy for `standards_formulations` collection.

    One chunk per monograph/formulation entry. Supplementary notes become child chunks.
    Metadata: {document_id, corpus_collection, source, monograph_id, formulation_name, substance_type, jurisdiction, text}
    """

    def chunk(self, document: ParsedDocument) -> List[Chunk]:
        chunks: List[Chunk] = []
        source_name = document.metadata.get("title", document.title)

        for idx, sec in enumerate(document.sections):
            monograph_title = sec.heading
            monograph_text = sec.text.strip()
            if not monograph_text:
                continue

            # Extract botanical name or formulation type if present
            botanical = sec.metadata.get("botanical_name") or self._extract_botanical(monograph_title)
            substance_type = sec.metadata.get("substance_type", "SINGLE_HERB" if botanical else "CLASSICAL_FORMULATION")
            monograph_id = sec.metadata.get("monograph_id", f"mono_{idx+1}")

            parent_chunk_id = f"{document.document_id}#{monograph_id}"
            parent_text = f"Monograph: {monograph_title}\nSource: {source_name}\n\n{monograph_text}"

            chunks.append(
                Chunk(
                    chunk_id=parent_chunk_id,
                    document_id=document.document_id,
                    corpus_collection="standards_formulations",
                    text=parent_text,
                    token_count=estimate_tokens(parent_text),
                    jurisdiction=document.jurisdiction,
                    metadata={
                        "document_id": document.document_id,
                        "corpus_collection": "standards_formulations",
                        "source": source_name,
                        "monograph_id": monograph_id,
                        "formulation_name": monograph_title,
                        "botanical_name": botanical,
                        "substance_type": substance_type,
                        "jurisdiction": document.jurisdiction,
                    },
                )
            )

            # Check for supplementary testing standards or heavy metal limit notes
            supp_notes = sec.metadata.get("supplementary_notes")
            if supp_notes:
                child_id = f"{parent_chunk_id}#assay_standards"
                child_text = f"Standards & Limits for {monograph_title}:\n{supp_notes}"
                chunks.append(
                    Chunk(
                        chunk_id=child_id,
                        document_id=document.document_id,
                        corpus_collection="standards_formulations",
                        text=child_text,
                        token_count=estimate_tokens(child_text),
                        jurisdiction=document.jurisdiction,
                        parent_chunk_id=parent_chunk_id,
                        metadata={
                            "document_id": document.document_id,
                            "corpus_collection": "standards_formulations",
                            "source": source_name,
                            "monograph_id": monograph_id,
                            "formulation_name": monograph_title,
                            "substance_type": "ANALYTICAL_STANDARD",
                            "jurisdiction": document.jurisdiction,
                            "parent_chunk_id": parent_chunk_id,
                        },
                    )
                )

        if not chunks and document.raw_text:
            chunks.append(
                Chunk(
                    chunk_id=f"{document.document_id}#0",
                    document_id=document.document_id,
                    corpus_collection="standards_formulations",
                    text=document.raw_text,
                    token_count=estimate_tokens(document.raw_text),
                    jurisdiction=document.jurisdiction,
                    metadata={
                        "document_id": document.document_id,
                        "corpus_collection": "standards_formulations",
                        "source": source_name,
                        "formulation_name": document.title,
                        "substance_type": "HERBAL_STANDARD",
                        "jurisdiction": document.jurisdiction,
                    },
                )
            )

        return chunks

    def _extract_botanical(self, title: str) -> Optional[str]:
        match = re.search(r"\(([^)]+)\)", title)
        if match:
            return match.group(1).strip()
        return None


class CaseLawChunker(BaseChunkingStrategy):
    """Chunking strategy for `case_law_prior_art` collection.

    Paragraph-level chunks with full case metadata pinned to every chunk.
    Metadata: {document_id, corpus_collection, case_name, court, year, citation_ref, paragraph_index, jurisdiction, text}
    """

    def chunk(self, document: ParsedDocument) -> List[Chunk]:
        chunks: List[Chunk] = []
        case_name = document.metadata.get("case_name", document.title)
        court = document.metadata.get("court", "Patent Office / Tribunal")
        year = document.metadata.get("year", "Unknown")
        citation_ref = document.metadata.get("citation_ref", document.document_id)

        paragraphs = [p.strip() for p in document.raw_text.split("\n\n") if len(p.strip()) > 30]

        for p_idx, p_text in enumerate(paragraphs):
            chunk_id = f"{document.document_id}#p_{p_idx + 1}"
            full_text = f"Case: {case_name} ({court}, {year})\nCitation: {citation_ref}\n\n[Paragraph {p_idx + 1}]\n{p_text}"

            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    corpus_collection="case_law_prior_art",
                    text=full_text,
                    token_count=estimate_tokens(full_text),
                    jurisdiction=document.jurisdiction,
                    metadata={
                        "document_id": document.document_id,
                        "corpus_collection": "case_law_prior_art",
                        "case_name": case_name,
                        "court": court,
                        "year": year,
                        "citation_ref": citation_ref,
                        "paragraph_index": p_idx + 1,
                        "jurisdiction": document.jurisdiction,
                    },
                )
            )

        return chunks


class ProceduralFormsChunker(BaseChunkingStrategy):
    """Chunking strategy for `procedural_forms` collection.

    Form section / field-group level (150–400 tokens).
    Metadata: {document_id, corpus_collection, form_name, section_heading, authority, jurisdiction, text}
    """

    def chunk(self, document: ParsedDocument) -> List[Chunk]:
        chunks: List[Chunk] = []
        form_name = document.metadata.get("title", document.title)
        authority = document.metadata.get("authority", "National Biodiversity Authority / SLA")

        for sec_idx, sec in enumerate(document.sections):
            sec_text = sec.text.strip()
            if not sec_text:
                continue

            chunk_id = f"{document.document_id}#form_sec_{sec_idx + 1}"
            full_text = f"{form_name}\nAuthority: {authority}\nSection: {sec.heading}\n\n{sec_text}"

            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    corpus_collection="procedural_forms",
                    text=full_text,
                    token_count=estimate_tokens(full_text),
                    jurisdiction=document.jurisdiction,
                    metadata={
                        "document_id": document.document_id,
                        "corpus_collection": "procedural_forms",
                        "form_name": form_name,
                        "section_heading": sec.heading,
                        "authority": authority,
                        "governing_law": document.metadata.get("governing_law", "Biological Diversity Act / Drugs Act"),
                        "jurisdiction": document.jurisdiction,
                    },
                )
            )

        if not chunks and document.raw_text:
            chunks.append(
                Chunk(
                    chunk_id=f"{document.document_id}#0",
                    document_id=document.document_id,
                    corpus_collection="procedural_forms",
                    text=f"{form_name}\n\n{document.raw_text}",
                    token_count=estimate_tokens(document.raw_text),
                    jurisdiction=document.jurisdiction,
                    metadata={
                        "document_id": document.document_id,
                        "corpus_collection": "procedural_forms",
                        "form_name": form_name,
                        "section_heading": "Form Content",
                        "authority": authority,
                        "jurisdiction": document.jurisdiction,
                    },
                )
            )

        return chunks


class InternationalExportChunker(BaseChunkingStrategy):
    """Chunking strategy for `international_export` collection.

    Article-level chunks (300–800 tokens).
    Metadata: {document_id, corpus_collection, treaty_name, article_number, paragraph, jurisdiction: "INTERNATIONAL", text}
    """

    def chunk(self, document: ParsedDocument) -> List[Chunk]:
        chunks: List[Chunk] = []
        treaty_name = document.metadata.get("title", document.title)

        for sec_idx, sec in enumerate(document.sections):
            sec_text = sec.text.strip()
            if not sec_text:
                continue

            art_num = sec.section_number or self._extract_article_number(sec.heading)
            chunk_id = f"{document.document_id}#art_{art_num or sec_idx + 1}"
            full_text = f"Treaty/Regulation: {treaty_name}\n{sec.heading}\n\n{sec_text}"

            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    corpus_collection="international_export",
                    text=full_text,
                    token_count=estimate_tokens(full_text),
                    jurisdiction=document.jurisdiction or "INTERNATIONAL",
                    metadata={
                        "document_id": document.document_id,
                        "corpus_collection": "international_export",
                        "treaty_name": treaty_name,
                        "article_number": str(art_num) if art_num else None,
                        "paragraph": None,
                        "jurisdiction": document.jurisdiction or "INTERNATIONAL",
                        "authority": document.metadata.get("authority", "WIPO / WTO / CBD"),
                    },
                )
            )

        if not chunks and document.raw_text:
            chunks.append(
                Chunk(
                    chunk_id=f"{document.document_id}#0",
                    document_id=document.document_id,
                    corpus_collection="international_export",
                    text=f"{treaty_name}\n\n{document.raw_text}",
                    token_count=estimate_tokens(document.raw_text),
                    jurisdiction=document.jurisdiction or "INTERNATIONAL",
                    metadata={
                        "document_id": document.document_id,
                        "corpus_collection": "international_export",
                        "treaty_name": treaty_name,
                        "article_number": None,
                        "paragraph": None,
                        "jurisdiction": "INTERNATIONAL",
                    },
                )
            )

        return chunks

    def _extract_article_number(self, heading: str) -> Optional[str]:
        match = re.search(r"Article\s*(\d+[A-Za-z]?(?:\.\d+)?)", heading, re.I)
        if match:
            return match.group(1)
        return None


# Strategy Registry for Dispatcher
STRATEGY_REGISTRY: Dict[str, Type[BaseChunkingStrategy]] = {
    "legal_statutory": LegalStatutoryChunker,
    "standards_formulations": StandardsFormulationsChunker,
    "case_law_prior_art": CaseLawChunker,
    "procedural_forms": ProceduralFormsChunker,
    "international_export": InternationalExportChunker,
}


def chunk_document(document: ParsedDocument) -> List[Chunk]:
    """Dispatcher function: routes parsed document to the collection-specific chunking strategy."""
    collection = document.corpus_collection
    strategy_cls = STRATEGY_REGISTRY.get(collection, LegalStatutoryChunker)
    strategy = strategy_cls()
    return strategy.chunk(document)
