from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from enum import Enum

class DomainIntent(str, Enum):
    BUSINESS = "BUSINESS"
    EXPORT = "EXPORT"
    MEDICINAL = "MEDICINAL"
    PATENT = "PATENT"
    RESEARCH = "RESEARCH"
    OTHER = "OTHER"

class AnswerType(str, Enum):
    TEXT = "text"
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"

class ContextQuestion(BaseModel):
    question_id: str
    question_text: str
    answer_type: AnswerType
    options: Optional[List[str]] = None
    required: bool = True

class ContextQuestionsResponse(BaseModel):
    intent: DomainIntent
    questions: List[ContextQuestion]

class ContextProcessRequest(BaseModel):
    intent: DomainIntent
    answers: Dict[str, Any]
    question: Optional[str] = None

class ContextProcessResponse(BaseModel):
    session_id: str
    context_object: Dict[str, Any]
    entity_set: Dict[str, Any]
