from pydantic import BaseModel
from typing import Optional, List, Any
from uuid import UUID

class ClassificationRequest(BaseModel):
    product_id: UUID
    product_type: str
    derived_from_authoritative_text: bool
    formulation_novelty: str
    biological_resources_used: List[str]

class ClassificationResponse(BaseModel):
    id: UUID
    product_id: UUID
    category: str
    regulatory_pathway: str
    rules_fired: List[dict[str, Any]]
