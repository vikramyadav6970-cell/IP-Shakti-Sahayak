"""Deterministic product classification rules engine.

Encodes context.md §2 Rule 6, context.md §5, and coding_conventions.md Rule 3:
- Fully auditable rules engine (no stochastic LLM inference).
- Encodes explicit FSSAI Ayurveda-Aahara food-vs-drug boundaries (2022 Regulations).
- Evaluates Drugs and Cosmetics Act 1940 Chapter IVA (Classical vs. Proprietary ASU medicine).
- Evaluates CDSCO Phytopharmaceutical Drug regulations (Rule 122E).
- Returns classification category, regulatory pathway, licensing form, and fired rules.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ProductCategory(str, Enum):
    """Authoritative legal product categories under Indian regulatory frameworks."""

    CLASSICAL_AYURVEDIC_MEDICINE = "CLASSICAL_AYURVEDIC_MEDICINE"
    PROPRIETARY_MEDICINE = "PROPRIETARY_MEDICINE"
    NEW_NON_CLASSICAL_DRUG = "NEW_NON_CLASSICAL_DRUG"
    PHYTOPHARMACEUTICAL = "PHYTOPHARMACEUTICAL"
    AYURVEDA_AAHARA = "AYURVEDA_AAHARA"
    COSMETIC = "COSMETIC"
    UNCLEAR = "UNCLEAR"


@dataclass
class ProductClassificationInput:
    """Input payload representing wizard answers for product classification."""

    product_type: str  # "MEDICINE" | "FOOD" | "FOOD_SUPPLEMENT" | "COSMETIC" | "EXTRACT" | "OTHER"
    derived_from_authoritative_text: Optional[bool] = None  # In First Schedule 54 books (Drugs Act)
    authoritative_text_name: Optional[str] = None  # e.g., "Charaka Samhita", "AFI", "API"
    has_novel_excipients_or_actives: Optional[bool] = None  # New chemical entities or synthetic additives
    standardized_fractional_extract: Optional[bool] = None  # Purified enriched fraction with marker compounds
    intended_use_therapeutic: Optional[bool] = None  # Intended for disease treatment/cure/mitigation
    intended_as_dietary_sustenance: Optional[bool] = None  # Intended as food/nourishment
    contains_synthetic_vitamins_or_minerals: Optional[bool] = None  # Synthetic fortification
    topical_beautification_only: Optional[bool] = None  # Cleansing/beautifying without medical claims
    biological_resources_used: Optional[List[str]] = None
    manufacturing_in_india: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProductClassificationResult:
    """Auditable product classification outcome."""

    category: ProductCategory
    confidence: float
    regulatory_pathway: str
    governing_act_and_rules: str
    required_licensing_form: Optional[str]
    statutory_authority: str
    rules_fired: List[str]
    key_compliance_requirements: List[str]


class ProductClassifier:
    """Deterministic, auditable statutory rules engine for product classification."""

    def classify(self, inputs: ProductClassificationInput) -> ProductClassificationResult:
        """Evaluate input against deterministic legal rules and return classification."""
        rules_fired: List[str] = []
        p_type = (inputs.product_type or "").upper().strip()

        # =========================================================================
        # Rule Branch 1: Cosmetic
        # =========================================================================
        if p_type == "COSMETIC" or inputs.topical_beautification_only is True:
            if inputs.intended_use_therapeutic is True:
                rules_fired.append("RULE_COSMETIC_THERAPEUTIC_CONFLICT: Cosmetic making therapeutic claims cannot be licensed as pure cosmetic.")
                return ProductClassificationResult(
                    category=ProductCategory.UNCLEAR,
                    confidence=0.60,
                    regulatory_pathway="Ambiguous: Product claims to be a cosmetic but asserts therapeutic disease treatment claims. Requires claim modification.",
                    governing_act_and_rules="Drugs and Cosmetics Act, 1940 (Section 3(aa) vs Section 3(a))",
                    required_licensing_form=None,
                    statutory_authority="State Licensing Authority (AYUSH / CDSCO)",
                    rules_fired=rules_fired,
                    key_compliance_requirements=[
                        "Remove therapeutic/disease cure claims to qualify as AYUSH Cosmetic (Class 3)",
                        "Or reformulate and file under ASU Proprietary Medicine (Form 24D) if therapeutic efficacy is intended",
                    ],
                )

            rules_fired.append("RULE_COSMETIC_APPLIED: Product intended exclusively for external beautification/cleansing without therapeutic claims.")
            return ProductClassificationResult(
                category=ProductCategory.COSMETIC,
                confidence=1.0,
                regulatory_pathway="AYUSH Cosmetic Manufacturing License / CDSCO Cosmetic Notification",
                governing_act_and_rules="Drugs and Cosmetics Act, 1940 (Section 3(aa)) and Drugs and Cosmetics Rules, 1945 (Part XIII/Schedule T)",
                required_licensing_form="Form 32 / State AYUSH Cosmetic License",
                statutory_authority="State Licensing Authority (AYUSH)",
                rules_fired=rules_fired,
                key_compliance_requirements=[
                    "Compliance with Schedule T / Cosmetic GMP guidelines",
                    "No therapeutic or medicinal claims on product packaging or labeling",
                    "List of permitted herbal ingredients and preservatives",
                ],
            )

        # =========================================================================
        # Rule Branch 2: FSSAI Ayurveda Aahara (2022 Regulations)
        # =========================================================================
        if p_type in ["FOOD", "FOOD_SUPPLEMENT"] or inputs.intended_as_dietary_sustenance is True:
            # Check for synthetic fortification violation
            if inputs.contains_synthetic_vitamins_or_minerals is True:
                rules_fired.append("RULE_AAHARA_SYNTHETIC_PROHIBITION: FSSAI Ayurveda Aahara strictly prohibits synthetic vitamins or mineral fortification.")
                return ProductClassificationResult(
                    category=ProductCategory.UNCLEAR,
                    confidence=0.85,
                    regulatory_pathway="Cannot qualify as Ayurveda Aahara due to synthetic fortification. Must file as standard FSSAI Nutraceutical/Food Supplement.",
                    governing_act_and_rules="Food Safety and Standards (Ayurveda Aahara) Regulations, 2022 (Regulation 4(1))",
                    required_licensing_form="FSSAI Central / State License (Nutraceutical Category)",
                    statutory_authority="Food Safety and Standards Authority of India (FSSAI)",
                    rules_fired=rules_fired,
                    key_compliance_requirements=[
                        "Remove synthetic vitamins/minerals to seek Ayurveda Aahara certification",
                        "Or seek regular FSSAI Health Supplement / Nutraceutical License under FSS (Health Supplements and Nutraceuticals) Regulations, 2022",
                    ],
                )

            # Check for therapeutic disease cure claim violation
            if inputs.intended_use_therapeutic is True:
                rules_fired.append("RULE_AAHARA_NO_DISEASE_CLAIMS: Ayurveda Aahara cannot make therapeutic, diagnostic, or disease cure claims.")
                return ProductClassificationResult(
                    category=ProductCategory.UNCLEAR,
                    confidence=0.80,
                    regulatory_pathway="Conflict: Food products cannot claim disease treatment/cure. Must be classified as Ayurvedic Medicine or remove therapeutic claims.",
                    governing_act_and_rules="Food Safety and Standards (Ayurveda Aahara) Regulations, 2022 & Drugs and Cosmetics Act, 1940",
                    required_licensing_form=None,
                    statutory_authority="FSSAI / State Licensing Authority",
                    rules_fired=rules_fired,
                    key_compliance_requirements=[
                        "If disease cure/treatment is intended: Must apply for ASU Drug Manufacturing License (Form 24D)",
                        "If marketed as Food/Ayurveda Aahara: Must restrict claims to dietary sustenance and physiological support without disease prevention/cure claims",
                    ],
                )

            # Valid Ayurveda Aahara
            if inputs.derived_from_authoritative_text is True or inputs.has_novel_excipients_or_actives is False:
                rules_fired.append("RULE_AYURVEDA_AAHARA_QUALIFIED: Food prepared per recipes/principles of First Schedule treatises without synthetic additives or disease cure claims.")
                return ProductClassificationResult(
                    category=ProductCategory.AYURVEDA_AAHARA,
                    confidence=1.0,
                    regulatory_pathway="FSSAI Ayurveda Aahara Licensing Pathway",
                    governing_act_and_rules="Food Safety and Standards (Ayurveda Aahara) Regulations, 2022 (F. No. Std/SP-05/A-Aahara/FSSAI-2021)",
                    required_licensing_form="FSSAI Food Business Operator (FBO) License under Category 100",
                    statutory_authority="Food Safety and Standards Authority of India (FSSAI)",
                    rules_fired=rules_fired,
                    key_compliance_requirements=[
                        "Mandatory display of the official 'Ayurveda Aahara' logo on label",
                        "Must state the target consumer group and physiological purpose",
                        "Strict prohibition of synthetic vitamins, minerals, and amino acids",
                        "No disease prevention, diagnosis, treatment, or mitigation claims permitted on label",
                    ],
                )

        # =========================================================================
        # Rule Branch 3: Phytopharmaceutical Drug (Rule 122E / CDSCO)
        # =========================================================================
        if inputs.standardized_fractional_extract is True:
            rules_fired.append("RULE_PHYTOPHARMACEUTICAL_APPLIED: Purified and standardized fractional extract from plant origin with minimum 4 bio-active markers for modern medical indication.")
            return ProductClassificationResult(
                category=ProductCategory.PHYTOPHARMACEUTICAL,
                confidence=1.0,
                regulatory_pathway="CDSCO Phytopharmaceutical Drug Approval Pathway (Central DCGI)",
                governing_act_and_rules="Drugs and Cosmetics Rules, 1945 (Rule 122-E, Schedule Y/New Drugs & Clinical Trials Rules 2019)",
                required_licensing_form="Form 44 / Form CT-06 (CDSCO SUGAM Portal)",
                statutory_authority="Central Drugs Standard Control Organization (CDSCO) / DCGI",
                rules_fired=rules_fired,
                key_compliance_requirements=[
                    "Chromatographic fingerprinting and assay of at least 4 bioactive marker compounds",
                    "Safety and preclinical toxicology dossier",
                    "Phase I, II, and III Clinical Trials approval from CDSCO",
                    "GMP manufacturing in accordance with modern pharmaceutical standards",
                ],
            )

        # =========================================================================
        # Rule Branch 4: New Non-Classical Drug (Synthetic or novel chemical additives)
        # =========================================================================
        if inputs.has_novel_excipients_or_actives is True and (
            inputs.derived_from_authoritative_text is False
            or inputs.contains_synthetic_vitamins_or_minerals is True
        ):
            rules_fired.append("RULE_NEW_NON_CLASSICAL_DRUG: Product contains synthetic active substances or non-classical chemical modifications.")
            return ProductClassificationResult(
                category=ProductCategory.NEW_NON_CLASSICAL_DRUG,
                confidence=0.95,
                regulatory_pathway="New Drug Approval & Clinical Trials Pathway under CDSCO",
                governing_act_and_rules="New Drugs and Clinical Trials Rules, 2019 and Drugs and Cosmetics Act, 1940",
                required_licensing_form="Form CT-04 / CT-06 (CDSCO)",
                statutory_authority="Central Drugs Standard Control Organization (CDSCO)",
                rules_fired=rules_fired,
                key_compliance_requirements=[
                    "Cannot be licensed under Chapter IVA as an Ayurvedic/ASU medicine",
                    "Full preclinical toxicology, IND application, and Phase I-III clinical trials mandatory",
                ],
            )

        # =========================================================================
        # Rule Branch 5: Classical Ayurvedic Medicine (Drugs Act Sec 3(a))
        # =========================================================================
        if (
            inputs.derived_from_authoritative_text is True
            and inputs.has_novel_excipients_or_actives is not True
        ):
            text_cite = inputs.authoritative_text_name or "First Schedule Classical Treatise"
            rules_fired.append(f"RULE_CLASSICAL_AYUSH_MEDICINE: Formulation manufactured strictly per authoritative formula in {text_cite} (First Schedule, Drugs Act).")
            return ProductClassificationResult(
                category=ProductCategory.CLASSICAL_AYURVEDIC_MEDICINE,
                confidence=1.0,
                regulatory_pathway="Classical ASU Drug Manufacturing License (State AYUSH Licensing Authority)",
                governing_act_and_rules="Drugs and Cosmetics Act, 1940 (Section 3(a)) and Drugs and Cosmetics Rules, 1945 (Part XVI)",
                required_licensing_form="Form 24D (Manufacturing License) / Form 24E (Loan License)",
                statutory_authority="State Licensing Authority (AYUSH)",
                rules_fired=rules_fired,
                key_compliance_requirements=[
                    f"Direct citation of classical recipe from authoritative treatise: {text_cite}",
                    "Schedule T Good Manufacturing Practice (GMP) compliance",
                    "No requirement for new clinical safety/efficacy trials (ancient traditional use recognized)",
                    "Quality control testing per Ayurvedic Pharmacopoeia of India (API) standards",
                ],
            )

        # =========================================================================
        # Rule Branch 6: ASU Proprietary Medicine (Drugs Act Sec 3(h) & Rule 158B)
        # =========================================================================
        if (
            inputs.intended_use_therapeutic is True
            or p_type == "MEDICINE"
            or inputs.derived_from_authoritative_text is False
        ):
            rules_fired.append("RULE_PROPRIETARY_ASU_MEDICINE: Formulation contains ingredients listed in authoritative texts but in novel proportions, dosage forms, or proprietary combinations (Rule 158B).")
            return ProductClassificationResult(
                category=ProductCategory.PROPRIETARY_MEDICINE,
                confidence=0.95,
                regulatory_pathway="Ayurvedic Proprietary Medicine License under Rule 158B",
                governing_act_and_rules="Drugs and Cosmetics Act, 1940 (Section 3(h)) and Drugs and Cosmetics Rules, 1945 (Rule 158-B)",
                required_licensing_form="Form 24D with Rule 158B Proof of Safety and Efficacy Dossier",
                statutory_authority="State Licensing Authority (AYUSH)",
                rules_fired=rules_fired,
                key_compliance_requirements=[
                    "All active herbal ingredients must be individually recognized in First Schedule classical texts",
                    "Submission of Rule 158B proof of safety and efficacy dossier (published pilot studies or literature evidence)",
                    "Schedule T GMP compliance",
                    "Heavy metal, pesticide residue, and microbial limit testing per PCIM&H standards",
                ],
            )

        # =========================================================================
        # Fallback: UNCLEAR
        # =========================================================================
        rules_fired.append("RULE_INSUFFICIENT_DATA: Insufficient inputs provided to deterministically classify product.")
        return ProductClassificationResult(
            category=ProductCategory.UNCLEAR,
            confidence=0.50,
            regulatory_pathway="Undetermined. Please complete the product classification wizard.",
            governing_act_and_rules="Drugs and Cosmetics Act, 1940 / Food Safety and Standards Act, 2006",
            required_licensing_form=None,
            statutory_authority="State AYUSH / FSSAI",
            rules_fired=rules_fired,
            key_compliance_requirements=[
                "Clarify intended use (therapeutic disease treatment vs. dietary nourishment)",
                "Specify whether formulation is derived directly from First Schedule classical treatises",
            ],
        )


# Module-level convenience classifier instance
default_product_classifier = ProductClassifier()


def classify_product(inputs: ProductClassificationInput) -> ProductClassificationResult:
    """Classify a product deterministically using statutory rules."""
    return default_product_classifier.classify(inputs)
