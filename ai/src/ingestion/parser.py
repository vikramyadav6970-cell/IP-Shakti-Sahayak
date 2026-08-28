"""Document parsing pipeline for legal and regulatory documents.

Extracts clean text and structural markers (chapters, sections, subsections, articles,
monographs, form fields) from PDF, HTML, JSONL, and plain text sources.
Preserves corpus_collection and manifest metadata across all parsed documents.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import io
import json
import logging
import os
import re

logger = logging.getLogger(__name__)


@dataclass
class ParsedSection:
    """Represents a structural section within a parsed legal/regulatory document."""

    heading: str
    section_number: Optional[str] = None
    level: int = 1  # 1 = Chapter/Part/Form, 2 = Section/Article/Rule/Monograph, 3 = Clause/Subsection
    text: str = ""
    page_number: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedDocument:
    """Normalized intermediate representation of an ingested document."""

    document_id: str
    title: str
    corpus_collection: str  # one of the 5 Qdrant collections
    jurisdiction: str
    document_type: str
    raw_text: str
    sections: List[ParsedSection] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DocumentParser:
    """Parser supporting PDF, HTML, and text-based legal & regulatory sources."""

    # Regex patterns for identifying legal structure markers
    CHAPTER_PATTERN = re.compile(
        r"^(?:CHAPTER|PART)\s+([IVXLCDM\d]+|[A-Z]+)[\s:.\-—]*(.*)$", re.IGNORECASE | re.MULTILINE
    )
    SECTION_PATTERN = re.compile(
        r"^(?:Section\s+)?(\d+[A-Za-z]?(?:\([a-zA-Z0-9]+\))*)\.\s+(.*)$", re.IGNORECASE | re.MULTILINE
    )
    ARTICLE_PATTERN = re.compile(
        r"^Article\s+(\d+[A-Za-z]?(?:\.\d+)*)[\s:.\-—]*(.*)$", re.IGNORECASE | re.MULTILINE
    )
    RULE_PATTERN = re.compile(
        r"^Rule\s+(\d+[A-Za-z]?(?:\.\d+)*)[\s:.\-—]*(.*)$", re.IGNORECASE | re.MULTILINE
    )
    FORM_PATTERN = re.compile(
        r"^FORM\s+([IVXLCDM\d]+|[A-Za-z0-9\-]+)[\s:.\-—]*(.*)$", re.IGNORECASE | re.MULTILINE
    )

    def __init__(self, use_ocr_fallback: bool = True):
        self.use_ocr_fallback = use_ocr_fallback

    def parse_text(
        self,
        text: str,
        manifest_meta: Dict[str, Any],
    ) -> ParsedDocument:
        """Parse raw text content, extracting sections and structural markers.

        Args:
            text: Plain text / Markdown content.
            manifest_meta: Metadata dictionary from the manifest.

        Returns:
            ParsedDocument instance.
        """
        clean_text = self._clean_text(text)
        sections = self._extract_sections_from_text(clean_text, manifest_meta.get("corpus_collection", ""))

        return ParsedDocument(
            document_id=manifest_meta.get("document_id", "doc_unknown"),
            title=manifest_meta.get("title", "Untitled Document"),
            corpus_collection=manifest_meta.get("corpus_collection", "legal_statutory"),
            jurisdiction=manifest_meta.get("jurisdiction", "INDIA"),
            document_type=manifest_meta.get("document_type", "STATUTE"),
            raw_text=clean_text,
            sections=sections,
            metadata=dict(manifest_meta),
        )

    def parse_html(
        self,
        html_content: Union[str, bytes],
        manifest_meta: Dict[str, Any],
    ) -> ParsedDocument:
        """Parse HTML source content into clean structured text and sections."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_content, "html.parser")

        # Remove scripts, styles, navigations, footers
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()

        # Extract structured text with headings preserved
        lines: List[str] = []
        sections: List[ParsedSection] = []

        current_heading = manifest_meta.get("title", "")
        current_sec_num: Optional[str] = None
        current_text_buf: List[str] = []

        for elem in soup.find_all(["h1", "h2", "h3", "h4", "p", "div", "li", "article", "section"]):
            text = elem.get_text(strip=True)
            if not text:
                continue

            if elem.name in ["h1", "h2", "h3", "h4"]:
                # Save previous section
                if current_text_buf:
                    sec_text = "\n".join(current_text_buf).strip()
                    if sec_text:
                        sections.append(
                            ParsedSection(
                                heading=current_heading,
                                section_number=current_sec_num,
                                text=sec_text,
                                level=2 if elem.name in ["h1", "h2"] else 3,
                            )
                        )
                    current_text_buf = []

                current_heading = text
                sec_match = re.search(r"(?:Section|Article|Rule)\s+(\d+[A-Za-z]?(?:\([a-zA-Z0-9]+\))*)", text, re.I)
                current_sec_num = sec_match.group(1) if sec_match else None
                lines.append(f"\n## {text}\n")
            else:
                lines.append(text)
                current_text_buf.append(text)

        # Flush trailing section
        if current_text_buf:
            sec_text = "\n".join(current_text_buf).strip()
            if sec_text:
                sections.append(
                    ParsedSection(
                        heading=current_heading,
                        section_number=current_sec_num,
                        text=sec_text,
                        level=2,
                    )
                )

        full_raw_text = "\n".join(lines).strip()
        clean_text = self._clean_text(full_raw_text)

        return ParsedDocument(
            document_id=manifest_meta.get("document_id", "doc_unknown"),
            title=manifest_meta.get("title", "Untitled Document"),
            corpus_collection=manifest_meta.get("corpus_collection", "legal_statutory"),
            jurisdiction=manifest_meta.get("jurisdiction", "INDIA"),
            document_type=manifest_meta.get("document_type", "STATUTE"),
            raw_text=clean_text,
            sections=sections if sections else self._extract_sections_from_text(clean_text, manifest_meta.get("corpus_collection", "")),
            metadata=dict(manifest_meta),
        )

    def parse_pdf(
        self,
        pdf_source: Union[str, Path, bytes, io.BytesIO],
        manifest_meta: Dict[str, Any],
    ) -> ParsedDocument:
        """Parse PDF document extracting text layer with PyMuPDF (fitz) or pypdf fallback."""
        text_pages: List[str] = []
        sections: List[ParsedSection] = []

        try:
            import fitz  # PyMuPDF

            if isinstance(pdf_source, (str, Path)):
                doc = fitz.open(str(pdf_source))
            elif isinstance(pdf_source, bytes):
                doc = fitz.open(stream=pdf_source, filetype="pdf")
            else:
                doc = fitz.open(stream=pdf_source.read(), filetype="pdf")

            for page_idx, page in enumerate(doc):
                page_text = page.get_text("text")
                if page_text and page_text.strip():
                    text_pages.append(page_text)
                elif self.use_ocr_fallback:
                    # Attempt OCR on scanned page image
                    ocr_text = self._ocr_page(page)
                    if ocr_text:
                        text_pages.append(ocr_text)

            doc.close()
        except ImportError:
            # Fallback to pypdf
            from pypdf import PdfReader

            reader = PdfReader(pdf_source if isinstance(pdf_source, (str, Path)) else io.BytesIO(pdf_source if isinstance(pdf_source, bytes) else pdf_source.read()))
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text_pages.append(extracted)

        full_raw_text = "\n\n".join(text_pages)
        clean_text = self._clean_text(full_raw_text)
        sections = self._extract_sections_from_text(clean_text, manifest_meta.get("corpus_collection", ""))

        return ParsedDocument(
            document_id=manifest_meta.get("document_id", "doc_unknown"),
            title=manifest_meta.get("title", "Untitled Document"),
            corpus_collection=manifest_meta.get("corpus_collection", "legal_statutory"),
            jurisdiction=manifest_meta.get("jurisdiction", "INDIA"),
            document_type=manifest_meta.get("document_type", "STATUTE"),
            raw_text=clean_text,
            sections=sections,
            metadata=dict(manifest_meta),
        )

    def parse_file(
        self,
        file_path: Union[str, Path],
        manifest_meta: Dict[str, Any],
    ) -> ParsedDocument:
        """Auto-detect format and parse file from filesystem."""
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix in [".pdf"]:
            return self.parse_pdf(path, manifest_meta)
        elif suffix in [".html", ".htm", ".xhtml"]:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return self.parse_html(f.read(), manifest_meta)
        elif suffix in [".json", ".jsonl"]:
            return self._parse_json_or_jsonl(path, manifest_meta)
        else:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return self.parse_text(f.read(), manifest_meta)

    def _parse_json_or_jsonl(
        self,
        path: Path,
        manifest_meta: Dict[str, Any],
    ) -> ParsedDocument:
        """Parse JSON or JSONL structured records."""
        sections: List[ParsedSection] = []
        raw_lines: List[str] = []

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read().strip()

        if path.suffix.lower() == ".jsonl":
            for line in content.splitlines():
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    heading = record.get("title") or record.get("section") or record.get("subject") or "Record"
                    text = record.get("text") or record.get("content") or record.get("raw_text") or json.dumps(record)
                    sec_num = record.get("section_number") or record.get("article_number")
                    sections.append(
                        ParsedSection(
                            heading=heading,
                            section_number=str(sec_num) if sec_num else None,
                            text=text,
                            metadata=record,
                        )
                    )
                    raw_lines.append(f"{heading}\n{text}\n")
                except json.JSONDecodeError:
                    continue
        else:
            data = json.loads(content)
            if isinstance(data, list):
                for item in data:
                    heading = item.get("title", "Section")
                    text = item.get("text", json.dumps(item))
                    sections.append(ParsedSection(heading=heading, text=text, metadata=item))
                    raw_lines.append(f"{heading}\n{text}\n")
            elif isinstance(data, dict):
                heading = data.get("title", manifest_meta.get("title", "Document"))
                text = data.get("text", json.dumps(data))
                sections.append(ParsedSection(heading=heading, text=text, metadata=data))
                raw_lines.append(text)

        raw_text = "\n".join(raw_lines).strip()
        return ParsedDocument(
            document_id=manifest_meta.get("document_id", path.stem),
            title=manifest_meta.get("title", path.stem),
            corpus_collection=manifest_meta.get("corpus_collection", "legal_statutory"),
            jurisdiction=manifest_meta.get("jurisdiction", "INDIA"),
            document_type=manifest_meta.get("document_type", "STATUTE"),
            raw_text=raw_text,
            sections=sections,
            metadata=dict(manifest_meta),
        )

    def _extract_sections_from_text(self, text: str, collection: str) -> List[ParsedSection]:
        """Extract structured sections based on legal markers in plain text."""
        sections: List[ParsedSection] = []
        lines = text.splitlines()

        current_heading = "Preamble / Preliminary"
        current_sec_num: Optional[str] = None
        current_level = 1
        current_buf: List[str] = []

        # Split on common statutory section patterns
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            sec_match = (
                self.SECTION_PATTERN.match(stripped)
                or self.ARTICLE_PATTERN.match(stripped)
                or self.RULE_PATTERN.match(stripped)
                or self.FORM_PATTERN.match(stripped)
                or self.CHAPTER_PATTERN.match(stripped)
            )

            if sec_match:
                # Flush previous section buffer
                if current_buf:
                    buf_text = "\n".join(current_buf).strip()
                    if buf_text:
                        sections.append(
                            ParsedSection(
                                heading=current_heading,
                                section_number=current_sec_num,
                                level=current_level,
                                text=buf_text,
                            )
                        )
                    current_buf = []

                current_sec_num = sec_match.group(1) if len(sec_match.groups()) >= 1 else None
                current_heading = stripped
                current_level = 1 if "CHAPTER" in stripped.upper() or "PART" in stripped.upper() else 2
                current_buf.append(stripped)
            else:
                current_buf.append(line)

        # Flush last section
        if current_buf:
            buf_text = "\n".join(current_buf).strip()
            if buf_text:
                sections.append(
                    ParsedSection(
                        heading=current_heading,
                        section_number=current_sec_num,
                        level=current_level,
                        text=buf_text,
                    )
                )

        # If no explicit sections found, return entire document as one section
        if not sections and text.strip():
            sections.append(
                ParsedSection(
                    heading="General",
                    text=text.strip(),
                    level=1,
                )
            )

        return sections

    def _ocr_page(self, page: Any) -> str:
        """Optional OCR fallback using pytesseract on page pixmap."""
        try:
            import pytesseract
            from PIL import Image

            pix = page.get_pixmap(dpi=150)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            return pytesseract.image_to_string(img)
        except Exception as e:
            logger.warning("OCR fallback failed or pytesseract not available: %s", e)
            return ""

    @staticmethod
    def _clean_text(text: str) -> str:
        """Normalize line breaks, remove null bytes, clean repetitive whitespace."""
        text = text.replace("\x00", "")
        text = re.sub(r"\r\n|\r", "\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


# Module-level instance
default_parser = DocumentParser()


def parse_document(
    source: Union[str, Path, bytes, io.BytesIO],
    manifest_meta: Dict[str, Any],
) -> ParsedDocument:
    """Convenience function to parse any supported document source."""
    if isinstance(source, (str, Path)) and os.path.exists(str(source)):
        return default_parser.parse_file(source, manifest_meta)
    elif isinstance(source, (bytes, io.BytesIO)):
        return default_parser.parse_pdf(source, manifest_meta)
    elif isinstance(source, str) and ("<html" in source.lower() or "<!doctype" in source.lower()):
        return default_parser.parse_html(source, manifest_meta)
    else:
        return default_parser.parse_text(str(source), manifest_meta)
