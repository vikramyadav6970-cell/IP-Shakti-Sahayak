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


def split_oversized_chunk(chunk: Chunk, target_size: int = 500, overlap: int = 50) -> List[Chunk]:
    """Split chunk into smaller segments with target_size tokens and overlap."""
    text = chunk.text
    doc_id = chunk.document_id
    base_meta = dict(chunk.metadata)

    def segment_text(raw: str) -> List[str]:
        blocks = [b.strip() for b in re.split(r"\n\n+", raw) if b.strip()]
        segments: List[str] = []
        for blk in blocks:
            if estimate_tokens(blk) <= target_size + overlap:
                segments.append(blk)
            else:
                sub_lines = [l.strip() for l in blk.split("\n") if l.strip()]
                for sl in sub_lines:
                    if estimate_tokens(sl) <= target_size + overlap:
                        segments.append(sl)
                    else:
                        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", sl) if s.strip()]
                        for s in sents:
                            if estimate_tokens(s) <= target_size + overlap:
                                segments.append(s)
                            else:
                                words = s.split()
                                step = max(50, target_size - overlap)
                                for w_i in range(0, len(words), step):
                                    w_chunk = " ".join(words[w_i : w_i + target_size])
                                    if w_chunk:
                                        segments.append(w_chunk)
        return segments

    segments = segment_text(text)
    if not segments:
        return [chunk]

    parts: List[str] = []
    current_buf: List[str] = []
    current_tokens = 0

    for seg in segments:
        seg_tokens = estimate_tokens(seg)
        if current_tokens + seg_tokens > (target_size + overlap) and current_buf:
            parts.append("\n\n".join(current_buf))
            overlap_seg = current_buf[-1] if estimate_tokens(current_buf[-1]) <= overlap else ""
            current_buf = [overlap_seg, seg] if overlap_seg else [seg]
            current_tokens = estimate_tokens("\n\n".join(current_buf))
        else:
            current_buf.append(seg)
            current_tokens += seg_tokens

    if current_buf:
        parts.append("\n\n".join(current_buf))

    if len(parts) <= 1:
        return [chunk]

    result_chunks: List[Chunk] = []
    for part_idx, part_text in enumerate(parts):
        part_clean = part_text.strip()
        if not part_clean:
            continue
        part_chunk_id = f"{chunk.chunk_id}#part_{part_idx + 1}"
        meta = dict(base_meta)
        meta["part_index"] = part_idx + 1
        meta["parent_chunk_id"] = chunk.chunk_id
        result_chunks.append(
            Chunk(
                chunk_id=part_chunk_id,
                document_id=doc_id,
                corpus_collection=chunk.corpus_collection,
                text=part_clean,
                token_count=estimate_tokens(part_clean),
                jurisdiction=chunk.jurisdiction,
                parent_chunk_id=chunk.chunk_id,
                metadata=meta,
            )
        )
    return result_chunks


def normalize_chunks(raw_chunks: List[Chunk], min_tokens: int = 200, max_tokens: int = 800) -> List[Chunk]:
    """Normalize chunks into the 200–800 token band: merge small siblings, split oversized chunks."""
    normalized: List[Chunk] = []

    # Discard pure non-substantive residual fragments (< 15 tokens)
    valid_chunks = [
        c for c in raw_chunks
        if c.text and len(c.text.strip()) > 25 and c.token_count >= 15
    ]
    if not valid_chunks:
        return raw_chunks

    idx = 0
    while idx < len(valid_chunks):
        c = valid_chunks[idx]

        # Case 1: Chunk is oversized (> max_tokens) -> Split into 400–600 token parts
        if c.token_count > max_tokens:
            splits = split_oversized_chunk(c, target_size=500, overlap=50)
            normalized.extend(splits)
            idx += 1
            continue

        # Case 2: Chunk is comfortably in band (min_tokens <= token_count <= max_tokens)
        if c.token_count >= min_tokens:
            normalized.append(c)
            idx += 1
            continue

        # Case 3: Chunk is smaller than min_tokens -> Merge with sibling chunks from same doc/section/chapter
        merged_text = c.text
        merged_tokens = c.token_count
        subsections = [str(c.metadata.get("subsection"))] if c.metadata.get("subsection") else []
        sec_num = c.metadata.get("section") or c.metadata.get("article_number") or c.metadata.get("monograph_id")
        doc_id = c.document_id

        next_idx = idx + 1
        while next_idx < len(valid_chunks):
            next_c = valid_chunks[next_idx]
            next_sec = next_c.metadata.get("section") or next_c.metadata.get("article_number") or next_c.metadata.get("monograph_id")

            same_doc = next_c.document_id == doc_id
            same_sec = next_sec == sec_num

            # Merge if same section or both are short statutory siblings within max_tokens
            can_merge = same_doc and (same_sec or (merged_tokens + next_c.token_count <= max_tokens))

            if can_merge and (merged_tokens + next_c.token_count <= max_tokens):
                add_text = next_c.text
                header_prefix = f"{c.metadata.get('act', '')}\n"
                if header_prefix and add_text.startswith(header_prefix):
                    add_text = add_text[len(header_prefix):].strip()

                merged_text += f"\n\n{add_text}"
                merged_tokens = estimate_tokens(merged_text)
                if next_c.metadata.get("subsection"):
                    subsections.append(str(next_c.metadata.get("subsection")))
                next_idx += 1
                if merged_tokens >= min_tokens:
                    break
            else:
                break

        sub_str = "-".join(filter(None, subsections)) if subsections else None
        merged_meta = dict(c.metadata)
        if sub_str:
            merged_meta["subsection"] = sub_str

        chunk_id = f"{doc_id}#sec_{sec_num or idx}_{sub_str}" if sub_str else f"{doc_id}#sec_{sec_num or idx}"

        normalized.append(
            Chunk(
                chunk_id=chunk_id,
                document_id=doc_id,
                corpus_collection=c.corpus_collection,
                text=merged_text.strip(),
                token_count=merged_tokens,
                jurisdiction=c.jurisdiction,
                metadata=merged_meta,
            )
        )
        idx = next_idx

    return normalized


def chunk_document(document: ParsedDocument) -> List[Chunk]:
    """Dispatcher function: routes parsed document to collection-specific chunking strategy and normalizes."""
    collection = document.corpus_collection
    strategy_cls = STRATEGY_REGISTRY.get(collection, LegalStatutoryChunker)
    strategy = strategy_cls()
    raw_chunks = strategy.chunk(document)
    return normalize_chunks(raw_chunks, min_tokens=200, max_tokens=800)

