"""Unit tests for classification modules (jurisdiction, intent, product)."""

import pytest

from src.classification.jurisdiction_classifier import (
    JurisdictionClassifier,
    JurisdictionClassificationResult,
    classify_jurisdiction,
)
from src.classification.intent_classifier import (
    DomainIntent,
    FineGrainedIntent,
    INTENT_TO_COLLECTIONS_MAP,
    IntentClassificationResult,
    IntentClassifier,
    classify_intent,
)
from src.classification.product_classifier import (
    ProductCategory,
    ProductClassificationInput,
    ProductClassificationResult,
    ProductClassifier,
    classify_product,
)


def test_jurisdiction_default_india():
    """Default UI selection of India with Indian patent question should resolve to INDIA without mismatch."""
    question = "Can I patent an Ayurvedic formulation under Section 3(p) of the Patents Act 1970?"
    res = classify_jurisdiction(question, ui_selected_jurisdiction="INDIA")

    assert isinstance(res, JurisdictionClassificationResult)
    assert res.effective_jurisdiction == "INDIA"
    assert res.ui_selected_jurisdiction == "INDIA"
    assert not res.mismatch_detected
    assert res.warning_message is None


def test_jurisdiction_mismatch_us_fda():
    """When UI is INDIA but question explicitly asks about US FDA / DSHEA, flag mismatch and direct to USA."""
    question = "What are the US FDA DSHEA notification requirements for selling herbal supplements in the United States?"
    res = classify_jurisdiction(question, ui_selected_jurisdiction="INDIA")

    assert res.effective_jurisdiction == "USA"
    assert res.mismatch_detected is True
    assert "USA" in (res.warning_message or "")
    assert res.ui_selected_jurisdiction == "INDIA"


def test_jurisdiction_mismatch_eu_thmpd():
    """When UI is INDIA but question explicitly asks about EU THMPD directive in Germany, flag mismatch and direct to EU."""
    question = "Do I need 30 years of traditional medicinal use evidence under the European EU THMPD directive in Germany?"
    res = classify_jurisdiction(question, ui_selected_jurisdiction="INDIA")

    assert res.effective_jurisdiction == "EU"
    assert res.mismatch_detected is True
    assert "EU" in (res.warning_message or "")


def test_jurisdiction_international_treaty():
    """Treaty-level questions (WIPO GRATK, CBD, TRIPS) should resolve to INTERNATIONAL."""
    question = "What does Article 3 of the WIPO GRATK Treaty require regarding mandatory traditional knowledge patent disclosure?"
    res = classify_jurisdiction(question, ui_selected_jurisdiction="INDIA")

    assert res.effective_jurisdiction == "INTERNATIONAL"


def test_jurisdiction_export_scenario():
    """Export questions from India to foreign markets should detect export intent and target country."""
    question = "Can I export an Ashwagandha and Tulsi supplement from India to the USA under FDA regulations?"
    res = classify_jurisdiction(question, ui_selected_jurisdiction="INDIA")

    assert res.is_export_query is True
    assert res.target_export_country == "USA"
    assert res.effective_jurisdiction == "INTERNATIONAL"


def test_intent_business_domain():
    """Business domain intent should resolve to trademark/GI/design and target legal/standards collections."""
    question = "How do I register a brand name and logo for my Ayurvedic cosmetic product in Class 5?"
    res = classify_intent(question, ui_domain_intent=DomainIntent.BUSINESS)

    assert res.domain_intent == DomainIntent.BUSINESS
    assert FineGrainedIntent.TRADEMARK in res.fine_grained_intents
    assert "legal_statutory" in res.target_collections
    assert "standards_formulations" in res.target_collections


def test_intent_export_domain():
    """Export domain intent should resolve to export/ABS and target international_export + domestic collections."""
    question = "Can I export an Ashwagandha dietary supplement to the EU under THMPD and do I need NBA clearance?"
    res = classify_intent(question, ui_domain_intent=DomainIntent.EXPORT)

    assert res.domain_intent == DomainIntent.EXPORT
    assert FineGrainedIntent.EXPORT in res.fine_grained_intents
    assert FineGrainedIntent.ABS in res.fine_grained_intents
    assert "international_export" in res.target_collections
    assert "legal_statutory" in res.target_collections


def test_intent_medicinal_domain():
    """Medicinal domain intent should resolve to drug/food regulation and target procedural/statutory collections."""
    question = "Is an herbal syrup classified as an Ayurvedic drug or FSSAI Ayurveda Aahara under Indian law?"
    res = classify_intent(question, ui_domain_intent=DomainIntent.MEDICINAL)

    assert res.domain_intent == DomainIntent.MEDICINAL
    assert (
        FineGrainedIntent.DRUG_REGULATION in res.fine_grained_intents
        or FineGrainedIntent.FOOD_REGULATION in res.fine_grained_intents
    )
    assert "legal_statutory" in res.target_collections
    assert "procedural_forms" in res.target_collections


def test_intent_patent_domain():
    """Patent domain intent should resolve to patent/TKDL and include case_law_prior_art."""
    question = "Can I get a patent for a synergistic extraction process of Curcuma longa overcoming Section 3(p) and TKDL prior art?"
    res = classify_intent(question, ui_domain_intent=DomainIntent.PATENT)

    assert res.domain_intent == DomainIntent.PATENT
    assert FineGrainedIntent.PATENT in res.fine_grained_intents
    assert FineGrainedIntent.TKDL in res.fine_grained_intents
    assert "case_law_prior_art" in res.target_collections
    assert "legal_statutory" in res.target_collections


def test_intent_research_domain():
    """Research domain intent should resolve to ABS and procedural forms."""
    question = "Do foreign university researchers need NBA Form I and benefit sharing approval to access Indian medicinal plants?"
    res = classify_intent(question, ui_domain_intent=DomainIntent.RESEARCH)

    assert res.domain_intent == DomainIntent.RESEARCH
    assert FineGrainedIntent.ABS in res.fine_grained_intents
    assert "procedural_forms" in res.target_collections
    assert "legal_statutory" in res.target_collections


def test_intent_other_domain_fallback():
    """OTHER domain intent should infer fine-grained intent from text keywords."""
    question = "How do I register a new plant variety under the PPV&FR Act?"
    res = classify_intent(question, ui_domain_intent=DomainIntent.OTHER)

    assert res.domain_intent == DomainIntent.OTHER
    assert FineGrainedIntent.PLANT_VARIETY in res.fine_grained_intents
    assert "legal_statutory" in res.target_collections


# =========================================================================
# Product Classification Rules Engine Tests
# =========================================================================

def test_product_classifier_classical_ayurvedic_medicine():
    """Direct First Schedule formulation without novel excipients must classify as CLASSICAL_AYURVEDIC_MEDICINE."""
    inp = ProductClassificationInput(
        product_type="MEDICINE",
        derived_from_authoritative_text=True,
        authoritative_text_name="Charaka Samhita",
        has_novel_excipients_or_actives=False,
        intended_use_therapeutic=True,
    )
    res = classify_product(inp)

    assert res.category == ProductCategory.CLASSICAL_AYURVEDIC_MEDICINE
    assert res.confidence == 1.0
    assert res.required_licensing_form is not None and "Form 24D" in res.required_licensing_form
    assert any("RULE_CLASSICAL_AYUSH_MEDICINE" in r for r in res.rules_fired)


def test_product_classifier_proprietary_medicine():
    """Novel combination of classical ingredients in modern dosage form must classify as PROPRIETARY_MEDICINE."""
    inp = ProductClassificationInput(
        product_type="MEDICINE",
        derived_from_authoritative_text=False,
        intended_use_therapeutic=True,
        has_novel_excipients_or_actives=False,
        standardized_fractional_extract=False,
    )
    res = classify_product(inp)

    assert res.category == ProductCategory.PROPRIETARY_MEDICINE
    assert any("RULE_PROPRIETARY_ASU_MEDICINE" in r for r in res.rules_fired)
    assert res.required_licensing_form is not None and "Rule 158B" in res.required_licensing_form


def test_product_classifier_phytopharmaceutical():
    """Standardized fractional extract with bioactive markers must classify as PHYTOPHARMACEUTICAL."""
    inp = ProductClassificationInput(
        product_type="EXTRACT",
        standardized_fractional_extract=True,
        intended_use_therapeutic=True,
    )
    res = classify_product(inp)

    assert res.category == ProductCategory.PHYTOPHARMACEUTICAL
    assert "CDSCO" in res.statutory_authority
    assert any("RULE_PHYTOPHARMACEUTICAL_APPLIED" in r for r in res.rules_fired)


def test_product_classifier_ayurveda_aahara():
    """Traditional recipe for dietary sustenance without disease cure or synthetic additives must classify as AYURVEDA_AAHARA."""
    inp = ProductClassificationInput(
        product_type="FOOD",
        intended_as_dietary_sustenance=True,
        intended_use_therapeutic=False,
        derived_from_authoritative_text=True,
        contains_synthetic_vitamins_or_minerals=False,
    )
    res = classify_product(inp)

    assert res.category == ProductCategory.AYURVEDA_AAHARA
    assert "FSSAI" in res.statutory_authority
    assert any("RULE_AYURVEDA_AAHARA_QUALIFIED" in r for r in res.rules_fired)


def test_product_classifier_cosmetic():
    """Topical beauty product without medical claims must classify as COSMETIC."""
    inp = ProductClassificationInput(
        product_type="COSMETIC",
        topical_beautification_only=True,
        intended_use_therapeutic=False,
    )
    res = classify_product(inp)

    assert res.category == ProductCategory.COSMETIC
    assert any("RULE_COSMETIC_APPLIED" in r for r in res.rules_fired)


def test_product_classifier_edge_case_synthetic_aahara():
    """Ayurveda Aahara with synthetic vitamins must be rejected and return UNCLEAR."""
    inp = ProductClassificationInput(
        product_type="FOOD",
        intended_as_dietary_sustenance=True,
        contains_synthetic_vitamins_or_minerals=True,
    )
    res = classify_product(inp)

    assert res.category == ProductCategory.UNCLEAR
    assert any("RULE_AAHARA_SYNTHETIC_PROHIBITION" in r for r in res.rules_fired)


def test_product_classifier_edge_case_therapeutic_food():
    """Food product claiming disease cure must return UNCLEAR due to regulatory violation."""
    inp = ProductClassificationInput(
        product_type="FOOD",
        intended_as_dietary_sustenance=True,
        intended_use_therapeutic=True,
    )
    res = classify_product(inp)

    assert res.category == ProductCategory.UNCLEAR
    assert any("RULE_AAHARA_NO_DISEASE_CLAIMS" in r for r in res.rules_fired)


def test_product_classifier_edge_case_therapeutic_cosmetic():
    """Cosmetic product claiming disease treatment must return UNCLEAR due to category conflict."""
    inp = ProductClassificationInput(
        product_type="COSMETIC",
        topical_beautification_only=True,
        intended_use_therapeutic=True,
    )
    res = classify_product(inp)

    assert res.category == ProductCategory.UNCLEAR
    assert any("RULE_COSMETIC_THERAPEUTIC_CONFLICT" in r for r in res.rules_fired)
