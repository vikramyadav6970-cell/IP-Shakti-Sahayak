"""Core query pipeline for IP-Shakti Sahayak.

Implements the 6-stage intent-first agentic pipeline:
1. Jurisdiction resolution (T3.1)
2. Fine-grained intent classification & Qdrant collection routing (T3.2)
3. Entity extraction (T3.6)
4. Deterministic query decomposition into targeted sub-tasks (T4.1)
5. Parallel multi-collection hybrid retrieval with hard jurisdiction filtering (T2.3)
6. Deduplicated evidence assembly and abstention thresholding
7. Structured LLM synthesis with grounded inline citations (T4.1)
8. Citation extraction and validation (T4.2)
9. Confidence scoring (T4.3)
10. Safety guardrails and compliance flags (T4.4)
"""

import asyncio
from dataclasses import dataclass, field
import logging
from pathlib import Path
import re
import time
from typing import Any, Dict, List, Optional, Sequence, Union

from src.abs.abs_engine import ABSAssessmentInput, ABSAssessmentResult, assess_abs
from src.classification.intent_classifier import (
    DomainIntent,
    FineGrainedIntent,
    IntentClassificationResult,
    classify_intent,
)
from src.classification.jurisdiction_classifier import (
    JurisdictionClassificationResult,
    classify_jurisdiction,
)
from src.classification.product_classifier import (
    ProductClassificationInput,
    ProductClassificationResult,
    classify_product,
)
from src.context_gathering.agent import (
    ContextObject,
    ExportContextObject,
    MedicinalContextObject,
    PatentContextObject,
)
from src.entity_extraction.extractor import (
    EntitySet,
    IPType,
    extract_entities,
)
from src.reasoning.llm_provider import LLMProvider, get_llm_provider
from src.retrieval.hybrid_retriever import EvidenceChunk, HybridRetriever, retrieve

logger = logging.getLogger(__name__)

MIN_EVIDENCE_THRESHOLD = 1  # Minimum evidence chunks required to prevent outright abstention


@dataclass
class SubTask:
    """A targeted sub-query routed to a specific collection and jurisdiction."""

    query_text: str
    collection: str
    jurisdiction: str
    sub_task_label: str


@dataclass
class Citation:
    """A verified citation anchoring an assertion in the answer."""

    chunk_id: str
    document_id: str
    collection: str
    jurisdiction: str
    title: str
    source_url: Optional[str] = None
    section_or_ref: Optional[str] = None
    snippet: str = ""


@dataclass
class QueryResult:
    """Full response schema matching backend /api/v1/chat contract."""

    answer: str
    confidence: float
    confidence_label: str  # "HIGH" | "MEDIUM" | "LOW" | "ABSTAIN"
    classification: Optional[ProductClassificationResult] = None
    abs_assessment: Optional[ABSAssessmentResult] = None
    citations: List[Citation] = field(default_factory=list)
    requires_human_review: bool = False
    sub_tasks_run: List[str] = field(default_factory=list)
    sources_by_collection: Dict[str, List[str]] = field(default_factory=dict)
    warning_message: Optional[str] = None
    latency_ms: Optional[float] = None
    domain_intent: Optional[DomainIntent] = None
    fine_grained_intents: List[FineGrainedIntent] = field(default_factory=list)


class QueryPipeline:
    """Executes the complete multi-collection reasoning and retrieval pipeline."""

    def __init__(
        self,
        retriever: Optional[HybridRetriever] = None,
        llm_provider: Optional[LLMProvider] = None,
        prompts_dir: Optional[Union[str, Path]] = None,
    ):
        self.retriever = retriever or HybridRetriever()
        self.llm_provider = llm_provider
        if prompts_dir is not None:
            self.prompts_dir = Path(prompts_dir)
        else:
            self.prompts_dir = Path(__file__).parent.parent / "prompts" / "answer_synthesis"

        self.system_prompt_template = self._load_prompt("system_prompt.txt")
        self.user_prompt_template = self._load_prompt("user_prompt.txt")

    def _load_prompt(self, filename: str) -> str:
        p = self.prompts_dir / filename
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    async def query(
        self,
        question: str,
        domain_intent: Union[DomainIntent, str] = DomainIntent.OTHER,
        context: Optional[ContextObject] = None,
        jurisdiction: str = "INDIA",
        language: str = "en",
        conversation_history: Optional[List[Dict[str, str]]] = None,
        llm_provider: Optional[LLMProvider] = None,
    ) -> QueryResult:
        """Top-level pipeline entrypoint called by backend /api/v1/chat."""
        start_time = time.perf_counter()

        # STEP 1: Jurisdiction resolution
        jurisdiction_result: JurisdictionClassificationResult = classify_jurisdiction(
            question=question,
            ui_selected_jurisdiction=jurisdiction,
        )
        effective_jurisdiction = jurisdiction_result.effective_jurisdiction
        warning_msg = jurisdiction_result.warning_message

        # STEP 2: Intent classification & collection routing
        intent_result: IntentClassificationResult = classify_intent(
            question=question,
            ui_domain_intent=domain_intent,
        )
        target_collections = intent_result.target_collections

        # STEP 3: Entity extraction
        entity_set: EntitySet = extract_entities(context=context, question=question)

        # STEP 3b: Optional statutory rules engines (Product / ABS)
        product_classification = None
        if intent_result.domain_intent == DomainIntent.MEDICINAL or (
            isinstance(context, MedicinalContextObject)
        ):
            prod_input = ProductClassificationInput(
                product_type="MEDICINE",
                derived_from_authoritative_text=getattr(context, "from_authoritative_text", None),
                has_novel_excipients_or_actives=bool(getattr(context, "new_ingredients", None)),
                intended_use_therapeutic=True,
            )
            product_classification = classify_product(prod_input)

        abs_assessment = None
        if FineGrainedIntent.ABS in intent_result.fine_grained_intents or IPType.ABS in entity_set.ip_types:
            abs_input = ABSAssessmentInput(
                biological_resources=entity_set.biological_resources or ["Indian Medicinal Plant"],
                origin_country="INDIA",
                intending_to_apply_for_ipr=(IPType.PATENT in entity_set.ip_types),
            )
            abs_assessment = assess_abs(abs_input)

        # STEP 4: Query decomposition
        sub_tasks: List[SubTask] = self.decompose(
            intent_result=intent_result,
            entity_set=entity_set,
            context=context,
            primary_jurisdiction=effective_jurisdiction,
            question=question,
        )

        if not sub_tasks:
            sub_tasks = [
                SubTask(
                    query_text=question,
                    collection=target_collections[0] if target_collections else "legal_statutory",
                    jurisdiction=effective_jurisdiction,
                    sub_task_label="General Inquiry",
                )
            ]

        # STEP 5: Parallel multi-collection retrieval
        sub_tasks_run = [t.sub_task_label for t in sub_tasks]
        all_sub_results: List[List[EvidenceChunk]] = []

        if len(sub_tasks) == 1:
            # FAST PATH: single query
            logger.info("path=fast_path, collection=%s", sub_tasks[0].collection)
            res = await self.retriever.retrieve(
                query=sub_tasks[0].query_text,
                collections=[sub_tasks[0].collection],
                jurisdiction=sub_tasks[0].jurisdiction,
                top_k=8,
            )
            all_sub_results = [res]
        else:
            logger.info("path=decomposed, sub_task_count=%d", len(sub_tasks))
            tasks = [
                self.retriever.retrieve(
                    query=t.query_text,
                    collections=[t.collection],
                    jurisdiction=t.jurisdiction,
                    top_k=6,
                )
                for t in sub_tasks
            ]
            all_sub_results = await asyncio.gather(*tasks)

        # STEP 6: Evidence assembly & deduplication
        seen_chunk_ids = set()
        evidence_chunks: List[EvidenceChunk] = []
        sources_by_collection: Dict[str, List[str]] = {}

        for sub_res in all_sub_results:
            for chunk in sub_res:
                if chunk.chunk_id not in seen_chunk_ids:
                    seen_chunk_ids.add(chunk.chunk_id)
                    evidence_chunks.append(chunk)

                # Record sources by collection
                col = chunk.corpus_collection
                if col not in sources_by_collection:
                    sources_by_collection[col] = []
                doc_title = chunk.payload.get("act") or chunk.payload.get("source") or chunk.payload.get("treaty_name") or chunk.document_id
                if doc_title and doc_title not in sources_by_collection[col]:
                    sources_by_collection[col].append(doc_title)

        # Sort by reranker / fused score descending
        evidence_chunks.sort(key=lambda c: c.score, reverse=True)

        # Abstention check: If insufficient evidence, return explicit abstention without hallucination
        if len(evidence_chunks) < MIN_EVIDENCE_THRESHOLD:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return QueryResult(
                answer=(
                    "The authoritative legal corpus does not contain sufficient verified evidence to answer this inquiry. "
                    "Please refine your query or consult an accredited AYUSH patent attorney / regulatory expert."
                ),
                confidence=0.0,
                confidence_label="ABSTAIN",
                classification=product_classification,
                abs_assessment=abs_assessment,
                citations=[],
                requires_human_review=True,
                sub_tasks_run=sub_tasks_run,
                sources_by_collection=sources_by_collection,
                warning_message=warning_msg or "Insufficient authoritative evidence found in the verified legal corpus.",
                latency_ms=elapsed_ms,
                domain_intent=intent_result.domain_intent,
                fine_grained_intents=intent_result.fine_grained_intents,
            )

        # STEP 7: LLM synthesis
        active_llm = llm_provider or self.llm_provider or get_llm_provider()
        raw_answer, raw_citations = await self._synthesize_answer(
            llm=active_llm,
            question=question,
            domain_intent=intent_result.domain_intent,
            entity_set=entity_set,
            sub_tasks=sub_tasks,
            evidence_chunks=evidence_chunks,
            language=language,
        )

        # STEP 8: Citation validation (zero-hallucination check)
        from src.citations.validator import validate_citations
        validation_result = validate_citations(
            raw_answer=raw_answer,
            evidence_chunks=evidence_chunks,
        )
        answer = validation_result.cleaned_answer
        citations = validation_result.valid_citations or raw_citations

        # STEP 9: Composite confidence scoring (Rule 4)
        from src.confidence.scorer import compute_confidence
        sub_tasks_with_evidence_count = sum(1 for sub_res in all_sub_results if len(sub_res) > 0)
        confidence_breakdown = compute_confidence(
            evidence_chunks=evidence_chunks,
            validation_result=validation_result,
            total_sub_tasks=len(sub_tasks),
            sub_tasks_with_evidence=sub_tasks_with_evidence_count,
            jurisdiction_mismatch=jurisdiction_result.mismatch_detected,
            is_export_cross_border=jurisdiction_result.is_export_query,
            raw_answer=answer,
        )

        confidence = confidence_breakdown.composite_score
        confidence_label = confidence_breakdown.confidence_label
        requires_human_review = (
            confidence_breakdown.requires_human_review
            or (product_classification and product_classification.category.value == "UNCLEAR")
        )

        # STEP 10: Guardrails & Compliance Enforcer (Rule 6, Rule 8)
        from src.guardrails.rules import apply_guardrails
        guardrail_result = apply_guardrails(
            raw_answer=answer,
            evidence_chunks=evidence_chunks,
            jurisdictions=entity_set.jurisdictions,
        )
        final_answer = guardrail_result.sanitized_answer
        if guardrail_result.is_abstaining:
            confidence = 0.0
            confidence_label = "ABSTAIN"
            requires_human_review = True

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return QueryResult(
            answer=final_answer,
            confidence=round(confidence, 2),
            confidence_label=confidence_label,
            classification=product_classification,
            abs_assessment=abs_assessment,
            citations=citations,
            requires_human_review=requires_human_review,
            sub_tasks_run=sub_tasks_run,
            sources_by_collection=sources_by_collection,
            warning_message=warning_msg,
            latency_ms=round(elapsed_ms, 2),
            domain_intent=intent_result.domain_intent,
            fine_grained_intents=intent_result.fine_grained_intents,
        )

    def decompose(
        self,
        intent_result: IntentClassificationResult,
        entity_set: EntitySet,
        context: Optional[ContextObject],
        primary_jurisdiction: str,
        question: str,
    ) -> List[SubTask]:
        """Deterministically decompose query into targeted collection sub-tasks (Rule 14)."""
        sub_tasks: List[SubTask] = []
        target_collections = intent_result.target_collections

        # 1. Standards & Formulations Collection
        if "standards_formulations" in target_collections:
            if entity_set.herbs:
                # Generate one sub-task per herb
                for herb in entity_set.herbs:
                    sub_tasks.append(
                        SubTask(
                            query_text=f"botanical monograph, identity, quality standards, and classical Ayurvedic references for {herb}",
                            collection="standards_formulations",
                            jurisdiction="INDIA",
                            sub_task_label=f"Standards & Monograph: {herb}",
                        )
                    )
            else:
                sub_tasks.append(
                    SubTask(
                        query_text=f"classical Ayurvedic formulations and pharmacopoeial monograph standards for {question}",
                        collection="standards_formulations",
                        jurisdiction="INDIA",
                        sub_task_label="Standards & Monographs",
                    )
                )

        # 2. Legal & Statutory Collection
        if "legal_statutory" in target_collections:
            if IPType.PATENT in entity_set.ip_types:
                sub_tasks.append(
                    SubTask(
                        query_text="Section 3(p) traditional knowledge exclusion, Section 3(d) enhancement of efficacy, Section 3(e) synergistic combinations, and Section 10(4) biological source disclosure under Patents Act 1970",
                        collection="legal_statutory",
                        jurisdiction="INDIA",
                        sub_task_label="Patents Act 1970 & Section 3(p)",
                    )
                )

            if IPType.ABS in entity_set.ip_types or FineGrainedIntent.ABS in intent_result.fine_grained_intents:
                sub_tasks.append(
                    SubTask(
                        query_text="Biological Diversity Act 2002 Section 3 foreign access, Section 6 IPR mandate, Section 7 SBB intimation, and 2023 Amendment exemptions",
                        collection="legal_statutory",
                        jurisdiction="INDIA",
                        sub_task_label="Biological Diversity Act & ABS Mandate",
                    )
                )

            if IPType.TRADEMARK in entity_set.ip_types:
                sub_tasks.append(
                    SubTask(
                        query_text="Trade Marks Act 1999 Section 9 absolute grounds for refusal, descriptive Ayurvedic terms, and Class 5/3/30 classification",
                        collection="legal_statutory",
                        jurisdiction="INDIA",
                        sub_task_label="Trade Marks Act & Class Classification",
                    )
                )

            if IPType.DRUG_REGULATION in entity_set.ip_types or IPType.FOOD_REGULATION in entity_set.ip_types:
                sub_tasks.append(
                    SubTask(
                        query_text="Drugs and Cosmetics Act 1940 Chapter IVA classical Form 24D vs proprietary Rule 158B licensing and FSSAI Ayurveda Aahara Regulations 2022",
                        collection="legal_statutory",
                        jurisdiction="INDIA",
                        sub_task_label="Drug Licensing & Ayurveda Aahara",
                    )
                )

            if not any(
                t.collection == "legal_statutory" for t in sub_tasks
            ):
                sub_tasks.append(
                    SubTask(
                        query_text=f"Indian statutory and regulatory provisions governing {question}",
                        collection="legal_statutory",
                        jurisdiction="INDIA",
                        sub_task_label="Statutory Regulations",
                    )
                )

        # 3. International & Export Collection
        if "international_export" in target_collections:
            dest = entity_set.destination_country or ("EU" if "EU" in primary_jurisdiction else "INTERNATIONAL")
            sub_tasks.append(
                SubTask(
                    query_text=f"{dest} regulatory framework, EU THMPD 2004/24/EC, US FDA DSHEA 1994, WIPO GRATK Treaty, and export quality controls",
                    collection="international_export",
                    jurisdiction=dest if dest in ["EU", "USA"] else "INTERNATIONAL",
                    sub_task_label=f"International Export Compliance ({dest})",
                )
            )

        # 4. Procedural Forms Collection
        if "procedural_forms" in target_collections:
            sub_tasks.append(
                SubTask(
                    query_text="NBA Form I access application, NBA Form III patent IPR approval, SBB prior intimation checklist, and Form 24D manufacturing application",
                    collection="procedural_forms",
                    jurisdiction="INDIA",
                    sub_task_label="Procedural Licensing & Forms",
                )
            )

        # 5. Case Law & Prior Art Collection
        if "case_law_prior_art" in target_collections:
            sub_tasks.append(
                SubTask(
                    query_text="CSIR TKDL prior art revocation precedents, turmeric patent revocation, neem patent case, and traditional knowledge anticipation",
                    collection="case_law_prior_art",
                    jurisdiction="INDIA",
                    sub_task_label="Prior Art & Landmark Case Law",
                )
            )

        # Enforce max 6 sub-tasks limit by merging sub-tasks in same collection if necessary
        if len(sub_tasks) > 6:
            merged: Dict[str, SubTask] = {}
            for t in sub_tasks:
                if t.collection not in merged:
                    merged[t.collection] = t
                else:
                    merged[t.collection].query_text += f" | {t.query_text}"
                    merged[t.collection].sub_task_label += f" + {t.sub_task_label}"
            sub_tasks = list(merged.values())

        return sub_tasks

    async def _synthesize_answer(
        self,
        llm: LLMProvider,
        question: str,
        domain_intent: DomainIntent,
        entity_set: EntitySet,
        sub_tasks: List[SubTask],
        evidence_chunks: List[EvidenceChunk],
        language: str,
    ) -> tuple[str, List[Citation]]:
        """Format prompt and call LLM for citation-anchored answer synthesis."""
        # Group evidence text with chunk IDs for citation anchoring
        evidence_lines = []
        evidence_by_id: Dict[str, EvidenceChunk] = {}

        for c in evidence_chunks:
            evidence_by_id[c.chunk_id] = c
            citation_tag = f"[{c.chunk_id}]"
            src_info = f"Collection: {c.corpus_collection} | Jurisdiction: {c.jurisdiction}"
            if c.payload.get("act"):
                src_info += f" | Act: {c.payload['act']}"
            if c.payload.get("section"):
                src_info += f" Sec {c.payload['section']}"

            evidence_lines.append(f"--- EVIDENCE ITEM {citation_tag} ({src_info}) ---\n{c.text}\n")

        evidence_text = "\n".join(evidence_lines)

        user_content = self.user_prompt_template.format(
            question=question,
            domain_intent=domain_intent.value,
            herbs=", ".join(entity_set.herbs) if entity_set.herbs else "None specified",
            jurisdictions=", ".join(entity_set.jurisdictions),
            ip_types=", ".join(t.value for t in entity_set.ip_types),
            formulation_name=entity_set.formulation_name or "None",
            destination_country=entity_set.destination_country or "Domestic (India)",
            evidence_blocks=evidence_text,
        )

        try:
            raw_response = await llm.generate_async(
                system_prompt=self.system_prompt_template,
                user_prompt=user_content,
                temperature=0.1,
                max_tokens=2048,
            )
        except Exception as e:
            logger.warning("Live LLM generation failed (%s); generating structured deterministic response from evidence.", e)
            raw_response = self._fallback_synthesis(question, evidence_chunks)

        # Extract and validate citations
        citations = self._extract_citations(raw_response, evidence_by_id)

        # Fallback citation anchoring if LLM omitted inline tags
        if not citations and evidence_chunks:
            for c in evidence_chunks[:3]:
                citations.append(
                    Citation(
                        chunk_id=c.chunk_id,
                        document_id=c.document_id,
                        collection=c.corpus_collection,
                        jurisdiction=c.jurisdiction,
                        title=c.payload.get("act") or c.payload.get("source") or c.payload.get("treaty_name") or c.document_id,
                        section_or_ref=str(c.payload.get("section") or c.payload.get("article_number") or ""),
                        snippet=c.text[:200],
                    )
                )

        return raw_response, citations

    def _extract_citations(
        self,
        text: str,
        evidence_by_id: Dict[str, EvidenceChunk],
    ) -> List[Citation]:
        """Extract all valid [chunk_id] citation markers matching provided evidence."""
        found_citations: List[Citation] = []
        seen_ids = set()

        matches = re.findall(r"\[([a-zA-Z0-9_\-\.\:\/]+)\]", text)
        for chunk_id in matches:
            if chunk_id in evidence_by_id and chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                chunk = evidence_by_id[chunk_id]
                found_citations.append(
                    Citation(
                        chunk_id=chunk.chunk_id,
                        document_id=chunk.document_id,
                        collection=chunk.corpus_collection,
                        jurisdiction=chunk.jurisdiction,
                        title=chunk.payload.get("act") or chunk.payload.get("source") or chunk.payload.get("treaty_name") or chunk.document_id,
                        section_or_ref=str(chunk.payload.get("section") or chunk.payload.get("article_number") or ""),
                        snippet=chunk.text[:250],
                    )
                )

        return found_citations

    def _compute_confidence(
        self,
        evidence_chunks: List[EvidenceChunk],
        citations: List[Citation],
    ) -> float:
        """Compute grounded confidence score based on retrieval scores and citation density."""
        if not evidence_chunks:
            return 0.0

        avg_score = sum(c.score for c in evidence_chunks[:4]) / min(len(evidence_chunks), 4)
        citation_factor = min(len(citations) / 2.0, 1.0)

        # Baseline confidence normalized
        raw_conf = (0.5 * avg_score) + (0.5 * citation_factor)
        return min(max(raw_conf, 0.20), 0.98)

    def _fallback_synthesis(
        self,
        question: str,
        evidence_chunks: List[EvidenceChunk],
    ) -> str:
        """Deterministic synthesis used when LLM endpoint is offline or in mock test mode."""
        lines = [
            f"### Regulatory & IP Advisory for: {question}",
            "",
            "Based on the verified statutory and pharmacopoeial corpus, here are the key legal requirements:",
            "",
        ]

        for i, c in enumerate(evidence_chunks[:4], 1):
            act_name = c.payload.get("act") or c.payload.get("source") or c.payload.get("treaty_name") or c.document_id
            sec = f" (Section {c.payload['section']})" if c.payload.get("section") else ""
            lines.append(f"**{i}. {act_name}{sec}** [{c.chunk_id}]:")
            lines.append(f"> {c.text.strip()}")
            lines.append("")

        lines.append(
            "*Disclaimer: This AI-generated synthesis is for informational guidance only and does not constitute formal legal advice.*"
        )
        return "\n".join(lines)


# Module-level convenience query function
default_pipeline = QueryPipeline()


async def query(
    question: str,
    domain_intent: Union[DomainIntent, str] = DomainIntent.OTHER,
    context: Optional[ContextObject] = None,
    jurisdiction: str = "INDIA",
    language: str = "en",
    conversation_history: Optional[List[Dict[str, str]]] = None,
    llm_provider: Optional[LLMProvider] = None,
) -> QueryResult:
    """Execute query through the IP-Shakti Sahayak query pipeline."""
    return await default_pipeline.query(
        question=question,
        domain_intent=domain_intent,
        context=context,
        jurisdiction=jurisdiction,
        language=language,
        conversation_history=conversation_history,
        llm_provider=llm_provider,
    )
