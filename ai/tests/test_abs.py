"""Unit tests for the Access & Benefit Sharing (ABS) assessment engine."""

import pytest

from src.abs.abs_engine import (
    ABSRelevance,
    ApplicantType,
    AccessPurpose,
    ABSAssessmentInput,
    ABSAssessmentResult,
    ABSEngine,
    assess_abs,
)


def test_abs_section_6_ipr_application():
    """Applying for IPR based on Indian biological resources requires mandatory NBA Form III prior approval."""
    inp = ABSAssessmentInput(
        biological_resources=["Withania somnifera", "Curcuma longa"],
        origin_country="INDIA",
        applicant_type=ApplicantType.INDIAN_ENTITY_OR_CITIZEN,
        intending_to_apply_for_ipr=True,
    )
    res = assess_abs(inp)

    assert res.relevance == ABSRelevance.HIGH
    assert res.nba_approval_required is True
    assert any("Form III" in f for f in res.applicable_forms)
    assert any("Section 6(1)" in sec for sec in res.governing_sections)
    assert any("RULE_SECTION_6_IPR_MANDATE" in r for r in res.rules_fired)


def test_abs_section_3_foreign_applicant():
    """Foreign citizen / non-Indian corporate accessing Indian biological resources requires NBA Form I."""
    inp = ABSAssessmentInput(
        biological_resources=["Ocimum sanctum"],
        origin_country="INDIA",
        applicant_type=ApplicantType.NON_INDIAN_OR_FOREIGN_CONTROLLED,
        access_purpose=AccessPurpose.COMMERCIAL_UTILIZATION,
    )
    res = assess_abs(inp)

    assert res.relevance == ABSRelevance.HIGH
    assert res.nba_approval_required is True
    assert any("Form I" in f for f in res.applicable_forms)
    assert any("Section 3" in sec for sec in res.governing_sections)


def test_abs_section_4_transfer_research_results():
    """Transfer of research results to foreign collaborators requires NBA Form II."""
    inp = ABSAssessmentInput(
        biological_resources=["Bacopa monnieri"],
        origin_country="INDIA",
        applicant_type=ApplicantType.INDIAN_ENTITY_OR_CITIZEN,
        access_purpose=AccessPurpose.TRANSFER_OF_RESEARCH_RESULTS,
        foreign_collaboration_or_transfer=True,
    )
    res = assess_abs(inp)

    assert res.relevance == ABSRelevance.HIGH
    assert res.nba_approval_required is True
    assert any("Form II" in f for f in res.applicable_forms)
    assert any("Section 4" in sec for sec in res.governing_sections)


def test_abs_section_7_indian_commercial_manufacturer():
    """Indian commercial entity using Indian wild biological resources requires State Biodiversity Board intimation."""
    inp = ABSAssessmentInput(
        biological_resources=["Terminalia chebula", "Terminalia bellirica", "Emblica officinalis"],
        origin_country="INDIA",
        applicant_type=ApplicantType.INDIAN_ENTITY_OR_CITIZEN,
        access_purpose=AccessPurpose.COMMERCIAL_UTILIZATION,
        is_cultivated_source=False,
    )
    res = assess_abs(inp)

    assert res.relevance == ABSRelevance.MEDIUM
    assert res.nba_approval_required is False
    assert res.sbb_intimation_required is True
    assert any("State Biodiversity Board" in f for f in res.applicable_forms)


def test_abs_ayush_practitioner_2023_amendment_exemption():
    """Registered AYUSH practitioners practicing indigenous medicine are exempt under 2023 Amendment."""
    inp = ABSAssessmentInput(
        biological_resources=["Withania somnifera"],
        origin_country="INDIA",
        applicant_type=ApplicantType.REGISTERED_AYUSH_PRACTITIONER,
        access_purpose=AccessPurpose.COMMERCIAL_UTILIZATION,
    )
    res = assess_abs(inp)

    assert res.relevance == ABSRelevance.NOT_APPLICABLE
    assert res.nba_approval_required is False
    assert res.sbb_intimation_required is False
    assert any("2023 Amendment" in ex for ex in res.exemptions_applicable)


def test_abs_ntac_section_40_commodity_exemption():
    """Commercial trading of commodities notified under Section 40 NTAC list is exempt."""
    inp = ABSAssessmentInput(
        biological_resources=["Piper nigrum (Black pepper)"],
        origin_country="INDIA",
        applicant_type=ApplicantType.INDIAN_ENTITY_OR_CITIZEN,
        access_purpose=AccessPurpose.COMMERCIAL_UTILIZATION,
        is_normally_traded_commodity=True,
    )
    res = assess_abs(inp)

    assert res.relevance == ABSRelevance.NOT_APPLICABLE
    assert res.nba_approval_required is False
    assert any("Section 40" in ex for ex in res.exemptions_applicable)


def test_abs_non_indian_biological_resource():
    """Biological resources originating outside India are not governed by Indian BDA 2002."""
    inp = ABSAssessmentInput(
        biological_resources=["Panax ginseng"],
        origin_country="KOREA",
        applicant_type=ApplicantType.INDIAN_ENTITY_OR_CITIZEN,
        access_purpose=AccessPurpose.COMMERCIAL_UTILIZATION,
    )
    res = assess_abs(inp)

    assert res.relevance == ABSRelevance.NOT_APPLICABLE
    assert res.nba_approval_required is False
