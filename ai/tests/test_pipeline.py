"""Unit tests for the complete QueryPipeline and parallel RAG reasoning."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.classification.intent_classifier import DomainIntent, FineGrainedIntent
from src.context_gathering.agent import (
    ExportContextObject,
    PatentContextObject,
    MedicinalContextObject,
)
from src.reasoning.llm_provider import LLMProvider
from src.reasoning.query_pipeline import (
    Citation,
    QueryResult,
    QueryPipeline,
    SubTask,
    query,
)
from src.retrieval.hybrid_retriever import EvidenceChunk, HybridRetriever


class MockTestLLM(LLMProvider):
    """Mock LLM returning citation-annotated responses."""

    def __init__(self, response_text: str = ""):
        super().__init__(model_name="mock-model", api_key="mock-key")
        self.response_text = response_text

    def generate(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        if self.response_text:
            return self.response_text
        return (
            "Under the Patents Act 1970 [chunk_patents_act_sec3p], inventions related to traditional knowledge "
            "are excluded from patentability under Section 3(p). Furthermore, access to biological resources "
            "requires prior approval from NBA [chunk_bda_sec6]."
        )

    async def generate_async(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        return self.generate(system_prompt, user_prompt, **kwargs)


@pytest.fixture
def mock_retriever():
    """Mock HybridRetriever returning mock evidence chunks."""
    retriever = MagicMock(spec=HybridRetriever)

    async def mock_retrieve(query: str, collections: list[str], jurisdiction: str, top_k: int = 8):
        col = collections[0] if collections else "legal_statutory"
        if "standards" in col:
            return [
                EvidenceChunk(
                    chunk_id="chunk_api_ashwagandha_01",
                    document_id="doc_api_ashwagandha",
                    corpus_collection="standards_formulations",
                    text="Withania somnifera (Ashwagandha) root monograph per API Part I Vol I.",
                    jurisdiction="INDIA",
                    score=0.92,
                    metadata={"act": "Ayurvedic Pharmacopoeia of India", "monograph_id": "API-WS-01"},
                )
            ]
        elif "export" in col:
            return [
                EvidenceChunk(
                    chunk_id="chunk_eu_thmpd_01",
                    document_id="doc_eu_thmpd",
                    corpus_collection="international_export",
                    text="EU Directive 2004/24/EC establishes simplified registration for traditional herbal medicinal products.",
                    jurisdiction="EU",
                    score=0.88,
                    metadata={"treaty_name": "EU THMPD Directive 2004/24/EC", "article_number": "1"},
                )
            ]
        else:
            return [
                EvidenceChunk(
                    chunk_id="chunk_patents_act_sec3p",
                    document_id="doc_patents_act_1970",
                    corpus_collection="legal_statutory",
                    text="Section 3(p): An invention which in effect is traditional knowledge or an aggregation of known properties is not patentable.",
                    jurisdiction="INDIA",
                    score=0.95,
                    metadata={"act": "Patents Act 1970", "section": "3(p)"},
                ),
                EvidenceChunk(
                    chunk_id="chunk_bda_sec6",
                    document_id="doc_bda_2002",
                    corpus_collection="legal_statutory",
                    text="Section 6: No person shall apply for any intellectual property right without previous approval of National Biodiversity Authority.",
                    jurisdiction="INDIA",
                    score=0.90,
                    metadata={"act": "Biological Diversity Act 2002", "section": "6"},
                ),
            ]

    retriever.retrieve = AsyncMock(side_effect=mock_retrieve)
    return retriever


@pytest.mark.asyncio
async def test_pipeline_export_workflow(mock_retriever):
    """EXPORT domain intent should decompose sub-tasks across standards, statutory, and international collections."""
    pipeline = QueryPipeline(retriever=mock_retriever, llm_provider=MockTestLLM())

    context = ExportContextObject(
        herbs=["Ashwagandha (Withania somnifera)"],
        destination="European Union (EU)",
        purpose="COMMERCIAL",
        nba_approached=False,
        already_in_market=True,
    )
    question = "Can I export an Ashwagandha supplement to the European Union and what are the NBA clearance steps?"

    res: QueryResult = await pipeline.query(
        question=question,
        domain_intent=DomainIntent.EXPORT,
        context=context,
        jurisdiction="INDIA",
    )

    assert isinstance(res, QueryResult)
    assert res.confidence > 0.50
    assert res.confidence_label in ["HIGH", "MEDIUM"]
    assert any("Standards" in label for label in res.sub_tasks_run)
    assert any("Export" in label for label in res.sub_tasks_run)
    assert res.abs_assessment is not None
    assert res.sources_by_collection is not None
    assert len(res.citations) > 0


@pytest.mark.asyncio
async def test_pipeline_patent_workflow(mock_retriever):
    """PATENT domain intent should extract Section 3(p) prior art and Patents Act statutory chunks."""
    pipeline = QueryPipeline(retriever=mock_retriever, llm_provider=MockTestLLM())

    context = PatentContextObject(
        novel_aspect="Supercritical CO2 extraction process yielding concentrated bioactive withanolides",
        type="PROCESS",
        prior_art_search_needed=True,
        uses_biological_resources=True,
    )
    question = "How can a patent claim on Ashwagandha extraction overcome Section 3(p) exclusion under Indian Patents Act?"

    res: QueryResult = await pipeline.query(
        question=question,
        domain_intent=DomainIntent.PATENT,
        context=context,
        jurisdiction="INDIA",
    )

    assert res.confidence_label in ["HIGH", "MEDIUM"]
    assert any("Patents Act" in label for label in res.sub_tasks_run)
    assert "legal_statutory" in res.sources_by_collection
    assert any(c.chunk_id == "chunk_patents_act_sec3p" for c in res.citations)


@pytest.mark.asyncio
async def test_pipeline_medicinal_with_product_classification(mock_retriever):
    """MEDICINAL intent should run deterministic product classification and link result."""
    pipeline = QueryPipeline(retriever=mock_retriever, llm_provider=MockTestLLM())

    context = MedicinalContextObject(
        formulation_type="CLASSICAL",
        from_authoritative_text=True,
        new_ingredients=[],
    )
    question = "What is the manufacturing licensing pathway for classical Ayurvedic syrup under Chapter IVA?"

    res: QueryResult = await pipeline.query(
        question=question,
        domain_intent=DomainIntent.MEDICINAL,
        context=context,
        jurisdiction="INDIA",
    )

    assert res.classification is not None
    assert res.classification.category.value == "CLASSICAL_AYURVEDIC_MEDICINE"


@pytest.mark.asyncio
async def test_pipeline_insufficient_evidence_abstention():
    """When retriever returns no evidence chunks, pipeline must return explicit ABSTAIN without calling LLM."""
    empty_retriever = MagicMock(spec=HybridRetriever)
    empty_retriever.retrieve = AsyncMock(return_value=[])

    pipeline = QueryPipeline(retriever=empty_retriever, llm_provider=MockTestLLM())

    res: QueryResult = await pipeline.query(
        question="Obscure query with zero matches in corpus",
        domain_intent=DomainIntent.OTHER,
        jurisdiction="INDIA",
    )

    assert res.confidence == 0.0
    assert res.confidence_label == "ABSTAIN"
    assert res.requires_human_review is True
    assert "sufficient verified evidence" in res.answer.lower()
