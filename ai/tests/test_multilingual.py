"""Unit tests for Multilingual / Hindi support and Bhashini client."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.classification.intent_classifier import DomainIntent
from src.multilingual.bhashini_client import (
    TranslationResult,
    BhashiniClient,
    translate_text,
)
from src.reasoning.llm_provider import LLMProvider
from src.reasoning.query_pipeline import QueryPipeline, QueryResult
from src.retrieval.hybrid_retriever import EvidenceChunk, HybridRetriever


class MockTranslationLLM(LLMProvider):
    """Mock LLM returning Hindi translation with citation placeholders preserved."""

    def __init__(self):
        super().__init__(model_name="mock-model", api_key="mock-key")

    def generate(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        if "Hindi" in system_prompt or "हिन्दी" in system_prompt:
            # Emulate translating English to Hindi while keeping __CITATION_TAG_X__ placeholders intact
            translated = (
                user_prompt.replace("Under Patents Act", "पेटेंट अधिनियम")
                .replace("Under the Patents Act", "पेटेंट अधिनियम")
                .replace("traditional knowledge is excluded", "पारंपरिक ज्ञान अपवर्जित है")
                .replace("traditional knowledge from patentability", "पारंपरिक ज्ञान पेटेंट योग्यता से अपवर्जित है")
                .replace("NBA approval is required", "एनबीए अनुमोदन आवश्यक है")
                .replace("Section 3(p) excludes", "धारा 3(p) अपवर्जित करती है")
            )
            return translated
        elif "IP-Shakti Sahayak" in system_prompt:
            return (
                "Under the Patents Act [chunk_patents_sec3p], Section 3(p) excludes traditional knowledge from patentability."
            )
        return "Can I patent an Ashwagandha formulation under Indian patent law?"

    async def generate_async(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        return self.generate(system_prompt, user_prompt, **kwargs)


@pytest.mark.asyncio
async def test_citation_protection_during_translation():
    """Inline [chunk_id] citation markers must be preserved verbatim during translation."""
    client = BhashiniClient(llm_provider=MockTranslationLLM())

    text = (
        "Under Patents Act [chunk_patents_sec3p], traditional knowledge is excluded. "
        "NBA approval is required [chunk_bda_sec6]."
    )

    res: TranslationResult = await client.translate_en_to_hi(text)

    assert "[chunk_patents_sec3p]" in res.translated_text
    assert "[chunk_bda_sec6]" in res.translated_text
    assert res.target_language == "hi"


@pytest.mark.asyncio
async def test_bhashini_unconfigured_fallback():
    """When Bhashini credentials are not set, client falls back to LLM translation."""
    client = BhashiniClient(llm_provider=MockTranslationLLM())

    assert client.is_bhashini_configured() is False
    res = await client.translate_hi_to_en("क्या अश्वगंधा पेटेंट योग्य है?")
    assert res.service_used == "LLM_FALLBACK"


@pytest.mark.asyncio
async def test_pipeline_hindi_query_workflow():
    """Full query pipeline with language='hi' translates input to English, runs RAG, and translates answer back."""
    mock_retriever = MagicMock(spec=HybridRetriever)
    mock_retriever.retrieve = AsyncMock(
        return_value=[
            EvidenceChunk(
                chunk_id="chunk_patents_sec3p",
                document_id="doc_patents_1970",
                corpus_collection="legal_statutory",
                text="Section 3(p) excludes traditional knowledge from patentability.",
                score=0.95,
                jurisdiction="INDIA",
                metadata={"act": "Patents Act 1970", "section": "3(p)"},
            )
        ]
    )

    pipeline = QueryPipeline(retriever=mock_retriever, llm_provider=MockTranslationLLM())

    res: QueryResult = await pipeline.query(
        question="क्या मैं अश्वगंधा उत्पाद का पेटेंट करा सकता हूँ?",
        domain_intent=DomainIntent.PATENT,
        language="hi",
        jurisdiction="INDIA",
    )

    assert res.confidence_label in ["HIGH", "MEDIUM"]
    assert len(res.citations) > 0
    assert "[chunk_patents_sec3p]" in res.answer
