"""Two-level intent classifier and collection routing.

Encodes coding_conventions.md Rule 11 & Rule 14:
- Level 1: UI Domain Intent (BUSINESS | EXPORT | MEDICINAL | PATENT | RESEARCH | OTHER)
- Level 2: Fine-grained intent(s) inferred from query text (PATENT, TRADEMARK, ABS, etc.)
- Maps fine-grained intents directly to target Qdrant collections.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Union
import logging
import re

from src.reasoning.llm_provider import LLMProvider, get_llm_provider

logger = logging.getLogger(__name__)


class DomainIntent(str, Enum):
    """Level 1 — User-selected domain intent from the frontend."""

    BUSINESS = "BUSINESS"
    EXPORT = "EXPORT"
    MEDICINAL = "MEDICINAL"
    PATENT = "PATENT"
    RESEARCH = "RESEARCH"
    OTHER = "OTHER"


class FineGrainedIntent(str, Enum):
    """Level 2 — Specific legal/regulatory domain intent."""

    PATENT = "PATENT"
    TRADEMARK = "TRADEMARK"
    GI = "GI"
    COPYRIGHT = "COPYRIGHT"
    DESIGN = "DESIGN"
    PLANT_VARIETY = "PLANT_VARIETY"
    TRADE_SECRET = "TRADE_SECRET"
    ABS = "ABS"
    TKDL = "TKDL"
    PRODUCT_CLASSIFICATION = "PRODUCT_CLASSIFICATION"
    DRUG_REGULATION = "DRUG_REGULATION"
    FOOD_REGULATION = "FOOD_REGULATION"
    COSMETIC = "COSMETIC"
    EXPORT = "EXPORT"
    INTERNATIONAL_IP = "INTERNATIONAL_IP"
    GENERAL = "GENERAL"


# Authoritative mapping from fine-grained intent to Qdrant collections (Rule 11)
INTENT_TO_COLLECTIONS_MAP: Dict[FineGrainedIntent, List[str]] = {
    FineGrainedIntent.PATENT: ["legal_statutory", "standards_formulations", "case_law_prior_art"],
    FineGrainedIntent.TKDL: ["legal_statutory", "standards_formulations", "case_law_prior_art"],
    FineGrainedIntent.PLANT_VARIETY: ["legal_statutory", "standards_formulations", "case_law_prior_art"],
    FineGrainedIntent.TRADEMARK: ["legal_statutory", "standards_formulations"],
    FineGrainedIntent.GI: ["legal_statutory", "standards_formulations"],
    FineGrainedIntent.COPYRIGHT: ["legal_statutory", "standards_formulations"],
    FineGrainedIntent.DESIGN: ["legal_statutory", "standards_formulations"],
    FineGrainedIntent.TRADE_SECRET: ["legal_statutory", "standards_formulations"],
    FineGrainedIntent.ABS: ["legal_statutory", "procedural_forms", "standards_formulations"],
    FineGrainedIntent.PRODUCT_CLASSIFICATION: ["legal_statutory", "standards_formulations", "procedural_forms"],
    FineGrainedIntent.DRUG_REGULATION: ["legal_statutory", "standards_formulations", "procedural_forms"],
    FineGrainedIntent.FOOD_REGULATION: ["legal_statutory", "standards_formulations", "procedural_forms"],
    FineGrainedIntent.COSMETIC: ["legal_statutory", "standards_formulations", "procedural_forms"],
    FineGrainedIntent.EXPORT: ["international_export", "legal_statutory", "standards_formulations"],
    FineGrainedIntent.INTERNATIONAL_IP: ["international_export", "legal_statutory", "standards_formulations"],
    FineGrainedIntent.GENERAL: [
        "legal_statutory",
        "standards_formulations",
        "procedural_forms",
        "international_export",
    ],
}

# Domain Intent defaults when text does not specify sub-intents
DOMAIN_TO_DEFAULT_INTENTS: Dict[DomainIntent, List[FineGrainedIntent]] = {
    DomainIntent.BUSINESS: [FineGrainedIntent.TRADEMARK, FineGrainedIntent.GI, FineGrainedIntent.DESIGN],
    DomainIntent.EXPORT: [FineGrainedIntent.EXPORT, FineGrainedIntent.ABS, FineGrainedIntent.INTERNATIONAL_IP],
    DomainIntent.MEDICINAL: [
        FineGrainedIntent.DRUG_REGULATION,
        FineGrainedIntent.FOOD_REGULATION,
        FineGrainedIntent.PRODUCT_CLASSIFICATION,
    ],
    DomainIntent.PATENT: [FineGrainedIntent.PATENT, FineGrainedIntent.TKDL],
    DomainIntent.RESEARCH: [FineGrainedIntent.ABS, FineGrainedIntent.PATENT, FineGrainedIntent.INTERNATIONAL_IP],
    DomainIntent.OTHER: [FineGrainedIntent.GENERAL],
}


@dataclass
class IntentClassificationResult:
    """Represents the resolved two-level intent and collection routing."""

    domain_intent: DomainIntent
    fine_grained_intents: List[FineGrainedIntent]
    target_collections: List[str]
    confidence: float = 1.0
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class IntentClassifier:
    """Classifies Level 1 UI intent and infers Level 2 fine-grained legal intents."""

    # Keyword rules for Level 2 intent detection
    INTENT_KEYWORDS: Dict[FineGrainedIntent, List[str]] = {
        FineGrainedIntent.PATENT: [
            r"\bpatent\b", r"\bpatents\b", r"\bsection 3\(p\)\b", r"\bsection 3\(d\)\b",
            r"\bsection 3\(e\)\b", r"\binvention\b", r"\binventive step\b", r"\bprior art\b",
            r"\bnovelty\b", r"\bsynergistic\b", r"\bprovisional specification\b",
        ],
        FineGrainedIntent.TKDL: [
            r"\btkdl\b", r"\btraditional knowledge digital library\b", r"\bcsir\b",
            r"\bclassical prior art\b", r"\bbiopiracy\b",
        ],
        FineGrainedIntent.TRADEMARK: [
            r"\btrademark\b", r"\btrade mark\b", r"\bbrand name\b", r"\blogo\b",
            r"\bclass 5\b", r"\bclass 3\b", r"\bclass 30\b", r"\binfringement\b",
        ],
        FineGrainedIntent.GI: [
            r"\bgeographical indication\b", r"\bgi tag\b", r"\bgi act\b", r"\bappellation of origin\b",
        ],
        FineGrainedIntent.DESIGN: [
            r"\bdesign\b", r"\bpackaging\b", r"\bbottle shape\b", r"\bcontainer design\b",
        ],
        FineGrainedIntent.COPYRIGHT: [
            r"\bcopyright\b", r"\blabel text\b", r"\bliterary work\b",
        ],
        FineGrainedIntent.PLANT_VARIETY: [
            r"\bplant variety\b", r"\bppv&fr\b", r"\bppvfr\b", r"\bfarmers rights\b", r"\bnew variety\b",
        ],
        FineGrainedIntent.ABS: [
            r"\babs\b", r"\bnba\b", r"\bnational biodiversity authority\b", r"\bbda\b",
            r"\bbiological diversity\b", r"\bbenefit sharing\b", r"\bform i\b", r"\bform iii\b",
            r"\bsbb\b", r"\bstate biodiversity board\b", r"\baccess to biological resources\b",
        ],
        FineGrainedIntent.DRUG_REGULATION: [
            r"\bdrug\b", r"\bdrugs and cosmetics act\b", r"\basu\b", r"\bayurvedic drug\b",
            r"\bform 24d\b", r"\bform 24e\b", r"\bmanufacturing license\b", r"\bschedule t\b",
            r"\bclassical medicine\b", r"\bproprietary medicine\b", r"\brule 158b\b",
        ],
        FineGrainedIntent.FOOD_REGULATION: [
            r"\bfssai\b", r"\bayurveda aahara\b", r"\bfood supplement\b", r"\bdietary supplement\b",
            r"\bfunctional food\b", r"\bnutraceutical\b",
        ],
        FineGrainedIntent.COSMETIC: [
            r"\bcosmetic\b", r"\bskincare\b", r"\bshampoo\b", r"\bherbal cosmetic\b",
        ],
        FineGrainedIntent.PRODUCT_CLASSIFICATION: [
            r"\bclassification\b", r"\bfood or drug\b", r"\bcategory\b", r"\bhow to classify\b",
            r"\bis it a medicine\b", r"\bis it a food\b",
        ],
        FineGrainedIntent.EXPORT: [
            r"\bexport\b", r"\bexporting\b", r"\bship to\b", r"\beu thmpd\b", r"\bus fda\b",
            r"\bdshea\b", r"\bcites\b", r"\bcustoms\b", r"\bexim\b",
        ],
        FineGrainedIntent.INTERNATIONAL_IP: [
            r"\btrips\b", r"\bwto\b", r"\bcbd\b", r"\bnagoya\b", r"\bwipo\b", r"\bgratk\b",
        ],
    }

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.llm_provider = llm_provider

    def classify(
        self,
        question: str,
        ui_domain_intent: Optional[Union[DomainIntent, str]] = None,
    ) -> IntentClassificationResult:
        """Classify user question into Level 1 DomainIntent and Level 2 FineGrainedIntents.

        Args:
            question: User question / input text.
            ui_domain_intent: Optional explicit UI selection (DomainIntent enum or string).

        Returns:
            IntentClassificationResult containing domain intent, fine-grained intents,
            and resolved target Qdrant collections.
        """
        # Resolve Level 1 DomainIntent
        domain_intent = self._resolve_domain_intent(question, ui_domain_intent)

        # Resolve Level 2 Fine-Grained Intents via keyword matching
        detected_fine_grained = self._detect_fine_grained_intents(question)

        # Merge with domain defaults if no specific keywords matched
        if not detected_fine_grained:
            final_fine_grained = DOMAIN_TO_DEFAULT_INTENTS.get(domain_intent, [FineGrainedIntent.GENERAL])
        else:
            # Add domain default if not overlapping
            domain_defaults = DOMAIN_TO_DEFAULT_INTENTS.get(domain_intent, [])
            final_fine_grained = list(dict.fromkeys(detected_fine_grained + domain_defaults))

        # Map to target collections
        target_collections = self._resolve_collections(final_fine_grained)

        reasoning = f"Domain intent: {domain_intent.value}; Inferred sub-intents: {[i.value for i in final_fine_grained]}"

        return IntentClassificationResult(
            domain_intent=domain_intent,
            fine_grained_intents=final_fine_grained,
            target_collections=target_collections,
            confidence=0.95 if detected_fine_grained else 0.80,
            reasoning=reasoning,
        )

    def _resolve_domain_intent(
        self,
        question: str,
        ui_intent: Optional[Union[DomainIntent, str]],
    ) -> DomainIntent:
        """Resolve Level 1 Domain Intent (honors UI selection directly if provided)."""
        if ui_intent:
            if isinstance(ui_intent, DomainIntent):
                return ui_intent
            ui_str = str(ui_intent).upper().strip()
            for val in DomainIntent:
                if val.value == ui_str:
                    return val

        # If no UI selection provided (or OTHER), infer from question keywords
        text = question.lower()
        if any(w in text for w in ["patent", "invent", "novel", "section 3", "prior art"]):
            return DomainIntent.PATENT
        if any(w in text for w in ["export", "ship", "customs", "fda", "thmpd", "eu", "usa"]):
            return DomainIntent.EXPORT
        if any(w in text for w in ["drug", "food", "fssai", "medicine", "syrup", "churna", "license"]):
            return DomainIntent.MEDICINAL
        if any(w in text for w in ["brand", "trademark", "gi", "logo", "business", "sell"]):
            return DomainIntent.BUSINESS
        if any(w in text for w in ["research", "abs", "nba", "biodiversity", "university"]):
            return DomainIntent.RESEARCH

        return DomainIntent.OTHER

    def _detect_fine_grained_intents(self, text: str) -> List[FineGrainedIntent]:
        """Detect fine-grained intents from text using regex patterns."""
        detected: List[FineGrainedIntent] = []
        for intent, patterns in self.INTENT_KEYWORDS.items():
            for p in patterns:
                if re.search(p, text, re.IGNORECASE):
                    detected.append(intent)
                    break
        return detected

    def _resolve_collections(self, intents: Sequence[FineGrainedIntent]) -> List[str]:
        """Resolve and deduplicate target collections for a sequence of fine-grained intents."""
        collections: List[str] = []
        for intent in intents:
            cols = INTENT_TO_COLLECTIONS_MAP.get(intent, ["legal_statutory", "standards_formulations"])
            for col in cols:
                if col not in collections:
                    collections.append(col)
        return collections if collections else ["legal_statutory", "standards_formulations"]


# Module-level convenience classifier
default_intent_classifier = IntentClassifier()


def classify_intent(
    question: str,
    ui_domain_intent: Optional[Union[DomainIntent, str]] = None,
) -> IntentClassificationResult:
    """Classify intent and resolve collection routing for a question."""
    return default_intent_classifier.classify(question, ui_domain_intent)
