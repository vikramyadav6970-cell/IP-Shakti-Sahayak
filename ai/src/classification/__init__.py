"""Classification module — jurisdiction, intent, and product classifiers."""

from src.classification.jurisdiction_classifier import (
    JurisdictionClassifier,
    JurisdictionClassificationResult,
    classify_jurisdiction,
)
from src.classification.intent_classifier import (
    DomainIntent,
    FineGrainedIntent,
    INTENT_TO_COLLECTIONS_MAP,
    DOMAIN_TO_DEFAULT_INTENTS,
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

__all__ = [
    "JurisdictionClassifier",
    "JurisdictionClassificationResult",
    "classify_jurisdiction",
    "DomainIntent",
    "FineGrainedIntent",
    "INTENT_TO_COLLECTIONS_MAP",
    "DOMAIN_TO_DEFAULT_INTENTS",
    "IntentClassificationResult",
    "IntentClassifier",
    "classify_intent",
    "ProductCategory",
    "ProductClassificationInput",
    "ProductClassificationResult",
    "ProductClassifier",
    "classify_product",
]
