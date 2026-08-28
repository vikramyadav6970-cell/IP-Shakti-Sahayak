"""Citations module — zero-hallucination citation validator."""

from src.citations.validator import (
    CitationValidationResult,
    CitationValidator,
    validate_citations,
)

__all__ = [
    "CitationValidationResult",
    "CitationValidator",
    "validate_citations",
]
