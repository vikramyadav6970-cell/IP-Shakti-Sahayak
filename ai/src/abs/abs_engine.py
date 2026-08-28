"""Access and Benefit Sharing (ABS) Assessment Engine.

Encodes the statutory provisions of:
- Biological Diversity Act, 2002 (as amended by Biological Diversity (Amendment) Act, 2023)
- Biological Diversity Rules, 2024 & 2004
- NBA Guidelines on Access to Biological Resources and Benefit Sharing Regulations, 2014

Determines ABS relevance (HIGH/MEDIUM/LOW/NOT_APPLICABLE), mandatory approval paths
(NBA Form I, II, III, IV vs. SBB Intimation), benefit sharing fee estimates, and
actionable ordered next steps.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ABSRelevance(str, Enum):
    """ABS relevance classification tier."""

    HIGH = "HIGH"  # Mandatory NBA prior approval required before action/grant
    MEDIUM = "MEDIUM"  # Mandatory SBB prior intimation / compliance required
    LOW = "LOW"  # Advisory compliance or conditional exemption
    NOT_APPLICABLE = "NOT_APPLICABLE"  # Completely exempt under BDA provisions


class ApplicantType(str, Enum):
    """Legal profile of the applicant accessing biological resources."""

    NON_INDIAN_OR_FOREIGN_CONTROLLED = "NON_INDIAN_OR_FOREIGN_CONTROLLED"  # Section 3 entity
    INDIAN_ENTITY_OR_CITIZEN = "INDIAN_ENTITY_OR_CITIZEN"  # Section 7 entity
    REGISTERED_AYUSH_PRACTITIONER = "REGISTERED_AYUSH_PRACTITIONER"  # 2023 Amendment Section 7 exemption
    LOCAL_COMMUNITY_OR_VAIDYA = "LOCAL_COMMUNITY_OR_VAIDYA"  # Section 7 proviso exemption


class AccessPurpose(str, Enum):
    """Intended purpose of accessing the biological resource or traditional knowledge."""

    COMMERCIAL_UTILIZATION = "COMMERCIAL_UTILIZATION"
    IPR_APPLICATION = "IPR_APPLICATION"
    RESEARCH_AND_DEVELOPMENT = "RESEARCH_AND_DEVELOPMENT"
    TRANSFER_OF_RESEARCH_RESULTS = "TRANSFER_OF_RESEARCH_RESULTS"
    THIRD_PARTY_TRANSFER = "THIRD_PARTY_TRANSFER"
    DOMESTIC_CONSUMPTION_ONLY = "DOMESTIC_CONSUMPTION_ONLY"


@dataclass
class ABSAssessmentInput:
    """Input payload representing applicant profile and biological resource utilization."""

    biological_resources: List[str]  # e.g., ["Withania somnifera", "Ocimum sanctum"]
    origin_country: str = "INDIA"
    geographic_location_in_india: Optional[str] = None
    is_cultivated_source: Optional[bool] = None
    is_normally_traded_commodity: Optional[bool] = None  # Section 40 NTAC list
    applicant_type: ApplicantType = ApplicantType.INDIAN_ENTITY_OR_CITIZEN
    access_purpose: AccessPurpose = AccessPurpose.COMMERCIAL_UTILIZATION
    access_already_occurred: bool = False
    intending_to_apply_for_ipr: bool = False
    foreign_collaboration_or_transfer: bool = False
    annual_turnover_inr: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ABSAssessmentResult:
    """Detailed ABS assessment outcome."""

    relevance: ABSRelevance
    nba_approval_required: bool
    sbb_intimation_required: bool
    governing_sections: List[str]
    applicable_forms: List[str]
    benefit_sharing_estimate: Optional[str]
    ordered_next_steps: List[str]
    exemptions_applicable: List[str]
    rules_fired: List[str]
    confidence: float = 1.0


class ABSEngine:
    """Rule-based engine assessing ABS liability under Indian Biodiversity Law."""

    def assess(self, inputs: ABSAssessmentInput) -> ABSAssessmentResult:
        """Evaluate ABS obligations deterministically against statutory rules."""
        rules_fired: List[str] = []
        governing_sections: List[str] = []
        applicable_forms: List[str] = []
        exemptions: List[str] = []
        next_steps: List[str] = []

        # =========================================================================
        # Rule Branch 1: Non-Indian Biological Resource
        # =========================================================================
        if inputs.origin_country.upper().strip() != "INDIA":
            rules_fired.append("RULE_NON_INDIAN_ORIGIN: Resource origin is outside India; Indian Biological Diversity Act 2002 does not apply.")
            return ABSAssessmentResult(
                relevance=ABSRelevance.NOT_APPLICABLE,
                nba_approval_required=False,
                sbb_intimation_required=False,
                governing_sections=["Non-Indian Jurisdiction"],
                applicable_forms=[],
                benefit_sharing_estimate=None,
                ordered_next_steps=[
                    "Verify compliance with the provider country's national ABS legislation under the Nagoya Protocol.",
                    "Ensure valid Prior Informed Consent (PIC) and Mutually Agreed Terms (MAT) from country of origin.",
                ],
                exemptions_applicable=["Indian Biological Diversity Act applies strictly to biological resources obtained from India."],
                rules_fired=rules_fired,
            )

        # =========================================================================
        # Rule Branch 2: IPR Application (Section 6 — Highest Priority Over-ride)
        # =========================================================================
        if inputs.intending_to_apply_for_ipr or inputs.access_purpose == AccessPurpose.IPR_APPLICATION:
            governing_sections.append("Section 6(1), Biological Diversity Act 2002")
            applicable_forms.append("NBA Form III (Application for IPR Approval)")
            rules_fired.append("RULE_SECTION_6_IPR_MANDATE: Mandatory prior approval from NBA is legally required before applying for any IPR inside or outside India based on Indian biological resources/knowledge.")

            benefit_sharing = (
                "2% to 5% of the royalty received on commercialization of the IPR, "
                "or 0.2% to 1.0% of ex-factory commercial sales (Regulation 8, ABS Guidelines 2014)."
            )

            next_steps.extend([
                "1. Prepare and file NBA Form III before or immediately upon filing patent application.",
                "2. Ensure patent complete specification under Section 10(4)(d)(ii) of the Indian Patents Act explicitly discloses the geographical source and origin of biological materials.",
                "3. Patent examiner will pause final patent grant pending receipt of NBA clearance certificate under Section 6.",
                "4. Execute the Benefit Sharing Agreement with NBA prior to commercial exploitation of the patented invention.",
            ])

            # Check if applicant is foreign or transferring results as well
            if inputs.applicant_type == ApplicantType.NON_INDIAN_OR_FOREIGN_CONTROLLED:
                governing_sections.append("Section 3, Biological Diversity Act 2002")
                applicable_forms.insert(0, "NBA Form I (Access Approval)")
                rules_fired.append("RULE_SECTION_3_FOREIGN_APPLICANT: Non-Indian applicant must also obtain Form I approval for accessing the biological resource.")

            return ABSAssessmentResult(
                relevance=ABSRelevance.HIGH,
                nba_approval_required=True,
                sbb_intimation_required=False,
                governing_sections=governing_sections,
                applicable_forms=applicable_forms,
                benefit_sharing_estimate=benefit_sharing,
                ordered_next_steps=next_steps,
                exemptions_applicable=exemptions,
                rules_fired=rules_fired,
            )

        # =========================================================================
        # Rule Branch 3: Foreign Citizen / Non-Indian / Foreign-Controlled Corporate
        # =========================================================================
        if inputs.applicant_type == ApplicantType.NON_INDIAN_OR_FOREIGN_CONTROLLED:
            governing_sections.append("Section 3 & Section 19, Biological Diversity Act 2002")
            applicable_forms.append("NBA Form I (Application for Access to Biological Resources)")
            rules_fired.append("RULE_SECTION_3_NON_INDIAN_ACCESS: Non-Indian citizens, NRI entities, and foreign-controlled/incorporated bodies must obtain NBA Form I approval before accessing any Indian biological resource.")

            benefit_sharing = "0.1% to 0.5% of annual ex-factory gross sales or mutually agreed terms under ABS Regulations 2014."

            next_steps.extend([
                "1. Submit NBA Form I online via the NBA ABS e-filing portal.",
                "2. Detail target taxa, collection coordinates, quantity, and purpose (commercial utilization / bio-survey).",
                "3. Consult and obtain consent from local Biodiversity Management Committees (BMCs) via NBA.",
                "4. Execute ABS agreement and pay statutory application fee before physical extraction/export of biological material.",
            ])

            return ABSAssessmentResult(
                relevance=ABSRelevance.HIGH,
                nba_approval_required=True,
                sbb_intimation_required=False,
                governing_sections=governing_sections,
                applicable_forms=applicable_forms,
                benefit_sharing_estimate=benefit_sharing,
                ordered_next_steps=next_steps,
                exemptions_applicable=exemptions,
                rules_fired=rules_fired,
            )

        # =========================================================================
        # Rule Branch 4: Transfer of Research Results to Foreign Entity (Section 4)
        # =========================================================================
        if (
            inputs.access_purpose == AccessPurpose.TRANSFER_OF_RESEARCH_RESULTS
            or inputs.foreign_collaboration_or_transfer
        ):
            governing_sections.append("Section 4 & Section 19, Biological Diversity Act 2002")
            applicable_forms.append("NBA Form II (Application for Transfer of Research Results)")
            rules_fired.append("RULE_SECTION_4_RESEARCH_TRANSFER: Transferring results of research relating to Indian biological resources to non-Indian entities requires mandatory NBA Form II approval.")

            next_steps.extend([
                "1. Submit NBA Form II prior to signing collaboration agreement or transferring research data/results abroad.",
                "2. Exempt only if research is under collaborative projects approved by Central Government (Section 5).",
            ])

            return ABSAssessmentResult(
                relevance=ABSRelevance.HIGH,
                nba_approval_required=True,
                sbb_intimation_required=False,
                governing_sections=governing_sections,
                applicable_forms=applicable_forms,
                benefit_sharing_estimate="Mutually agreed terms evaluated case-by-case by NBA.",
                ordered_next_steps=next_steps,
                exemptions_applicable=exemptions,
                rules_fired=rules_fired,
            )

        # =========================================================================
        # Rule Branch 5: Third-Party Transfer (Section 20)
        # =========================================================================
        if inputs.access_purpose == AccessPurpose.THIRD_PARTY_TRANSFER:
            governing_sections.append("Section 20, Biological Diversity Act 2002")
            applicable_forms.append("NBA Form IV (Application for Third Party Transfer)")
            rules_fired.append("RULE_SECTION_20_THIRD_PARTY: Transferring already accessed biological resources or knowledge to third parties requires prior NBA approval.")

            return ABSAssessmentResult(
                relevance=ABSRelevance.HIGH,
                nba_approval_required=True,
                sbb_intimation_required=False,
                governing_sections=governing_sections,
                applicable_forms=applicable_forms,
                benefit_sharing_estimate="Equal to original access agreement terms or supplementary fee.",
                ordered_next_steps=["Submit NBA Form IV and obtain formal sanction before handing over materials."],
                exemptions_applicable=exemptions,
                rules_fired=rules_fired,
            )

        # =========================================================================
        # Rule Branch 6: Section 40 NTAC Exemption (Normally Traded Commodities)
        # =========================================================================
        if inputs.is_normally_traded_commodity is True:
            exemptions.append("Section 40 Exemption: Biological resources notified by Central Government as Normally Traded Commodities (NTAC list) are exempt from SBB prior intimation when traded as raw commodities.")
            rules_fired.append("RULE_SECTION_40_NTAC: Commercial trading of notified agricultural/spice commodities without proprietary IPR claims is exempt.")

            return ABSAssessmentResult(
                relevance=ABSRelevance.NOT_APPLICABLE,
                nba_approval_required=False,
                sbb_intimation_required=False,
                governing_sections=["Section 40, Biological Diversity Act 2002"],
                applicable_forms=[],
                benefit_sharing_estimate=None,
                ordered_next_steps=[
                    "Maintain commodity purchase invoices verifying sourcing from standard Mandis / agricultural trade.",
                    "If subsequent IPR or foreign export for bio-prospecting is initiated, Section 6 / Section 3 will reactivate.",
                ],
                exemptions_applicable=exemptions,
                rules_fired=rules_fired,
            )

        # =========================================================================
        # Rule Branch 7: Registered Ayush Practitioners & Vaids (2023 Amendment)
        # =========================================================================
        if inputs.applicant_type in [
            ApplicantType.REGISTERED_AYUSH_PRACTITIONER,
            ApplicantType.LOCAL_COMMUNITY_OR_VAIDYA,
        ]:
            exemptions.append(
                "2023 Amendment Relief: Registered Ayush practitioners, local vaids, and hakims practicing indigenous medicine are explicitly exempt from prior intimation to State Biodiversity Boards."
            )
            rules_fired.append("RULE_AYUSH_PRACTITIONER_EXEMPTION: Registered Indian Ayush practitioner conducting clinical practice is exempt under Section 7 proviso (2023 Amendment).")

            return ABSAssessmentResult(
                relevance=ABSRelevance.NOT_APPLICABLE,
                nba_approval_required=False,
                sbb_intimation_required=False,
                governing_sections=["Section 7 Proviso, Biological Diversity (Amendment) Act 2023"],
                applicable_forms=[],
                benefit_sharing_estimate=None,
                ordered_next_steps=["Maintain state Ayush practitioner registration certificate on record."],
                exemptions_applicable=exemptions,
                rules_fired=rules_fired,
            )

        # =========================================================================
        # Rule Branch 8: Indian Commercial Manufacturers (Section 7 SBB Intimation)
        # =========================================================================
        if (
            inputs.applicant_type == ApplicantType.INDIAN_ENTITY_OR_CITIZEN
            and inputs.access_purpose == AccessPurpose.COMMERCIAL_UTILIZATION
        ):
            governing_sections.append("Section 7 & Section 24, Biological Diversity Act 2002")
            applicable_forms.append("State Biodiversity Board (SBB) Prior Intimation Form")
            rules_fired.append("RULE_SECTION_7_INDIAN_COMMERCIAL: Indian entities commercializing biological resources must give prior intimation to the concerned State Biodiversity Board.")

            # Check for cultivated medicinal plant exemption under 2023 amendment
            if inputs.is_cultivated_source is True:
                exemptions.append("2023 Amendment Provision: Cultivated medicinal plants sourced from certified growers receive fast-tracked processing and conditional benefit-sharing exemptions under state rules.")
                benefit_sharing = "Exempt or discounted benefit sharing upon producing certified cultivation source certificate."
                relevance = ABSRelevance.LOW
            else:
                benefit_sharing = (
                    "0.1% of annual ex-factory gross sales for turnover up to INR 1 Crore;\n"
                    "0.2% for turnover between INR 1 Crore and 3 Crores;\n"
                    "0.5% for turnover exceeding INR 3 Crores (ABS Guidelines 2014 Regulation 11)."
                )
                relevance = ABSRelevance.MEDIUM

            next_steps.extend([
                "1. File prior intimation with the State Biodiversity Board (SBB) of the state where biological resources are sourced/manufactured.",
                "2. If herbs are cultivated, obtain Cultivation Certificate from Gram Panchayat / District Agriculture Officer to claim exemption/discount.",
                "3. Calculate and remit the statutory ABS percentage based on ex-factory commercial sales turnover.",
                "4. Maintain trace records of batch procurement from certified local suppliers.",
            ])

            return ABSAssessmentResult(
                relevance=relevance,
                nba_approval_required=False,
                sbb_intimation_required=True,
                governing_sections=governing_sections,
                applicable_forms=applicable_forms,
                benefit_sharing_estimate=benefit_sharing,
                ordered_next_steps=next_steps,
                exemptions_applicable=exemptions,
                rules_fired=rules_fired,
            )

        # =========================================================================
        # Fallback: Domestic consumption / Low relevance
        # =========================================================================
        rules_fired.append("RULE_DOMESTIC_USE: Personal or domestic consumption without commercial sale or IPR.")
        return ABSAssessmentResult(
            relevance=ABSRelevance.NOT_APPLICABLE,
            nba_approval_required=False,
            sbb_intimation_required=False,
            governing_sections=["Biological Diversity Act 2002"],
            applicable_forms=[],
            benefit_sharing_estimate=None,
            ordered_next_steps=["No statutory ABS filing required for personal consumption or non-commercial domestic use."],
            exemptions_applicable=["Domestic personal use."],
            rules_fired=rules_fired,
        )


# Module-level convenience engine instance
default_abs_engine = ABSEngine()


def assess_abs(inputs: ABSAssessmentInput) -> ABSAssessmentResult:
    """Assess ABS obligations for a given biological resource access request."""
    return default_abs_engine.assess(inputs)
