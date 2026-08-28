from fastapi import APIRouter, Query, HTTPException, status
import uuid

from app.schemas.context import (
    DomainIntent, 
    ContextQuestionsResponse, 
    ContextProcessRequest, 
    ContextProcessResponse
)
from app.services.context_service import context_service
from app.security.rate_limit import RateLimiter
from fastapi import Depends

router = APIRouter(prefix="/context", tags=["context"])

@router.get("/questions", response_model=ContextQuestionsResponse, dependencies=[Depends(RateLimiter(60, 60))])
async def get_context_questions(
    intent: DomainIntent = Query(...)
):
    """
    Get context-gathering questions for a given domain intent.
    Public route (no auth required).
    """
    questions = context_service.get_questions(intent)
    return ContextQuestionsResponse(
        intent=intent,
        questions=questions
    )

@router.post("/process", response_model=ContextProcessResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RateLimiter(20, 60))])
async def process_context(
    request: ContextProcessRequest
):
    """
    Process context answers, extract entities, and create a session.
    Public route (called before entering chat).
    """
    context_obj, entity_set = context_service.process_context(
        intent=request.intent,
        answers=request.answers,
        question=request.question
    )
    
    session_id = str(uuid.uuid4())
    context_service.save_session(session_id, context_obj, entity_set)
    
    return ContextProcessResponse(
        session_id=session_id,
        context_object=context_obj,
        entity_set=entity_set
    )
