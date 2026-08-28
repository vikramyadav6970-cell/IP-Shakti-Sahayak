"""Entity extraction module — extracts botanical herbs, jurisdictions, and IP types."""

from src.entity_extraction.extractor import (
    IPType,
    EntitySet,
    EntityExtractor,
    extract_entities,
)

__all__ = [
    "IPType",
    "EntitySet",
    "EntityExtractor",
    "extract_entities",
]
