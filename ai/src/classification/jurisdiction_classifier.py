"""Jurisdiction classifier.

Resolves concrete jurisdiction filter values ('INDIA', 'USA', 'EU', 'INTERNATIONAL')
for retrieval based on the UI-selected jurisdiction (primary source of truth) and
question text analysis. Enforces context.md §2 Rule 2 (no cross-jurisdiction leakage).
"""

from dataclasses import dataclass
from typing import List, Optional
import re


@dataclass
class JurisdictionClassificationResult:
    """Represents the resolved jurisdiction classification and metadata."""

    effective_jurisdiction: str  # "INDIA" | "USA" | "EU" | "INTERNATIONAL"
    detected_in_text: Optional[str] = None
    ui_selected_jurisdiction: str = "INDIA"
    mismatch_detected: bool = False
    warning_message: Optional[str] = None
    is_export_query: bool = False
    target_export_country: Optional[str] = None
    confidence: float = 1.0


class JurisdictionClassifier:
    """Rule-based jurisdiction classifier with text extraction heuristics."""

    # Regex patterns for jurisdiction detection
    USA_PATTERNS = [
        r"\b(?:USA|U\.S\.A|United States|US|U\.S)\b",
        r"\b(?:USPTO|FDA|USFDA|DSHEA|21 CFR|FTC|35 U\.S\.C)\b",
        r"\b(?:American market|New York|California)\b",
    ]

    EU_PATTERNS = [
        r"\b(?:EU|E\.U|European Union|Europe|European)\b",
        r"\b(?:EPO|EMA|THMPD|EFSA|CE mark)\b",
        r"\b(?:Germany|France|Italy|Spain|Netherlands|UK|United Kingdom|MHRA)\b",
    ]

    INDIA_PATTERNS = [
        r"\b(?:India|Indian|Bharat)\b",
        r"\b(?:AYUSH|FSSAI|NBA|TKDL|IP India|CGPDTM|SBB|CCRAS|PCIM&H|PLIM|ASUTAB)\b",
        r"\b(?:Patents Act 1970|Section 3\(p\)|Drugs and Cosmetics Act|Biological Diversity Act)\b",
        r"\b(?:Form 24D|Form 24E|Form III|Ayurveda Aahara)\b",
    ]

    INTL_PATTERNS = [
        r"\b(?:TRIPS|WTO|CBD|Nagoya Protocol|WIPO|GRATK|CITES)\b",
        r"\b(?:international|cross-border|global|multilateral|treaty)\b",
    ]

    EXPORT_PATTERNS = [
        r"\b(?:export|exporting|ship to|overseas|cross-border)\b",
    ]

    def classify(
        self,
        question: str,
        ui_selected_jurisdiction: Optional[str] = "INDIA",
    ) -> JurisdictionClassificationResult:
        """Classify jurisdiction for the given question and UI toggle.

        Args:
            question: User input question / prompt.
            ui_selected_jurisdiction: UI toggle value ("INDIA", "USA", "EU", "INTERNATIONAL").

        Returns:
            JurisdictionClassificationResult object.
        """
        ui_jur = (ui_selected_jurisdiction or "INDIA").upper().strip()
        text = question.strip()

        detected_in_text: Optional[str] = self._detect_jurisdiction_in_text(text)
        is_export = any(re.search(p, text, re.IGNORECASE) for p in self.EXPORT_PATTERNS)

        target_export: Optional[str] = None
        if is_export:
            if self._matches_pattern(text, self.USA_PATTERNS):
                target_export = "USA"
            elif self._matches_pattern(text, self.EU_PATTERNS):
                target_export = "EU"
            elif self._matches_pattern(text, self.INTL_PATTERNS):
                target_export = "INTERNATIONAL"

        # Case 1: Explicit export query mentioning source and destination (e.g. India -> EU or India -> USA)
        if is_export and target_export:
            effective_jur = "INTERNATIONAL"
            mismatch = False
            warning = None
            if ui_jur != "INTERNATIONAL" and ui_jur != target_export and ui_jur != "INDIA":
                mismatch = True
                warning = f"Export question targeting {target_export} detected. Retrieval will query both domestic and {target_export} export regulations."

            return JurisdictionClassificationResult(
                effective_jurisdiction=effective_jur,
                detected_in_text=target_export,
                ui_selected_jurisdiction=ui_jur,
                mismatch_detected=mismatch,
                warning_message=warning,
                is_export_query=True,
                target_export_country=target_export,
                confidence=0.95,
            )

        # Case 2: Explicit international treaty mentioned
        if detected_in_text == "INTERNATIONAL":
            return JurisdictionClassificationResult(
                effective_jurisdiction="INTERNATIONAL",
                detected_in_text="INTERNATIONAL",
                ui_selected_jurisdiction=ui_jur,
                mismatch_detected=(ui_jur != "INTERNATIONAL"),
                warning_message="International treaty or convention detected in query." if ui_jur != "INTERNATIONAL" else None,
                confidence=0.95,
            )

        # Case 3: Text explicitly names a jurisdiction different from UI selection
        if detected_in_text and detected_in_text != ui_jur:
            # Question explicitly mentions USA or EU, but UI was left on INDIA (or vice versa)
            return JurisdictionClassificationResult(
                effective_jurisdiction=detected_in_text,
                detected_in_text=detected_in_text,
                ui_selected_jurisdiction=ui_jur,
                mismatch_detected=True,
                warning_message=(
                    f"You selected '{ui_jur}' in the UI, but your question asks specifically about {detected_in_text} laws/regulations. "
                    f"Retrieval has been directed to {detected_in_text}."
                ),
                confidence=0.90,
            )

        # Case 4: No conflict — honor UI selection
        return JurisdictionClassificationResult(
            effective_jurisdiction=ui_jur,
            detected_in_text=detected_in_text,
            ui_selected_jurisdiction=ui_jur,
            mismatch_detected=False,
            warning_message=None,
            confidence=1.0,
        )

    def _detect_jurisdiction_in_text(self, text: str) -> Optional[str]:
        """Detect any explicit jurisdiction mentioned in the query text."""
        has_intl = self._matches_pattern(text, self.INTL_PATTERNS)
        has_usa = self._matches_pattern(text, self.USA_PATTERNS)
        has_eu = self._matches_pattern(text, self.EU_PATTERNS)
        has_india = self._matches_pattern(text, self.INDIA_PATTERNS)

        if has_intl:
            return "INTERNATIONAL"
        if has_usa and not has_india:
            return "USA"
        if has_eu and not has_india:
            return "EU"
        if has_india and not (has_usa or has_eu):
            return "INDIA"
        if has_usa and has_india:
            return "USA"
        if has_eu and has_india:
            return "EU"

        return None

    def _matches_pattern(self, text: str, patterns: List[str]) -> bool:
        """Helper to match a list of regex patterns."""
        for p in patterns:
            if re.search(p, text, re.IGNORECASE):
                return True
        return False


# Module-level convenience classifier
default_jurisdiction_classifier = JurisdictionClassifier()


def classify_jurisdiction(
    question: str,
    ui_selected_jurisdiction: Optional[str] = "INDIA",
) -> JurisdictionClassificationResult:
    """Classify jurisdiction for a question."""
    return default_jurisdiction_classifier.classify(question, ui_selected_jurisdiction)
