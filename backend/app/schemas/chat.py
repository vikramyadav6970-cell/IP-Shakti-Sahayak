from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    domain_intent: str
    session_id: Optional[str] = None
    jurisdiction: str = "INDIA"
    language: str = "en"
    conversation_id: Optional[str] = None


class CitationSchema(BaseModel):
    id: Optional[str] = None
    document_title: str
    section_reference: Optional[str] = None
    collection: str = ""
    jurisdiction: str = ""
    source_authority: Optional[str] = None
    source_url: Optional[str] = None
    relevance_score: Optional[float] = None
    excerpt: Optional[str] = None
    document_type: Optional[str] = None

    # Backend-only field aliases for DB persistence compatibility
    @property
    def section_ref(self) -> Optional[str]:
        return self.section_reference

    @property
    def corpus_collection(self) -> str:
        return self.collection


class ChatResponse(BaseModel):
    answer: str
    confidence: float
    confidence_label: str
    classification: Optional[str] = None
    abs_assessment: Optional[Dict[str, Any]] = None
    citations: List[CitationSchema] = []
    requires_human_review: bool = False
    conversation_id: Optional[str] = None
    sub_tasks_run: List[str] = []
    sources_by_collection: Dict[str, int] = {}


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
