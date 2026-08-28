import uuid
import json
from app.schemas.context import DomainIntent, ContextQuestion, AnswerType
from app.security.rate_limit import redis_client

class ContextService:
    @staticmethod
    def get_questions(intent: DomainIntent) -> list[ContextQuestion]:
        """
        Stub for AI Layer T3.5 get_questions.
        Returns a list of context-gathering questions based on domain intent.
        """
        # A simple stub matching context.md example questions
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
        # Generic stub for others
        return [
            ContextQuestion(question_id="q1", question_text="Please describe your product or query in detail.", answer_type=AnswerType.TEXT)
        ]

    @staticmethod
    def process_context(intent: DomainIntent, answers: dict, question: str | None) -> tuple[dict, dict]:
        """
        Stub for AI Layer T3.5 parse_answers and T3.6 extract.
        Returns context_object and entity_set.
        """
        context_object = {
            "intent": intent.value,
            "parsed_answers": answers,
            "status": "STUBBED_CONTEXT"
        }
        
        entity_set = {
            "extracted_entities": ["STUB_HERB_1", "STUB_JURISDICTION_INDIA"] if question else [],
            "status": "STUBBED_ENTITIES"
        }
        
        return context_object, entity_set

    @staticmethod
    def save_session(session_id: str, context_object: dict, entity_set: dict):
        """Save session to Upstash Redis with a 1-hour TTL."""
        key = f"chat_session:{session_id}"
        data = {
            "context_object": context_object,
            "entity_set": entity_set
        }
        # TTL of 3600 seconds = 1 hour
        redis_client.setex(key, 3600, json.dumps(data))

context_service = ContextService()
