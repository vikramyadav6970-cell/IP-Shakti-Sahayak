from pydantic import BaseModel
from typing import Optional, List, Any
from uuid import UUID


class IPAssessmentRequest(BaseModel):
    product_id: UUID
    ip_type: str  # e.g. "Patent", "Trademark", "GI", "Trade Secret", "Copyright"


class IPAssessmentResponse(BaseModel):
    id: UUID
    product_id: UUID
    ip_type: str
    relevance_label: str
    reasoning: str
    legal_provisions: List[dict[str, Any]]


class ABSAssessmentRequest(BaseModel):
    product_id: UUID
    biological_resources: List[dict[str, Any]]
    origin: Optional[str] = None
    purpose: Optional[str] = None


class ABSAssessmentResponse(BaseModel):
    id: UUID
    product_id: UUID
    biological_resources: List[dict[str, Any]]
    origin: Optional[str] = None
    purpose: Optional[str] = None
    relevance_label: str
    next_steps: List[dict[str, Any]]
