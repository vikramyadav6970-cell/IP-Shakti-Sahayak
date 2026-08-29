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
    FREE_TEXT = "FREE_TEXT"
    SINGLE_SELECT = "SINGLE_SELECT"
    MULTI_SELECT = "MULTI_SELECT"


class ContextQuestion(BaseModel):
    question_id: str
    question_text: str
    answer_type: AnswerType
    options: Optional[List[str]] = None
    required: bool = True
    placeholder: Optional[str] = None
    help_text: Optional[str] = None


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
