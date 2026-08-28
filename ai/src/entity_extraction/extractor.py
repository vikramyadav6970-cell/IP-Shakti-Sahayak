"""Entity Extractor module.

Extracts structured EntitySet (botanical herbs, jurisdictions, IP types, biological resources,
formulation names, destinations, and regulatory regimes) from user questions and ContextObjects.
Input to the query decomposer and parallel multi-collection RAG pipeline (T4.1).
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union
import logging
import re
import yaml

from src.context_gathering.agent import (
    ContextObject,
    ExportContextObject,
    PatentContextObject,
    MedicinalContextObject,
    BusinessContextObject,
    ResearchContextObject,
    OtherContextObject,
)

logger = logging.getLogger(__name__)


class IPType(str, Enum):
    """Intellectual Property and Regulatory Types."""

    PATENT = "PATENT"
    TRADEMARK = "TRADEMARK"
    GI = "GI"
    COPYRIGHT = "COPYRIGHT"
    DESIGN = "DESIGN"
    PLANT_VARIETY = "PLANT_VARIETY"
    ABS = "ABS"
    EXPORT = "EXPORT"
    DRUG_REGULATION = "DRUG_REGULATION"
    FOOD_REGULATION = "FOOD_REGULATION"
    COSMETIC = "COSMETIC"
    GENERAL = "GENERAL"


@dataclass
class EntitySet:
    """Structured entity container consumed by Query Decomposer and RAG retriever."""

    herbs: List[str]  # Official botanical Latin names where resolved (e.g. "Withania somnifera")
    jurisdictions: List[str]  # e.g. ["INDIA", "EU"]
    ip_types: List[IPType]  # e.g. [IPType.PATENT, IPType.ABS]
    biological_resources: List[str] = field(default_factory=list)
    formulation_name: Optional[str] = None
    destination_country: Optional[str] = None
    regulatory_regime: Optional[str] = None
    raw_entities: Dict[str, Any] = field(default_factory=dict)


class EntityExtractor:
    """Extracts and resolves canonical botanical and legal entities."""

    # Canonical jurisdiction map
    JURISDICTION_MAP: Dict[str, str] = {
        "eu": "EU",
        "european union": "EU",
        "europe": "EU",
        "germany": "EU",
        "france": "EU",
        "italy": "EU",
        "spain": "EU",
        "netherlands": "EU",
        "us": "USA",
        "usa": "USA",
        "u.s.": "USA",
        "united states": "USA",
        "america": "USA",
        "uk": "UK",
        "united kingdom": "UK",
        "great britain": "UK",
        "india": "INDIA",
        "bharat": "INDIA",
        "international": "INTERNATIONAL",
        "wto": "INTERNATIONAL",
        "wipo": "INTERNATIONAL",
        "cbd": "INTERNATIONAL",
    }

    # IP Type keyword regex triggers
    IP_PATTERNS: Dict[IPType, List[str]] = {
        IPType.PATENT: [
            r"\bpatent\b", r"\bpatents\b", r"\bsection 3\(p\)\b", r"\bsection 3\(d\)\b",
            r"\bsection 3\(e\)\b", r"\bsection 10\(4\)\b", r"\binvention\b", r"\bprior art\b",
            r"\btkdl\b", r"\bclaims\b", r"\bspecification\b",
        ],
        IPType.TRADEMARK: [
            r"\btrademark\b", r"\btrade mark\b", r"\bbrand\b", r"\bbrand name\b",
            r"\blogo\b", r"\bclass 5\b", r"\bclass 3\b", r"\bclass 30\b",
        ],
        IPType.GI: [
            r"\bgi\b", r"\bgeographical indication\b", r"\bgi tag\b", r"\bappellation\b",
        ],
        IPType.DESIGN: [
            r"\bdesign\b", r"\bpackaging\b", r"\bbottle\b", r"\bcontainer\b",
        ],
        IPType.ABS: [
            r"\babs\b", r"\bnba\b", r"\bnational biodiversity authority\b", r"\bbda\b",
            r"\bbiological diversity\b", r"\bbenefit sharing\b", r"\bform i\b", r"\bform ii\b",
            r"\bform iii\b", r"\bform iv\b", r"\bsbb\b", r"\bstate biodiversity board\b",
        ],
        IPType.EXPORT: [
            r"\bexport\b", r"\bexporting\b", r"\bship to\b", r"\beu thmpd\b", r"\bus fda\b",
            r"\bdshea\b", r"\bcites\b", r"\bcustoms\b",
        ],
        IPType.DRUG_REGULATION: [
            r"\bdrug\b", r"\basu\b", r"\bform 24d\b", r"\bform 24e\b", r"\bmanufacturing license\b",
            r"\bclassical\b", r"\bproprietary\b", r"\brule 158b\b",
        ],
        IPType.FOOD_REGULATION: [
            r"\bfssai\b", r"\bayurveda aahara\b", r"\bfood\b", r"\bdietary supplement\b", r"\bnutraceutical\b",
        ],
    }

    def __init__(self, herb_table_path: Optional[Union[str, Path]] = None):
        if herb_table_path is not None:
            self.herb_table_path = Path(herb_table_path)
        else:
            self.herb_table_path = Path(__file__).parent.parent.parent / "data" / "herb_names.yaml"

        self.herb_lookup: Dict[str, str] = {}  # synonym/common name -> botanical name
        self._load_herb_table()

    def _load_herb_table(self) -> None:
        """Load curated botanical herb name mappings."""
        if not self.herb_table_path.exists():
            logger.warning("Herb names table missing at %s; relying on fallback NER.", self.herb_table_path)
            return

        try:
            with open(self.herb_table_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            herbs_dict = data.get("herbs", {})
            for key, entry in herbs_dict.items():
                botanical = entry.get("botanical_name", key)
                self.herb_lookup[key.lower()] = botanical
                self.herb_lookup[botanical.lower()] = botanical

                for syn in entry.get("synonyms", []):
                    self.herb_lookup[syn.lower()] = botanical

            logger.debug("Loaded %d herb synonym mappings into EntityExtractor", len(self.herb_lookup))
        except Exception as e:
            logger.error("Failed to parse herb names table: %s", e)

    def extract(
        self,
        context: Optional[ContextObject] = None,
        question: str = "",
    ) -> EntitySet:
        """Extract EntitySet combining ContextObject and question text."""
        combined_text = question
        if context:
            combined_text = f"{question} {self._context_to_text(context)}"

        # 1. Herb and biological resource extraction
        herbs = self._extract_herbs(context, combined_text)
        biological_resources = list(herbs)

        # 2. Jurisdiction & destination extraction
        destination, jurisdictions = self._extract_jurisdictions(context, combined_text)

        # 3. IP Types extraction
        ip_types = self._extract_ip_types(context, combined_text)

        # 4. Formulation & regulatory regime detection
        formulation_name = self._extract_formulation_name(context, combined_text)
        regulatory_regime = self._infer_regulatory_regime(destination, ip_types, combined_text)

        return EntitySet(
            herbs=herbs,
            jurisdictions=jurisdictions,
            ip_types=ip_types,
            biological_resources=biological_resources,
            formulation_name=formulation_name,
            destination_country=destination,
            regulatory_regime=regulatory_regime,
            raw_entities={"combined_text": combined_text},
        )

    def _extract_herbs(self, context: Optional[ContextObject], text: str) -> List[str]:
        """Extract botanical herbs using curated lookup table first, with regex scanning."""
        found_herbs: List[str] = []
        lower_text = text.lower()

        # Check herbs in context object first
        if isinstance(context, ExportContextObject):
            for h in context.herbs:
                resolved = self._resolve_herb_name(h)
                if resolved and resolved not in found_herbs:
                    found_herbs.append(resolved)

        # Scan text for curated herb synonyms (longest match first)
        sorted_synonyms = sorted(self.herb_lookup.keys(), key=len, reverse=True)
        for syn in sorted_synonyms:
            pattern = r"\b" + re.escape(syn) + r"\b"
            if re.search(pattern, lower_text):
                botanical = self.herb_lookup[syn]
                if botanical not in found_herbs:
                    found_herbs.append(botanical)

        return found_herbs

    def _resolve_herb_name(self, name: str) -> str:
        """Resolve a single herb string to botanical name if in table; otherwise return clean string."""
        clean = name.strip()
        lower = clean.lower()

        # Check direct lookup
        if lower in self.herb_lookup:
            return self.herb_lookup[lower]

        # Check partial / bracketed name e.g. "Ashwagandha (Withania somnifera)"
        match = re.search(r"\(([^)]+)\)", clean)
        if match:
            inner = match.group(1).lower().strip()
            if inner in self.herb_lookup:
                return self.herb_lookup[inner]

        # Scan words
        for word in lower.split():
            if word in self.herb_lookup:
                return self.herb_lookup[word]

        return clean

    def _extract_jurisdictions(
        self,
        context: Optional[ContextObject],
        text: str,
    ) -> tuple[Optional[str], List[str]]:
        """Extract destination country and canonical jurisdictions list."""
        destination: Optional[str] = None
        jurisdictions: List[str] = ["INDIA"]  # Domestic regulatory compliance is always included

        if isinstance(context, ExportContextObject) and context.destination:
            dest_raw = context.destination.lower()
            for key, val in self.JURISDICTION_MAP.items():
                if key in dest_raw:
                    destination = val
                    if val not in jurisdictions:
                        jurisdictions.append(val)
                    break
            if not destination:
                destination = context.destination

        # Scan free text for explicit target jurisdictions
        lower_text = text.lower()
        for key, val in self.JURISDICTION_MAP.items():
            pattern = r"\b" + re.escape(key) + r"\b"
            if re.search(pattern, lower_text):
                if val not in jurisdictions:
                    jurisdictions.append(val)
                if not destination and val != "INDIA":
                    destination = val

        return destination, jurisdictions

    def _extract_ip_types(self, context: Optional[ContextObject], text: str) -> List[IPType]:
        """Extract relevant IP types from ContextObject and question text."""
        ip_types: List[IPType] = []

        # Context-based mapping
        if isinstance(context, PatentContextObject):
            ip_types.append(IPType.PATENT)
            if context.uses_biological_resources:
                ip_types.append(IPType.ABS)
        elif isinstance(context, ExportContextObject):
            ip_types.append(IPType.EXPORT)
            if context.nba_approached or "RESEARCH" in context.purpose:
                ip_types.append(IPType.ABS)
        elif isinstance(context, MedicinalContextObject):
            ip_types.append(IPType.DRUG_REGULATION)
            ip_types.append(IPType.FOOD_REGULATION)
        elif isinstance(context, BusinessContextObject):
            ip_types.append(IPType.TRADEMARK)
            ip_types.append(IPType.DESIGN)
        elif isinstance(context, ResearchContextObject):
            ip_types.append(IPType.ABS)
            if context.research_type == "IP":
                ip_types.append(IPType.PATENT)

        # Text-based regex triggers
        for ip_type, patterns in self.IP_PATTERNS.items():
            for p in patterns:
                if re.search(p, text, re.IGNORECASE):
                    if ip_type not in ip_types:
                        ip_types.append(ip_type)
                    break

        if not ip_types:
            ip_types.append(IPType.GENERAL)

        return ip_types

    def _extract_formulation_name(self, context: Optional[ContextObject], text: str) -> Optional[str]:
        """Extract classical or proprietary formulation name if present."""
        # Common formulation patterns
        matches = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Churna|Taila|Ghrita|Vati|Gutika|Asava|Arishta|Avaleha|Syrup|Capsules|Tablet))\b", text)
        if matches:
            return matches[0]
        return None

    def _infer_regulatory_regime(
        self,
        destination: Optional[str],
        ip_types: List[IPType],
        text: str,
    ) -> Optional[str]:
        """Infer target regulatory regime description."""
        if destination == "EU":
            return "EU Traditional Herbal Medicinal Products Directive (THMPD) & Food Supplements"
        if destination == "USA":
            return "US FDA Dietary Supplement Health and Education Act (DSHEA)"
        if IPType.FOOD_REGULATION in ip_types or "ayurveda aahara" in text.lower():
            return "FSSAI (Ayurveda Aahara) Regulations 2022"
        if IPType.PATENT in ip_types:
            return "Indian Patents Act 1970 (Section 3(p) & Section 10(4))"
        if IPType.ABS in ip_types:
            return "Biological Diversity Act 2002 (ABS Framework)"
        return "AYUSH Drug & IPR Framework"

    def _context_to_text(self, context: ContextObject) -> str:
        """Convert ContextObject to supplementary text representation for extraction."""
        if hasattr(context, "raw_answers") and context.raw_answers:
            return " ".join(str(v) for v in context.raw_answers.values())
        return str(context)


# Module-level convenience extractor
default_entity_extractor = EntityExtractor()


def extract_entities(
    context: Optional[ContextObject] = None,
    question: str = "",
) -> EntitySet:
    """Extract EntitySet from ContextObject and question text."""
    return default_entity_extractor.extract(context, question)
