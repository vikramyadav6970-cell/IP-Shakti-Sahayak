import uuid
import json
import logging
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.context import DomainIntent, ContextQuestion, AnswerType
from app.security.rate_limit import redis_client

logger = logging.getLogger(__name__)

# Answer type mapping from AI layer enum to backend schema enum
_ANSWER_TYPE_MAP = {
    "FREE_TEXT": AnswerType.TEXT,
    "SINGLE_SELECT": AnswerType.SINGLE_CHOICE,
    "MULTI_SELECT": AnswerType.MULTIPLE_CHOICE,
    "text": AnswerType.TEXT,
    "single_choice": AnswerType.SINGLE_CHOICE,
    "multiple_choice": AnswerType.MULTIPLE_CHOICE,
}


def _map_answer_type(at: Any) -> AnswerType:
    """Convert AI layer AnswerType to backend schema AnswerType."""
    s = str(at.value if hasattr(at, 'value') else at)
    return _ANSWER_TYPE_MAP.get(s, AnswerType.TEXT)


class ContextService:
    @staticmethod
    def get_questions(intent: DomainIntent) -> list[ContextQuestion]:
        """
        Get context-gathering questions from the real AI layer.
        Falls back to stub if AI layer is unavailable.
        """
        try:
            from src.context_gathering.agent import get_context_questions as ai_get_questions
            ai_questions = ai_get_questions(intent.value)
            return [
                ContextQuestion(
                    question_id=q.question_id,
                    question_text=q.question_text,
                    answer_type=_map_answer_type(q.answer_type),
                    options=q.options,
                    required=q.required,
                    placeholder=getattr(q, 'placeholder', None),
                    help_text=getattr(q, 'help_text', None),
                )
                for q in ai_questions
            ]
        except Exception as e:
            logger.warning(f"AI layer context gathering unavailable ({e}), using stubs")
            return ContextService._stub_questions(intent)

    @staticmethod
    def process_context(intent: DomainIntent, answers: dict, question: str | None) -> tuple[dict, dict]:
        """
        Process context answers through AI layer's parse_context_answers + extract_entities.
        Falls back to stub if AI layer is unavailable.
        """
        try:
            from src.context_gathering.agent import parse_context_answers
            from src.entity_extraction.extractor import extract_entities

            # Parse answers into typed ContextObject
            context_obj = parse_context_answers(intent.value, answers)

            # Extract entities from the context object + question
            entity_set = extract_entities(
                context=context_obj,
                question=question or ""
            )

            # Convert dataclasses to dicts for JSON serialization
            context_dict = asdict(context_obj) if hasattr(context_obj, '__dataclass_fields__') else {"intent": intent.value, "answers": answers}
            entity_dict = asdict(entity_set) if hasattr(entity_set, '__dataclass_fields__') else {}

            # Convert enums in entity_dict to strings
            if "ip_types" in entity_dict:
                entity_dict["ip_types"] = [str(t.value) if hasattr(t, 'value') else str(t) for t in entity_dict["ip_types"]]

            return context_dict, entity_dict
        except Exception as e:
            logger.warning(f"AI layer context processing unavailable ({e}), using stubs")
            return ContextService._stub_process(intent, answers, question)

    @staticmethod
    def save_session(session_id: str, context_object: dict, entity_set: dict):
        """Save session to Upstash Redis with a 1-hour TTL. No-op if Redis is unavailable."""
        if redis_client is None:
            logger.warning("Redis unavailable — session not persisted (chat will proceed without context)")
            return

        try:
            key = f"chat_session:{session_id}"
            data = {
                "context_object": context_object,
                "entity_set": entity_set
            }
            redis_client.setex(key, 3600, json.dumps(data, default=str))
        except Exception as e:
            logger.warning(f"Failed to save session to Redis: {e}")

    # ---- Fallback stubs (used when AI layer import fails) ----

    @staticmethod
    def _stub_questions(intent: DomainIntent) -> list[ContextQuestion]:
        if intent == DomainIntent.BUSINESS:
            return [
                ContextQuestion(question_id="q1", question_text="What is the product type?", answer_type=AnswerType.TEXT),
                ContextQuestion(question_id="q2", question_text="Do you have an existing brand name?", answer_type=AnswerType.SINGLE_CHOICE, options=["Yes", "No"])
            ]
        elif intent == DomainIntent.PATENT:
            return [
                ContextQuestion(question_id="q1", question_text="What is the novel aspect?", answer_type=AnswerType.TEXT),
                ContextQuestion(question_id="q2", question_text="Is it a process or a formulation?", answer_type=AnswerType.SINGLE_CHOICE, options=["Process", "Formulation", "Both"])
            ]
        return [
            ContextQuestion(question_id="q1", question_text="Please describe your product or query in detail.", answer_type=AnswerType.TEXT)
        ]

    @staticmethod
    def _stub_process(intent: DomainIntent, answers: dict, question: str | None) -> tuple[dict, dict]:
        context_object = {
            "intent": intent.value,
            "parsed_answers": answers,
            "status": "STUBBED_CONTEXT"
        }
        entity_set = {
            "herbs": [],
            "jurisdictions": ["INDIA"],
            "ip_types": [],
            "biological_resources": [],
            "formulation_name": None,
            "destination_country": None,
            "regulatory_regime": None,
        }
        return context_object, entity_set


context_service = ContextService()
