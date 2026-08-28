import logging
from typing import Any

logger = logging.getLogger(__name__)


def assess_ip_relevance(product_id: str, ip_type: str) -> dict[str, Any]:
    """
    STUB — AI layer IP relevance assessment.

    Will be replaced by the AI layer's IP assessment logic once ready.
    The backend calls this and persists the result to IPAssessment.

    Returns:
        {
            "ip_type": str,
            "relevance_label": str,       # "High" | "Medium" | "Low" | "Not Applicable"
            "reasoning": str,
            "legal_provisions": [
                {"provision": str, "description": str, "jurisdiction": str}
            ]
        }
    """
    # Stubbed reasoning per IP type
    ip_assessments = {
        "patent": {
            "relevance_label": "High",
            "reasoning": "Ayurvedic formulations with novel processes or compositions may qualify for patent protection under the Patents Act, 1970. However, traditional knowledge documented in classical texts is excluded from patentability.",
            "legal_provisions": [
                {"provision": "Patents Act 1970, Section 3(p)", "description": "Excludes traditional knowledge from patentability", "jurisdiction": "India"},
                {"provision": "TRIPS Agreement, Article 27", "description": "Patentable subject matter requirements", "jurisdiction": "International"},
            ],
        },
        "trademark": {
            "relevance_label": "Medium",
            "reasoning": "Brand names and distinctive packaging for Ayurvedic products can be registered as trademarks. Generic Ayurvedic terms cannot be trademarked.",
            "legal_provisions": [
                {"provision": "Trade Marks Act 1999, Section 9", "description": "Absolute grounds for refusal", "jurisdiction": "India"},
            ],
        },
        "gi": {
            "relevance_label": "Medium",
            "reasoning": "Region-specific Ayurvedic preparations may qualify for Geographical Indication protection if they have a proven geographical origin link.",
            "legal_provisions": [
                {"provision": "GI Act 1999, Section 2(e)", "description": "Definition of geographical indication", "jurisdiction": "India"},
            ],
        },
        "trade secret": {
            "relevance_label": "Low",
            "reasoning": "Proprietary formulation processes that are not disclosed publicly may be protected as trade secrets.",
            "legal_provisions": [
                {"provision": "Indian Contract Act 1872, Section 27", "description": "Restraint of trade provisions", "jurisdiction": "India"},
            ],
        },
        "copyright": {
            "relevance_label": "Low",
            "reasoning": "Original literary works describing formulations (e.g. product monographs) can be copyrighted, but the formulation itself cannot.",
            "legal_provisions": [
                {"provision": "Copyright Act 1957, Section 13", "description": "Works in which copyright subsists", "jurisdiction": "India"},
            ],
        },
    }

    assessment = ip_assessments.get(ip_type.lower(), {
        "relevance_label": "Not Applicable",
        "reasoning": f"No assessment available for IP type: {ip_type}",
        "legal_provisions": [],
    })

    logger.info("STUB IP assessment: ip_type=%s, relevance=%s", ip_type, assessment["relevance_label"])

    return {
        "ip_type": ip_type,
        **assessment,
    }


def assess_abs_obligations(
    product_id: str,
    biological_resources: list[dict[str, Any]],
    origin: str | None,
    purpose: str | None,
) -> dict[str, Any]:
    """
    STUB — AI layer ABS (Access and Benefit Sharing) assessment.

    Will be replaced by the AI layer's ABS logic (ai/ T3.4) once ready.
    The backend calls this and persists the result to ABSAssessment.

    Returns:
        {
            "relevance_label": str,   # "Applicable" | "Likely Applicable" | "Not Applicable"
            "next_steps": [
                {"step": str, "description": str, "authority": str}
            ]
        }
    """
    has_resources = bool(biological_resources)

    if has_resources:
        relevance_label = "Applicable"
        next_steps = [
            {
                "step": "NBA Approval",
                "description": "Apply to the National Biodiversity Authority for approval before commercializing products using biological resources.",
                "authority": "National Biodiversity Authority (NBA)",
            },
            {
                "step": "SBB Intimation",
                "description": "Intimate the State Biodiversity Board about use of biological resources for commercial purposes.",
                "authority": "State Biodiversity Board (SBB)",
            },
            {
                "step": "Benefit Sharing Agreement",
                "description": "Negotiate and execute a benefit-sharing agreement as per the Biological Diversity Act, 2002.",
                "authority": "NBA / Local Biodiversity Management Committee",
            },
        ]
    else:
        relevance_label = "Not Applicable"
        next_steps = [
            {
                "step": "No ABS Obligations",
                "description": "No biological resources identified — ABS provisions do not apply.",
                "authority": "N/A",
            },
        ]

    logger.info("STUB ABS assessment: relevance=%s, steps=%d", relevance_label, len(next_steps))

    return {
        "relevance_label": relevance_label,
        "next_steps": next_steps,
    }
