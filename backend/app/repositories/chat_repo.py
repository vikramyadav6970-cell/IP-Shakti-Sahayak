from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from uuid import UUID

from app.models.chat import Conversation, Message, Citation, MessageRole

class ChatRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def get_conversation(self, conversation_id: UUID) -> Optional[Conversation]:
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_conversation(self, user_id: UUID) -> Conversation:
        conv = Conversation(user_id=user_id)
        self.session.add(conv)
        await self.session.flush()
        return conv

    async def add_message(
        self, 
        conversation_id: UUID, 
        role: MessageRole, 
        content: str,
        jurisdiction: Optional[str] = None,
        confidence_score: Optional[float] = None,
        confidence_label: Optional[str] = None,
        requires_human_review: bool = False
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            jurisdiction=jurisdiction,
            confidence_score=confidence_score,
            confidence_label=confidence_label,
            requires_human_review=requires_human_review
        )
        self.session.add(msg)
        await self.session.flush()
        return msg

    async def add_citation(
        self,
        message_id: UUID,
        document_title: str,
        corpus_collection: str,
        jurisdiction: Optional[str] = None,
        document_type: Optional[str] = None,
        section_ref: Optional[str] = None,
        source_url: Optional[str] = None
    ) -> Citation:
        cit = Citation(
            message_id=message_id,
            document_title=document_title,
            corpus_collection=corpus_collection,
            jurisdiction=jurisdiction,
            document_type=document_type,
            section_ref=section_ref,
            source_url=source_url
        )
        self.session.add(cit)
        await self.session.flush()
        return cit

    async def list_conversations(self, user_id: UUID) -> List[Conversation]:
        stmt = select(Conversation).where(Conversation.user_id == user_id).order_by(Conversation.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    from sqlalchemy.orm import selectinload

    async def get_conversation_with_messages(self, conversation_id: UUID, user_id: UUID = None) -> Optional[Conversation]:
        # Eagerly load messages and their citations
        stmt = select(Conversation).options(
            selectinload(Conversation.messages).selectinload(Message.citations)
        ).where(Conversation.id == conversation_id)
        
        # If user_id is provided, enforce access control
        if user_id:
            stmt = stmt.where(Conversation.user_id == user_id)
            
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
