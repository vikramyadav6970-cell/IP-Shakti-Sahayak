from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    domain_intent: str
    session_id: Optional[str] = None
    jurisdiction: str
    language: str
    conversation_id: Optional[str] = None

class CitationSchema(BaseModel):
    document_title: str
    section_ref: Optional[str] = None
    source_url: Optional[str] = None
    jurisdiction: str
    document_type: str
    corpus_collection: str

class ChatResponse(BaseModel):
    answer: str
    confidence: float
    confidence_label: str
    classification: str
    citations: List[CitationSchema]
    requires_human_review: bool
    conversation_id: str

from datetime import datetime

class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    jurisdiction: Optional[str] = None
    confidence_score: Optional[float] = None
    confidence_label: Optional[str] = None
    requires_human_review: bool
    citations: List[CitationSchema] = []
    created_at: datetime

class ConversationListResponse(BaseModel):
    id: UUID
    created_at: datetime

class ConversationDetailResponse(BaseModel):
    id: UUID
    created_at: datetime
    messages: List[MessageResponse]
