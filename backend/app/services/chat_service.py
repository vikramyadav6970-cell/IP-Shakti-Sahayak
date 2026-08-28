import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.schemas.chat import ChatRequest, ChatResponse, CitationSchema
from app.repositories.chat_repo import ChatRepository
from app.models.chat import MessageRole
from app.services.audit import write_audit_log
from app.security.rate_limit import redis_client

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ChatRepository(db)

    async def process_chat(self, request: ChatRequest, user_id: UUID) -> ChatResponse:
        context_object = None
        entity_set = None
        
        # 1. Fetch context from Redis if session_id is provided
        if request.session_id:
            key = f"chat_session:{request.session_id}"
            cached_data = redis_client.get(key)
            if cached_data:
                try:
                    data = json.loads(cached_data)
                    context_object = data.get("context_object")
                    entity_set = data.get("entity_set")
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse session data for session_id {request.session_id}")
            else:
                logger.warning(f"Cache miss for session_id {request.session_id} - proceeding without context")

        # 2. Mock AI Layer query pipeline
        # (check ai/status.md for the current function signature/interface)
        # We will mock the response here.
        mock_ai_response = self._mock_ai_query_pipeline(
            question=request.question,
            domain_intent=request.domain_intent,
            jurisdiction=request.jurisdiction,
            language=request.language,
            context_object=context_object,
            entity_set=entity_set
        )

        # Enforce hard constraint: zero citations or low confidence -> requires human review
        requires_human_review = mock_ai_response["requires_human_review"]
        if not mock_ai_response["citations"] or mock_ai_response["confidence"] < 0.7:
            requires_human_review = True

        # 3. Persist Conversation, Messages, and Citations
        if request.conversation_id:
            conv_id = UUID(request.conversation_id)
            conv = await self.repo.get_conversation(conv_id)
            if not conv:
                conv = await self.repo.create_conversation(user_id)
        else:
            conv = await self.repo.create_conversation(user_id)

        # Persist User Message
        await self.repo.add_message(
            conversation_id=conv.id,
            role=MessageRole.user,
            content=request.question
        )

        # Persist Assistant Message
        assistant_msg = await self.repo.add_message(
            conversation_id=conv.id,
            role=MessageRole.assistant,
            content=mock_ai_response["answer"],
            jurisdiction=request.jurisdiction,
            confidence_score=mock_ai_response["confidence"],
            confidence_label=mock_ai_response["confidence_label"],
            requires_human_review=requires_human_review
        )

        # Persist Citations
        persisted_citations = []
        for cit_data in mock_ai_response["citations"]:
            cit = await self.repo.add_citation(
                message_id=assistant_msg.id,
                document_title=cit_data["document_title"],
                corpus_collection=cit_data["corpus_collection"],
                jurisdiction=cit_data.get("jurisdiction"),
                document_type=cit_data.get("document_type"),
                section_ref=cit_data.get("section_ref"),
                source_url=cit_data.get("source_url")
            )
            persisted_citations.append(CitationSchema(
                document_title=cit.document_title,
                section_ref=cit.section_ref,
                source_url=cit.source_url,
                jurisdiction=cit.jurisdiction or request.jurisdiction,
                document_type=cit.document_type or "UNKNOWN",
                corpus_collection=cit.corpus_collection
            ))

        # Audit log — DPDP compliance
        await write_audit_log(
            db=self.db,
            user_id=user_id,
            action="CHAT_QUERY",
            resource_type="Conversation",
            resource_id=str(conv.id),
            metadata_payload={"domain_intent": request.domain_intent, "confidence": mock_ai_response["confidence"]},
        )

        await self.db.commit()

        # 4. Return response
        return ChatResponse(
            answer=mock_ai_response["answer"],
            confidence=mock_ai_response["confidence"],
            confidence_label=mock_ai_response["confidence_label"],
            classification=mock_ai_response["classification"],
            citations=persisted_citations,
            requires_human_review=requires_human_review,
            conversation_id=str(conv.id)
        )

    def _mock_ai_query_pipeline(self, question, domain_intent, jurisdiction, language, context_object, entity_set) -> dict:
        """
        Mock for the ai/ query pipeline.
        Returns a mock dict matching the expected frontend output structure.
        """
        # If context was provided, acknowledge it
        has_context = bool(context_object and entity_set)
        
        return {
            "answer": f"Mock answer for '{question}'. Context provided: {has_context}.",
            "confidence": 0.85,
            "confidence_label": "High",
            "classification": domain_intent,
            "requires_human_review": False,
            "citations": [
                {
                    "document_title": "Mock Act 2026",
                    "corpus_collection": "legal_statutory",
                    "jurisdiction": jurisdiction,
                    "document_type": "STATUTE",
                    "section_ref": "Section 42",
                    "source_url": "https://example.com/act"
                }
            ]
        }
