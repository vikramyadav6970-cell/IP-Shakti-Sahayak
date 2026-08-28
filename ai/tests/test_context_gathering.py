"""Unit tests for the Context Gathering Agent and typed ContextObjects."""

import pytest

from src.classification.intent_classifier import DomainIntent
from src.context_gathering.agent import (
    AnswerType,
    ContextQuestion,
    ExportContextObject,
    PatentContextObject,
    MedicinalContextObject,
    BusinessContextObject,
    ResearchContextObject,
    OtherContextObject,
    ContextGatheringAgent,
    get_context_questions,
    parse_context_answers,
)


def test_get_questions_export_intent():
    """EXPORT intent should return expected questions with correct answer_types."""
    questions = get_context_questions(DomainIntent.EXPORT)

    assert len(questions) >= 4
    q_ids = [q.question_id for q in questions]
    assert "herbs" in q_ids
    assert "destination" in q_ids
    assert "purpose" in q_ids
    assert "nba_approached" in q_ids

    dest_q = next(q for q in questions if q.question_id == "destination")
    assert dest_q.answer_type == AnswerType.SINGLE_SELECT
    assert dest_q.options is not None
    assert any("European Union" in opt for opt in dest_q.options)


def test_get_questions_patent_intent():
    """PATENT intent should return expected questions with correct answer_types."""
    questions = get_context_questions(DomainIntent.PATENT)

    assert len(questions) >= 4
    q_ids = [q.question_id for q in questions]
    assert "novel_aspect" in q_ids
    assert "type" in q_ids
    assert "prior_art_search_needed" in q_ids
    assert "uses_biological_resources" in q_ids

    novel_q = next(q for q in questions if q.question_id == "novel_aspect")
    assert novel_q.answer_type == AnswerType.FREE_TEXT


def test_get_questions_other_intent():
    """OTHER intent should return exactly 1 free-text description question."""
    questions = get_context_questions(DomainIntent.OTHER)

    assert len(questions) == 1
    assert questions[0].question_id == "free_description"
    assert questions[0].answer_type == AnswerType.FREE_TEXT


def test_parse_answers_export():
    """parse_answers on mock EXPORT answer dict produces correctly typed ExportContextObject."""
    raw_answers = {
        "herbs": "Ashwagandha (Withania somnifera), Tulsi (Ocimum sanctum)",
        "destination": "European Union (EU)",
        "purpose": "COMMERCIAL",
        "nba_approached": "Yes",
        "already_in_market": "No",
    }

    ctx = parse_context_answers(DomainIntent.EXPORT, raw_answers)

    assert isinstance(ctx, ExportContextObject)
    assert ctx.domain_intent == DomainIntent.EXPORT
    assert len(ctx.herbs) == 2
    assert "Ashwagandha (Withania somnifera)" in ctx.herbs
    assert ctx.destination == "European Union (EU)"
    assert ctx.purpose == "COMMERCIAL"
    assert ctx.nba_approached is True
    assert ctx.already_in_market is False


def test_parse_answers_patent():
    """parse_answers on mock PATENT answer dict produces correctly typed PatentContextObject."""
    raw_answers = {
        "novel_aspect": "Supercritical CO2 extraction yielding 5x withanolide content",
        "type": "PROCESS",
        "prior_art_search_needed": "Yes",
        "uses_biological_resources": "Yes",
    }

    ctx = parse_context_answers(DomainIntent.PATENT, raw_answers)

    assert isinstance(ctx, PatentContextObject)
    assert ctx.domain_intent == DomainIntent.PATENT
    assert "Supercritical CO2" in ctx.novel_aspect
    assert ctx.type == "PROCESS"
    assert ctx.prior_art_search_needed is True
    assert ctx.uses_biological_resources is True


def test_parse_answers_medicinal():
    """parse_answers on mock MEDICINAL answer dict produces correctly typed MedicinalContextObject."""
    raw_answers = {
        "formulation_type": "PROPRIETARY",
        "from_authoritative_text": "No",
        "new_ingredients": "Zinc gluconate, Synthetic Vitamin C",
    }

    ctx = parse_context_answers(DomainIntent.MEDICINAL, raw_answers)

    assert isinstance(ctx, MedicinalContextObject)
    assert ctx.formulation_type == "PROPRIETARY"
    assert ctx.from_authoritative_text is False
    assert "Zinc gluconate" in ctx.new_ingredients


def test_parse_answers_business():
    """parse_answers on mock BUSINESS answer dict produces correctly typed BusinessContextObject."""
    raw_answers = {
        "product_type": "Herbal Skincare (Class 3)",
        "brand_name": "VedaGlow",
        "target_market": "INTERNATIONAL",
    }

    ctx = parse_context_answers(DomainIntent.BUSINESS, raw_answers)

    assert isinstance(ctx, BusinessContextObject)
    assert ctx.brand_name == "VedaGlow"
    assert ctx.target_market == "INTERNATIONAL"


def test_parse_answers_research():
    """parse_answers on mock RESEARCH answer dict produces correctly typed ResearchContextObject."""
    raw_answers = {
        "research_type": "PHYTOCHEMICAL",
        "biological_resources": "Yes",
        "publish_internationally": "Yes",
    }

    ctx = parse_context_answers(DomainIntent.RESEARCH, raw_answers)

    assert isinstance(ctx, ResearchContextObject)
    assert ctx.research_type == "PHYTOCHEMICAL"
    assert ctx.biological_resources is True
    assert ctx.publish_internationally is True
