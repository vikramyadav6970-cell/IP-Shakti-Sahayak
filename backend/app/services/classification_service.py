import logging
from typing import Any

logger = logging.getLogger(__name__)


def classify_product(
    product_type: str,
    derived_from_authoritative_text: bool,
    formulation_novelty: str,
    biological_resources_used: list[str],
) -> dict[str, Any]:
    """
    STUB — deterministic rules engine for product classification.

    This function will be replaced by the AI layer's rules engine
    (ai/prompts/phases.md Phase 3, T3.3) once it is ready. The backend
    calls this function and persists the result; it never embeds
    classification logic of its own.

    Returns:
        {
            "category": str,           # e.g. "Classical Medicine", "Proprietary Medicine", …
            "regulatory_pathway": str,  # e.g. "Schedule E1 — Classical", "Rule 158-B", …
            "rules_fired": [           # audit trail — every rule evaluated
                {"rule": str, "input": str, "result": str},
                ...
            ]
        }
    """
    rules_fired: list[dict[str, Any]] = []

    # ── Rule 1: Authoritative text check ──
    if derived_from_authoritative_text:
        category = "Classical Medicine"
        regulatory_pathway = "Schedule E1 — Classical Ayurvedic Medicine"
        rules_fired.append({
            "rule": "AUTHORITATIVE_TEXT_CHECK",
            "input": "derived_from_authoritative_text=True",
            "result": "Classified as Classical Medicine",
        })
    else:
        category = "Proprietary Medicine"
        regulatory_pathway = "Rule 158-B — Proprietary Ayurvedic Medicine"
        rules_fired.append({
            "rule": "AUTHORITATIVE_TEXT_CHECK",
            "input": "derived_from_authoritative_text=False",
            "result": "Classified as Proprietary Medicine",
        })

    # ── Rule 2: Formulation novelty override ──
    if formulation_novelty.lower() in ("novel", "new"):
        category = "New Drug"
        regulatory_pathway = "Rule 122-E — New Drug Application"
        rules_fired.append({
            "rule": "FORMULATION_NOVELTY_OVERRIDE",
            "input": f"formulation_novelty={formulation_novelty}",
            "result": "Overridden to New Drug",
        })
    else:
        rules_fired.append({
            "rule": "FORMULATION_NOVELTY_OVERRIDE",
            "input": f"formulation_novelty={formulation_novelty}",
            "result": "No override applied",
        })

    # ── Rule 3: Product type refinement ──
    product_type_lower = product_type.lower()
    if product_type_lower == "cosmetic":
        category = "Cosmetic"
        regulatory_pathway = "Drugs & Cosmetics Act — Cosmetic Rules"
        rules_fired.append({
            "rule": "PRODUCT_TYPE_REFINEMENT",
            "input": f"product_type={product_type}",
            "result": "Reclassified as Cosmetic",
        })
    elif product_type_lower == "food" or product_type_lower == "ayurveda-aahara":
        category = "Ayurveda-Aahara"
        regulatory_pathway = "FSSAI — Ayurveda Aahara Regulations"
        rules_fired.append({
            "rule": "PRODUCT_TYPE_REFINEMENT",
            "input": f"product_type={product_type}",
            "result": "Reclassified as Ayurveda-Aahara",
        })
    elif product_type_lower == "phytopharmaceutical":
        category = "Phytopharmaceutical"
        regulatory_pathway = "Rule 122-DAB — Phytopharmaceutical Drug"
        rules_fired.append({
            "rule": "PRODUCT_TYPE_REFINEMENT",
            "input": f"product_type={product_type}",
            "result": "Reclassified as Phytopharmaceutical",
        })
    else:
        rules_fired.append({
            "rule": "PRODUCT_TYPE_REFINEMENT",
            "input": f"product_type={product_type}",
            "result": "No product-type reclassification",
        })

    # ── Rule 4: Biological resources flag ──
    if biological_resources_used:
        rules_fired.append({
            "rule": "BIOLOGICAL_RESOURCES_FLAG",
            "input": f"biological_resources_used={biological_resources_used}",
            "result": "ABS assessment recommended",
        })
    else:
        rules_fired.append({
            "rule": "BIOLOGICAL_RESOURCES_FLAG",
            "input": "biological_resources_used=[]",
            "result": "No ABS flag",
        })

    logger.info(
        "STUB classification: category=%s, pathway=%s, rules=%d",
        category,
        regulatory_pathway,
        len(rules_fired),
    )

    return {
        "category": category,
        "regulatory_pathway": regulatory_pathway,
        "rules_fired": rules_fired,
    }
