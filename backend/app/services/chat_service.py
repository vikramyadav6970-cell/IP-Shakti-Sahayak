import json
import logging
from dataclasses import asdict
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional

from app.schemas.chat import ChatRequest, ChatResponse, CitationSchema
from app.security.rate_limit import redis_client

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_chat(self, request: ChatRequest, user_id: UUID) -> ChatResponse:
        context_object = None
        entity_set = None

        # 1. Fetch context from Redis if session_id is provided
        if request.session_id and redis_client is not None:
            key = f"chat_session:{request.session_id}"
            try:
                cached_data = redis_client.get(key)
                if cached_data:
                    data = json.loads(cached_data)
                    context_object = data.get("context_object")
                    entity_set = data.get("entity_set")
                else:
                    logger.warning(f"Cache miss for session_id {request.session_id}")
            except Exception as e:
                logger.warning(f"Failed to fetch session data: {e}")

        # 2. Call AI Layer query pipeline
        ai_response = await self._call_ai_pipeline(
            question=request.question,
            domain_intent=request.domain_intent,
            jurisdiction=request.jurisdiction,
            language=request.language,
            context_object=context_object,
            entity_set=entity_set,
        )

        # Enforce hard constraint: zero citations or low confidence -> requires human review
        requires_human_review = ai_response["requires_human_review"]
        if not ai_response["citations"] or ai_response["confidence"] < 0.7:
            requires_human_review = True

        # 3. Persist Conversation, Messages, and Citations (if DB is available)
        conversation_id = None
        try:
            from app.repositories.chat_repo import ChatRepository
            from app.models.chat import MessageRole
            from app.services.audit import write_audit_log

            repo = ChatRepository(self.db)

            if request.conversation_id:
                conv_id = UUID(request.conversation_id)
                conv = await repo.get_conversation(conv_id)
                if not conv:
                    conv = await repo.create_conversation(user_id)
            else:
                conv = await repo.create_conversation(user_id)

            conversation_id = str(conv.id)

            # Persist User Message
            await repo.add_message(
                conversation_id=conv.id,
                role=MessageRole.user,
                content=request.question
            )

            # Persist Assistant Message
            assistant_msg = await repo.add_message(
                conversation_id=conv.id,
                role=MessageRole.assistant,
                content=ai_response["answer"],
                jurisdiction=request.jurisdiction,
                confidence_score=ai_response["confidence"],
                confidence_label=ai_response["confidence_label"],
                requires_human_review=requires_human_review
            )

            # Persist Citations
            for cit_data in ai_response["citations"]:
                await repo.add_citation(
                    message_id=assistant_msg.id,
                    document_title=cit_data.get("document_title", ""),
                    corpus_collection=cit_data.get("collection", ""),
                    jurisdiction=cit_data.get("jurisdiction", request.jurisdiction),
                    document_type=cit_data.get("document_type", "UNKNOWN"),
                    section_ref=cit_data.get("section_reference"),
                    source_url=cit_data.get("source_url"),
                )

            # Audit log — DPDP compliance
            await write_audit_log(
                db=self.db,
                user_id=user_id,
                action="CHAT_QUERY",
                resource_type="Conversation",
                resource_id=conversation_id,
                metadata_payload={"domain_intent": request.domain_intent, "confidence": ai_response["confidence"]},
            )

            await self.db.commit()
        except Exception as e:
            logger.warning(f"DB persistence failed (non-fatal): {e}")
            # AI response still goes through even if DB is down

        # 4. Build citations for response
        response_citations = [
            CitationSchema(
                id=cit.get("id", f"cite-{i}"),
                document_title=cit.get("document_title", ""),
                section_reference=cit.get("section_reference"),
                collection=cit.get("collection", ""),
                jurisdiction=cit.get("jurisdiction", request.jurisdiction),
                source_authority=cit.get("source_authority"),
                source_url=cit.get("source_url"),
                relevance_score=cit.get("relevance_score"),
                excerpt=cit.get("excerpt"),
                document_type=cit.get("document_type"),
            )
            for i, cit in enumerate(ai_response["citations"])
        ]

        return ChatResponse(
            answer=ai_response["answer"],
            confidence=ai_response["confidence"],
            confidence_label=ai_response["confidence_label"],
            classification=ai_response.get("classification"),
            abs_assessment=ai_response.get("abs_assessment"),
            citations=response_citations,
            requires_human_review=requires_human_review,
            conversation_id=conversation_id,
            sub_tasks_run=ai_response.get("sub_tasks_run", []),
            sources_by_collection=ai_response.get("sources_by_collection", {}),
        )

    async def _call_ai_pipeline(
        self,
        question: str,
        domain_intent: str,
        jurisdiction: str,
        language: str,
        context_object: Optional[dict],
        entity_set: Optional[dict],
    ) -> dict:
        """
        Call the real AI query pipeline. Falls back to mock if unavailable.
        """
        try:
            from src.reasoning.query_pipeline import query as ai_query
            from src.context_gathering.agent import parse_context_answers

            # Reconstruct typed ContextObject from cached dict if available
            typed_context = None
            if context_object and "intent" in context_object:
                try:
                    raw_answers = context_object.get("raw_answers", context_object.get("parsed_answers", context_object.get("answers", {})))
                    intent_val = context_object.get("intent", context_object.get("domain_intent", domain_intent))
                    typed_context = parse_context_answers(intent_val, raw_answers)
                except Exception as e:
                    logger.warning(f"Failed to reconstruct ContextObject: {e}")

            # Call the async query pipeline
            result = await ai_query(
                question=question,
                domain_intent=domain_intent,
                context=typed_context,
                jurisdiction=jurisdiction,
                language=language,
            )

            # Convert QueryResult dataclass to dict
            citations = []
            for cit in result.citations:
                citations.append({
                    "id": getattr(cit, 'chunk_id', ''),
                    "document_title": getattr(cit, 'title', ''),
                    "section_reference": getattr(cit, 'section_or_ref', ''),
                    "collection": getattr(cit, 'collection', ''),
                    "jurisdiction": getattr(cit, 'jurisdiction', jurisdiction),
                    "source_url": getattr(cit, 'source_url', None),
                    "excerpt": getattr(cit, 'snippet', ''),
                    "relevance_score": None,
                    "document_type": None,
                })

            # Build sources_by_collection as int counts
            sources_by_collection = {}
            if hasattr(result, 'sources_by_collection') and result.sources_by_collection:
                for coll, sources in result.sources_by_collection.items():
                    sources_by_collection[coll] = len(sources) if isinstance(sources, list) else int(sources)

            # Classification
            classification_str = None
            if result.classification:
                classification_str = getattr(result.classification, 'category', str(result.classification))

            # ABS assessment
            abs_dict = None
            if result.abs_assessment:
                try:
                    abs_dict = asdict(result.abs_assessment) if hasattr(result.abs_assessment, '__dataclass_fields__') else None
                except Exception:
                    abs_dict = None

            return {
                "answer": result.answer,
                "confidence": result.confidence,
                "confidence_label": result.confidence_label,
                "classification": classification_str,
                "abs_assessment": abs_dict,
                "requires_human_review": result.requires_human_review,
                "citations": citations,
                "sub_tasks_run": result.sub_tasks_run,
                "sources_by_collection": sources_by_collection,
            }

        except Exception as e:
            logger.warning(f"AI pipeline unavailable ({e}), using mock response")
            return self._mock_ai_response(question, domain_intent, jurisdiction, context_object, entity_set)

    def _mock_ai_response(self, question, domain_intent, jurisdiction, context_object, entity_set) -> dict:
        """
        Fallback mock response when AI pipeline is unavailable.
        """
        has_context = bool(context_object and entity_set)

        return {
            "answer": f"""## Analysis for {domain_intent} Intent

Based on your query regarding **{domain_intent.lower()}** matters in Ayurvedic intellectual property:

### Key Findings

This is a **demo response** — the AI pipeline could not process the query (likely missing model weights or Qdrant connection). When fully operational, this section will contain:

1. **Citation-grounded legal analysis** traced to specific sections of Indian IP law
2. **Jurisdiction-specific guidance** with India and International answers clearly separated
3. **Product classification** determining your regulatory pathway

### Relevant Legal Framework

- **Patents Act 1970, Section 3(p)** — inventions that are essentially traditional knowledge are not patentable
- **Biological Diversity Act 2002** (as amended 2023) — governs access and benefit sharing
- **TKDL** — Traditional Knowledge Digital Library for prior art searches

### Context Status
- Context provided: **{has_context}**
- Question: *{question[:200]}*

> **⚠️ Note:** This is a fallback response. Connect LLM API key and Qdrant credentials in `.env` for real RAG-powered answers.

*Disclaimer: This AI-generated synthesis is for informational guidance only and does not constitute formal legal advice.*""",
            "confidence": 0.35 if not has_context else 0.55,
            "confidence_label": "LOW",
            "classification": domain_intent,
            "abs_assessment": None,
            "requires_human_review": True,
            "citations": [
                {
                    "id": "mock-cite-1",
                    "document_title": "The Patents Act, 1970",
                    "section_reference": "Section 3(p)",
                    "collection": "legal_statutory",
                    "jurisdiction": "India",
                    "source_authority": "Parliament of India",
                    "source_url": "https://indiacode.nic.in",
                    "relevance_score": 0.92,
                    "excerpt": "An invention which, in effect, is traditional knowledge or which is an aggregation or duplication of known properties of traditionally known component or components.",
                    "document_type": "STATUTE",
                },
                {
                    "id": "mock-cite-2",
                    "document_title": "Biological Diversity Act, 2002",
                    "section_reference": "Section 3 (as amended 2023)",
                    "collection": "legal_statutory",
                    "jurisdiction": "India",
                    "source_authority": "Ministry of Environment",
                    "source_url": "https://nbaindia.org",
                    "relevance_score": 0.85,
                    "excerpt": "No person shall, without previous approval of the National Biodiversity Authority, obtain any biological resource occurring in India.",
                    "document_type": "STATUTE",
                },
            ],
            "sub_tasks_run": ["legal_analysis", "abs_check"],
            "sources_by_collection": {
                "legal_statutory": 2,
                "international_export": 0,
                "standards_formulations": 0,
                "procedural_forms": 0,
                "case_law_prior_art": 0,
            },
        }
