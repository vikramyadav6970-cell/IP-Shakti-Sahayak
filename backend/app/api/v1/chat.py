from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.security.dependencies import get_optional_current_user, get_current_user
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, ConversationListResponse, ConversationDetailResponse
from app.services.chat_service import ChatService
from app.repositories.chat_repo import ChatRepository
from app.security.rate_limit import RateLimiter
from typing import List, Optional
from uuid import UUID

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("", response_model=ChatResponse, dependencies=[Depends(RateLimiter(10, 60))])
async def process_chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Process a chat query, retrieve context, call AI layer, and persist the conversation.
    """
    service = ChatService(db)
    user_id = current_user.id if current_user else None
    return await service.process_chat(request, user_id)

@router.get("/conversations", response_model=List[ConversationListResponse], dependencies=[Depends(RateLimiter(60, 60))])
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all conversations for the authenticated user.
    """
    repo = ChatRepository(db)
    conversations = await repo.list_conversations(current_user.id)
    return conversations

@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse, dependencies=[Depends(RateLimiter(60, 60))])
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get full message and citation history for a specific conversation.
    """
    repo = ChatRepository(db)
    # The repository enforces that the user_id matches the conversation's user_id
    conversation = await repo.get_conversation_with_messages(conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found or unauthorized")
    
    return conversation
