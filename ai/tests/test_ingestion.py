"""Unit tests for the ingestion parsing and collection-aware chunking pipeline."""

from pathlib import Path
import pytest

from src.ingestion.parser import (
    DocumentParser,
    ParsedDocument,
    ParsedSection,
    parse_document,
)
from src.ingestion.chunker import (
    Chunk,
    LegalStatutoryChunker,
    StandardsFormulationsChunker,
    CaseLawChunker,
    ProceduralFormsChunker,
    InternationalExportChunker,
    chunk_document,
)


def test_parse_plain_text_statute():
    """Parser should extract structural sections and preserve metadata for statutory text."""
    statute_text = """
CHAPTER II
INVENTIONS NOT PATENTABLE

Section 3. What are not inventions.
The following are not inventions within the meaning of this Act:
(d) the mere discovery of a new form of a known substance which does not result in the enhancement of the known efficacy;
(e) a substance obtained by a mere admixture resulting only in the aggregation of the properties;
(p) an invention which in effect is traditional knowledge or which is an aggregation or duplication of known properties of traditionally known component or components.

Section 10. Contents of specifications.
(4) Every complete specification shall:
(d)(ii) disclose the source and geographical origin of the biological material in the specification.
"""
    manifest_meta = {
        "document_id": "doc_in_patents_act_1970",
        "title": "The Patents Act, 1970",
        "corpus_collection": "legal_statutory",
        "jurisdiction": "INDIA",
        "document_type": "STATUTE",
        "authority": "Ministry of Law and Justice",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/1392",
    }

    doc = parse_document(statute_text, manifest_meta)

    assert isinstance(doc, ParsedDocument)
    assert doc.document_id == "doc_in_patents_act_1970"
    assert doc.corpus_collection == "legal_statutory"
    assert doc.jurisdiction == "INDIA"
    assert doc.document_type == "STATUTE"
    assert len(doc.sections) >= 2


def test_legal_statutory_chunker_section_3p():
    """LegalStatutoryChunker must extract section 3 subsection (p) with exact metadata."""
    statute_text = """
Section 3. What are not inventions.
The following are not inventions within the meaning of this Act:
(d) the mere discovery of a new form of a known substance which does not result in the enhancement of the known efficacy;
(p) an invention which in effect is traditional knowledge or which is an aggregation or duplication of known properties of traditionally known component or components.
"""
    manifest_meta = {
        "document_id": "doc_in_patents_act_1970",
        "title": "The Patents Act, 1970",
        "corpus_collection": "legal_statutory",
        "jurisdiction": "INDIA",
        "document_type": "STATUTE",
    }
    doc = parse_document(statute_text, manifest_meta)
    chunker = LegalStatutoryChunker()
    chunks = chunker.chunk(doc)

    assert len(chunks) >= 1
    # Check Section 3(p) chunk
    p_chunk = next((c for c in chunks if c.metadata.get("subsection") == "p" or "traditional knowledge" in c.text), None)
    assert p_chunk is not None
    assert p_chunk.corpus_collection == "legal_statutory"
    assert p_chunk.jurisdiction == "INDIA"
    assert p_chunk.metadata.get("act") == "The Patents Act, 1970"
    assert "traditional knowledge" in p_chunk.text


def test_standards_formulations_chunker():
    """StandardsFormulationsChunker must produce monograph chunk and linked child standard notes."""
    doc = ParsedDocument(
        document_id="doc_std_api_ashwagandha",
        title="Ayurvedic Pharmacopoeia of India",
        corpus_collection="standards_formulations",
        jurisdiction="INDIA",
        document_type="MONOGRAPH",
        raw_text="",
        sections=[
            ParsedSection(
                heading="Ashwagandha (Withania somnifera Dunal. - Root)",
                text="Ashwagandha consists of dried mature roots of Withania somnifera Dunal. (Fam. Solanaceae). Rasa: Tikta, Kashaya; Virya: Ushna; Vipaka: Madhura. Karma: Balya, Rasayana, Vatahara.",
                metadata={
                    "botanical_name": "Withania somnifera Dunal.",
                    "monograph_id": "api_ashwagandha_001",
                    "supplementary_notes": "Heavy metal limits: Lead max 10 ppm, Cadmium max 0.3 ppm. Assay: Withanolides not less than 0.5% w/w by HPLC.",
                },
            )
        ],
    )
    chunker = StandardsFormulationsChunker()
    chunks = chunker.chunk(doc)

    assert len(chunks) == 2  # 1 parent monograph + 1 child assay limits note
    parent = chunks[0]
    child = chunks[1]

    assert parent.corpus_collection == "standards_formulations"
    assert parent.metadata["monograph_id"] == "api_ashwagandha_001"
    assert parent.metadata["botanical_name"] == "Withania somnifera Dunal."
    assert child.parent_chunk_id == parent.chunk_id
    assert child.metadata["substance_type"] == "ANALYTICAL_STANDARD"
    assert "Withanolides" in child.text


def test_case_law_chunker():
    """CaseLawChunker must chunk at paragraph level and replicate case metadata on every chunk."""
    doc = ParsedDocument(
        document_id="doc_case_turmeric_revocation",
        title="Turmeric Patent Re-examination",
        corpus_collection="case_law_prior_art",
        jurisdiction="USA",
        document_type="CASE_LAW",
        raw_text="The USPTO granted US Patent 5,401,504 claiming use of turmeric in wound healing.\n\nCSIR filed a formal request for re-examination presenting ancient Sanskrit texts and classical Ayurvedic treatises proving prior art across India.\n\nAll claims were revoked on grounds of lack of novelty anticipated by traditional knowledge.",
        metadata={
            "case_name": "In re US Patent 5,401,504 (Turmeric Wound Healing)",
            "court": "USPTO Re-examination Board",
            "year": "1997",
            "citation_ref": "US Patent 5,401,504 Revocation",
        },
    )
    chunker = CaseLawChunker()
    chunks = chunker.chunk(doc)

    assert len(chunks) == 3
    for chunk in chunks:
        assert chunk.corpus_collection == "case_law_prior_art"
        assert chunk.metadata["case_name"] == "In re US Patent 5,401,504 (Turmeric Wound Healing)"
        assert chunk.metadata["court"] == "USPTO Re-examination Board"
        assert chunk.metadata["year"] == "1997"
        assert "Paragraph" in chunk.text


def test_procedural_forms_chunker():
    """ProceduralFormsChunker must chunk form sections with authority and field instructions."""
    doc = ParsedDocument(
        document_id="doc_form_nba_form3",
        title="NBA Form III — Application for IPR Approval",
        corpus_collection="procedural_forms",
        jurisdiction="INDIA",
        document_type="FORM",
        raw_text="",
        sections=[
            ParsedSection(
                heading="Section A: Applicant and Patent Application Profile",
                text="Details of patent application number, filing date, patent office (India/PCT/foreign), and title of the herbal invention.",
            ),
            ParsedSection(
                heading="Section B: Biological Resource and Traditional Knowledge Utilization",
                text="Name of botanical species (scientific and vernacular name), geographical location where collected, and traditional knowledge source.",
            ),
        ],
        metadata={
            "authority": "National Biodiversity Authority",
            "governing_law": "Section 6, Biological Diversity Act 2002",
        },
    )
    chunker = ProceduralFormsChunker()
    chunks = chunker.chunk(doc)

    assert len(chunks) == 2
    for chunk in chunks:
        assert chunk.corpus_collection == "procedural_forms"
        assert chunk.metadata["authority"] == "National Biodiversity Authority"
        assert "NBA Form III" in chunk.text


def test_international_export_chunker():
    """InternationalExportChunker must extract Article-level chunks with international jurisdiction."""
    doc = ParsedDocument(
        document_id="doc_int_trips_agreement",
        title="WTO TRIPS Agreement",
        corpus_collection="international_export",
        jurisdiction="INTERNATIONAL",
        document_type="TREATY",
        raw_text="",
        sections=[
            ParsedSection(
                heading="Article 27. Patentable Subject Matter",
                section_number="27",
                text="1. Patents shall be available for any inventions, whether products or processes, in all fields of technology, provided that they are new, involve an inventive step and are capable of industrial application.\n2. Members may exclude from patentability inventions the prevention within their territory of the commercial exploitation of which is necessary to protect ordre public or morality.",
            )
        ],
        metadata={"authority": "World Trade Organization"},
    )
    chunker = InternationalExportChunker()
    chunks = chunker.chunk(doc)

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.corpus_collection == "international_export"
    assert chunk.metadata["article_number"] == "27"
    assert chunk.jurisdiction == "INTERNATIONAL"
    assert "Article 27" in chunk.text


def test_chunker_dispatcher():
    """chunk_document dispatcher should route to correct strategy based on corpus_collection."""
    statute_doc = ParsedDocument(
        document_id="doc_statute",
        title="Patents Act",
        corpus_collection="legal_statutory",
        jurisdiction="INDIA",
        document_type="STATUTE",
        raw_text="Section 3(p) traditional knowledge.",
    )
    chunks = chunk_document(statute_doc)
    assert chunks[0].corpus_collection == "legal_statutory"

    export_doc = ParsedDocument(
        document_id="doc_treaty",
        title="Nagoya Protocol",
        corpus_collection="international_export",
        jurisdiction="INTERNATIONAL",
        document_type="TREATY",
        raw_text="Article 5 Fair and equitable benefit-sharing.",
    )
    chunks = chunk_document(export_doc)
    assert chunks[0].corpus_collection == "international_export"


def test_normalize_chunks_merging_and_splitting():
    """normalize_chunks should merge tiny siblings into 200-800 token band and split >800 token chunks."""
    from src.ingestion.chunker import normalize_chunks, estimate_tokens

    # 1. Test merging tiny siblings
    small_chunks = [
        Chunk(
            chunk_id=f"doc_test#sec_3_clause_{i}",
            document_id="doc_test",
            corpus_collection="legal_statutory",
            text=f"Clause {i}: Substantive rule text for traditional knowledge herbal formulations part {i}." * 3,
            token_count=35,
            jurisdiction="INDIA",
            metadata={"act": "Test Act", "section": "3", "subsection": str(i)},
        )
        for i in range(1, 8)
    ]
    merged = normalize_chunks(small_chunks, min_tokens=200, max_tokens=800)
    assert len(merged) < len(small_chunks)
    assert merged[0].token_count >= 200
    assert "1" in merged[0].metadata.get("subsection", "")

    # 2. Test splitting oversized chunk
    oversized_text = ("This is a long legal section explaining intellectual property rights in India. " * 30 + "\n\n") * 10
    oversized_chunk = Chunk(
        chunk_id="doc_large#sec_1",
        document_id="doc_large",
        corpus_collection="legal_statutory",
        text=oversized_text,
        token_count=estimate_tokens(oversized_text),
        jurisdiction="INDIA",
        metadata={"act": "Large Act", "section": "1"},
    )
    assert oversized_chunk.token_count > 800
    splits = normalize_chunks([oversized_chunk], min_tokens=200, max_tokens=800)
    assert len(splits) >= 2
    for s in splits:
        assert s.token_count <= 800
        assert s.parent_chunk_id == "doc_large#sec_1"

