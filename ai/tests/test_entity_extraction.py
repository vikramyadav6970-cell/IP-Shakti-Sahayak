"""Unit tests for the Entity Extractor and EntitySet."""

import pytest

from src.classification.intent_classifier import DomainIntent
from src.context_gathering.agent import (
    ExportContextObject,
    PatentContextObject,
    MedicinalContextObject,
    BusinessContextObject,
    ResearchContextObject,
)
from src.entity_extraction.extractor import (
    IPType,
    EntitySet,
    EntityExtractor,
    extract_entities,
)


def test_extract_export_scenario():
    """Export Ashwagandha and Tulsi supplement to the EU should extract botanical names, jurisdictions, and ABS."""
    context = ExportContextObject(
        herbs=["Ashwagandha", "Tulsi"],
        destination="European Union (EU)",
        purpose="COMMERCIAL",
        nba_approached=True,
        already_in_market=False,
    )
    question = "Export Ashwagandha and Tulsi supplement to the EU"

    entity_set = extract_entities(context, question)

    assert isinstance(entity_set, EntitySet)
    assert "Withania somnifera" in entity_set.herbs
    assert "Ocimum sanctum" in entity_set.herbs
    assert "INDIA" in entity_set.jurisdictions
    assert "EU" in entity_set.jurisdictions
    assert entity_set.destination_country == "EU"
    assert IPType.EXPORT in entity_set.ip_types
    assert IPType.ABS in entity_set.ip_types


def test_extract_patent_section_3p():
    """A question mentioning Section 3(p) should extract IPType.PATENT and botanical herb name."""
    question = "Can I patent a synergistic extraction method for Curcuma longa overcoming Section 3(p) and TKDL citations?"
    entity_set = extract_entities(question=question)

    assert IPType.PATENT in entity_set.ip_types
    assert "Curcuma longa" in entity_set.herbs
    assert "INDIA" in entity_set.jurisdictions


def test_extract_trademark_and_brand():
    """A trademark question should extract IPType.TRADEMARK and Class info."""
    context = BusinessContextObject(
        product_type="Herbal Cosmetic (Class 3)",
        brand_name="VedaGlow",
        target_market="INDIA",
    )
    question = "How do I register a brand name VedaGlow for my Ayurvedic cosmetic product in Class 3?"

    entity_set = extract_entities(context, question)

    assert IPType.TRADEMARK in entity_set.ip_types


def test_extract_formulation_name():
    """Questions with classical formulations should extract formulation name."""
    question = "What are the testing and licensing requirements for Triphala Churna under Form 24D?"
    entity_set = extract_entities(question=question)

    assert entity_set.formulation_name == "Triphala Churna"
    assert IPType.DRUG_REGULATION in entity_set.ip_types


def test_extract_botanical_synonyms():
    """Sanskrit/vernacular synonyms should map to canonical botanical names."""
    question = "Do I need NBA approval for commercial extraction of Giloy, Mulethi, and Haldi?"
    entity_set = extract_entities(question=question)

    assert "Tinospora cordifolia" in entity_set.herbs  # Giloy
    assert "Glycyrrhiza glabra" in entity_set.herbs     # Mulethi
    assert "Curcuma longa" in entity_set.herbs         # Haldi
    assert IPType.ABS in entity_set.ip_types
