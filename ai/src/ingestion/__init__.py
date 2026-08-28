"""Ingestion module — parsing and collection-aware chunking."""

from src.ingestion.parser import (
    DocumentParser,
    ParsedDocument,
    ParsedSection,
    parse_document,
)
from src.ingestion.chunker import (
    Chunk,
    BaseChunkingStrategy,
    LegalStatutoryChunker,
    StandardsFormulationsChunker,
    CaseLawChunker,
    ProceduralFormsChunker,
    InternationalExportChunker,
    chunk_document,
)

__all__ = [
    "DocumentParser",
    "ParsedDocument",
    "ParsedSection",
    "parse_document",
    "Chunk",
    "BaseChunkingStrategy",
    "LegalStatutoryChunker",
    "StandardsFormulationsChunker",
    "CaseLawChunker",
    "ProceduralFormsChunker",
    "InternationalExportChunker",
    "chunk_document",
]
