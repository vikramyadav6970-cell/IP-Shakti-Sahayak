"""Context gathering agent.

Generates structured, domain-specific follow-up questions based on the user-selected
DomainIntent (BUSINESS, EXPORT, MEDICINAL, PATENT, RESEARCH, OTHER) and parses user
answers into strictly typed ContextObject instances for entity extraction & RAG.

Templates are loaded from versioned YAML files at startup (Rule 14).
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Sequence, Union
import logging
import yaml

from src.classification.intent_classifier import DomainIntent

logger = logging.getLogger(__name__)


class AnswerType(str, Enum):
    """Supported input UI answer types for context gathering questions."""

    FREE_TEXT = "FREE_TEXT"
    SINGLE_SELECT = "SINGLE_SELECT"
    MULTI_SELECT = "MULTI_SELECT"


@dataclass
class ContextQuestion:
    """Represents a structured follow-up question presented to the user."""

    question_id: str
    question_text: str
    answer_type: AnswerType
    options: Optional[List[str]] = None
    required: bool = True
    placeholder: Optional[str] = None
    help_text: Optional[str] = None


# =========================================================================
# Typed ContextObject Schemas per Domain Intent
# =========================================================================

@dataclass
class ExportContextObject:
    """Structured context for EXPORT intent."""

    herbs: List[str]
    destination: str
    purpose: Literal["COMMERCIAL", "RESEARCH"]
    nba_approached: bool
    already_in_market: bool
    domain_intent: DomainIntent = DomainIntent.EXPORT
    raw_answers: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PatentContextObject:
    """Structured context for PATENT intent."""

    novel_aspect: str
    type: Literal["HERB", "FORMULATION", "PROCESS"]
    prior_art_search_needed: bool
    uses_biological_resources: bool
    domain_intent: DomainIntent = DomainIntent.PATENT
    raw_answers: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MedicinalContextObject:
    """Structured context for MEDICINAL intent."""

    formulation_type: Literal["CLASSICAL", "PROPRIETARY", "UNKNOWN"]
    from_authoritative_text: bool
    new_ingredients: List[str]
    domain_intent: DomainIntent = DomainIntent.MEDICINAL
    raw_answers: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BusinessContextObject:
    """Structured context for BUSINESS intent."""

    product_type: str
    brand_name: Optional[str]
    target_market: Literal["INDIA", "INTERNATIONAL", "BOTH"]
    domain_intent: DomainIntent = DomainIntent.BUSINESS
    raw_answers: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearchContextObject:
    """Structured context for RESEARCH intent."""

    research_type: Literal["CLINICAL", "PHYTOCHEMICAL", "IP"]
    biological_resources: bool
    publish_internationally: bool
    domain_intent: DomainIntent = DomainIntent.RESEARCH
    raw_answers: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OtherContextObject:
    """Structured context for OTHER intent."""

    free_description: str
    domain_intent: DomainIntent = DomainIntent.OTHER
    raw_answers: Dict[str, Any] = field(default_factory=dict)


ContextObject = Union[
    ExportContextObject,
    PatentContextObject,
    MedicinalContextObject,
    BusinessContextObject,
    ResearchContextObject,
    OtherContextObject,
]


class ContextGatheringAgent:
    """Loads versioned question templates at startup and parses answers into typed schemas."""

    def __init__(self, templates_dir: Optional[Union[str, Path]] = None):
        if templates_dir is not None:
            self.templates_dir = Path(templates_dir)
        else:
            self.templates_dir = Path(__file__).parent.parent / "prompts" / "context_questions"

        self.questions_by_intent: Dict[DomainIntent, List[ContextQuestion]] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load all versioned YAML question templates at startup."""
        for intent in DomainIntent:
            yaml_path = self.templates_dir / f"{intent.value}.yaml"
            if not yaml_path.exists():
                logger.warning("Context question template missing for intent %s at: %s", intent.value, yaml_path)
                continue

            try:
                with open(yaml_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                raw_questions = data.get("questions", [])
                parsed_questions: List[ContextQuestion] = []

                for q in raw_questions:
                    parsed_questions.append(
                        ContextQuestion(
                            question_id=q["question_id"],
                            question_text=q["question_text"],
                            answer_type=AnswerType(q["answer_type"]),
                            options=q.get("options"),
                            required=q.get("required", True),
                            placeholder=q.get("placeholder"),
                            help_text=q.get("help_text"),
                        )
                    )

                self.questions_by_intent[intent] = parsed_questions
                logger.debug("Loaded %d context questions for intent %s", len(parsed_questions), intent.value)
            except Exception as e:
                logger.error("Failed to load context question template '%s': %s", yaml_path, e)

    def get_questions(self, domain_intent: Union[DomainIntent, str]) -> List[ContextQuestion]:
        """Retrieve pre-configured context questions for a given domain intent."""
        intent = self._normalize_intent(domain_intent)
        return self.questions_by_intent.get(intent, self.questions_by_intent.get(DomainIntent.OTHER, []))

    def parse_answers(
        self,
        domain_intent: Union[DomainIntent, str],
        raw_answers: Dict[str, Any],
    ) -> ContextObject:
        """Parse raw answer dictionary into the corresponding typed ContextObject."""
        intent = self._normalize_intent(domain_intent)

        if intent == DomainIntent.EXPORT:
            return self._parse_export(raw_answers)
        elif intent == DomainIntent.PATENT:
            return self._parse_patent(raw_answers)
        elif intent == DomainIntent.MEDICINAL:
            return self._parse_medicinal(raw_answers)
        elif intent == DomainIntent.BUSINESS:
            return self._parse_business(raw_answers)
        elif intent == DomainIntent.RESEARCH:
            return self._parse_research(raw_answers)
        else:
            return self._parse_other(raw_answers)

    def _parse_export(self, a: Dict[str, Any]) -> ExportContextObject:
        raw_herbs = a.get("herbs", "")
        if isinstance(raw_herbs, list):
            herbs = raw_herbs
        else:
            herbs = [h.strip() for h in str(raw_herbs).split(",") if h.strip()]

        destination = str(a.get("destination", "European Union (EU)"))
        purpose_raw = str(a.get("purpose", "COMMERCIAL")).upper()
        purpose: Literal["COMMERCIAL", "RESEARCH"] = "RESEARCH" if "RESEARCH" in purpose_raw else "COMMERCIAL"

        nba_approached = self._to_bool(a.get("nba_approached"))
        already_in_market = self._to_bool(a.get("already_in_market"))

        return ExportContextObject(
            herbs=herbs,
            destination=destination,
            purpose=purpose,
            nba_approached=nba_approached,
            already_in_market=already_in_market,
            raw_answers=a,
        )

    def _parse_patent(self, a: Dict[str, Any]) -> PatentContextObject:
        novel_aspect = str(a.get("novel_aspect", ""))
        type_raw = str(a.get("type", "PROCESS")).upper()
        p_type: Literal["HERB", "FORMULATION", "PROCESS"] = "PROCESS"
        if "HERB" in type_raw:
            p_type = "HERB"
        elif "FORMULATION" in type_raw:
            p_type = "FORMULATION"

        prior_art_needed = self._to_bool(a.get("prior_art_search_needed", True))
        uses_bio = self._to_bool(a.get("uses_biological_resources", True))

        return PatentContextObject(
            novel_aspect=novel_aspect,
            type=p_type,
            prior_art_search_needed=prior_art_needed,
            uses_biological_resources=uses_bio,
            raw_answers=a,
        )

    def _parse_medicinal(self, a: Dict[str, Any]) -> MedicinalContextObject:
        f_type_raw = str(a.get("formulation_type", "CLASSICAL")).upper()
        f_type: Literal["CLASSICAL", "PROPRIETARY", "UNKNOWN"] = "CLASSICAL"
        if "PROPRIETARY" in f_type_raw:
            f_type = "PROPRIETARY"
        elif "UNKNOWN" in f_type_raw:
            f_type = "UNKNOWN"

        from_text = self._to_bool(a.get("from_authoritative_text", True))
        raw_new = a.get("new_ingredients", [])
        if isinstance(raw_new, list):
            new_ings = raw_new
        else:
            new_ings = [i.strip() for i in str(raw_new).split(",") if i.strip() and i.lower() != "none"]

        return MedicinalContextObject(
            formulation_type=f_type,
            from_authoritative_text=from_text,
            new_ingredients=new_ings,
            raw_answers=a,
        )

    def _parse_business(self, a: Dict[str, Any]) -> BusinessContextObject:
        product_type = str(a.get("product_type", "Ayurvedic Product"))
        brand_name = a.get("brand_name")
        market_raw = str(a.get("target_market", "INDIA")).upper()
        market: Literal["INDIA", "INTERNATIONAL", "BOTH"] = "INDIA"
        if "BOTH" in market_raw:
            market = "BOTH"
        elif "INTERNATIONAL" in market_raw:
            market = "INTERNATIONAL"

        return BusinessContextObject(
            product_type=product_type,
            brand_name=str(brand_name) if brand_name else None,
            target_market=market,
            raw_answers=a,
        )

    def _parse_research(self, a: Dict[str, Any]) -> ResearchContextObject:
        r_type_raw = str(a.get("research_type", "CLINICAL")).upper()
        r_type: Literal["CLINICAL", "PHYTOCHEMICAL", "IP"] = "CLINICAL"
        if "PHYTOCHEMICAL" in r_type_raw:
            r_type = "PHYTOCHEMICAL"
        elif "IP" in r_type_raw:
            r_type = "IP"

        bio = self._to_bool(a.get("biological_resources", True))
        pub = self._to_bool(a.get("publish_internationally", False))

        return ResearchContextObject(
            research_type=r_type,
            biological_resources=bio,
            publish_internationally=pub,
            raw_answers=a,
        )

    def _parse_other(self, a: Dict[str, Any]) -> OtherContextObject:
        free_desc = str(a.get("free_description", a.get("query", "")))
        return OtherContextObject(
            free_description=free_desc,
            raw_answers=a,
        )

    def _normalize_intent(self, domain_intent: Union[DomainIntent, str]) -> DomainIntent:
        if isinstance(domain_intent, DomainIntent):
            return domain_intent
        try:
            return DomainIntent(str(domain_intent).upper().strip())
        except ValueError:
            return DomainIntent.OTHER

    @staticmethod
    def _to_bool(val: Any) -> bool:
        """Helper to convert yes/no/true/false to bool."""
        if isinstance(val, bool):
            return val
        s = str(val).lower().strip()
        return s in ["true", "yes", "1", "y", "licensed asu drug", "fssai ayurveda aahara / food", "ayush cosmetic"]


# Module-level default agent instance
default_context_agent = ContextGatheringAgent()


def get_context_questions(domain_intent: Union[DomainIntent, str]) -> List[ContextQuestion]:
    """Retrieve context questions for a given domain intent."""
    return default_context_agent.get_questions(domain_intent)


def parse_context_answers(
    domain_intent: Union[DomainIntent, str],
    raw_answers: Dict[str, Any],
) -> ContextObject:
    """Parse raw answer dictionary into typed ContextObject."""
    return default_context_agent.parse_answers(domain_intent, raw_answers)
