# ai/status.md

Granular status log + the authoritative record of interfaces/function signatures
the backend calls into (e.g. the ingestion task signature, the query pipeline
entrypoint). Populate as you go — don't make backend guess your function shapes.

---

## Interfaces backend depends on

```python
# T2.3 Core Multi-Collection Retrieval Primitive (async for parallel sub-task execution):
from src.retrieval.hybrid_retriever import EvidenceChunk, retrieve

async def retrieve(
    query: str,
    collections: list[str],
    jurisdiction: str,        # HARD filter at Qdrant query level: "INDIA" | "INTERNATIONAL" | "EU" | "USA"
    top_k: int = 8,
) -> list[EvidenceChunk]

# T3.1 Jurisdiction Classifier:
from src.classification.jurisdiction_classifier import JurisdictionClassificationResult, classify_jurisdiction

def classify_jurisdiction(
    question: str,
    ui_selected_jurisdiction: str = "INDIA",
) -> JurisdictionClassificationResult

# T3.2 Intent Classifier & Collection Router:
from src.classification.intent_classifier import (
    DomainIntent,
    FineGrainedIntent,
    IntentClassificationResult,
    classify_intent,
)

def classify_intent(
    question: str,
    ui_domain_intent: str | DomainIntent | None = None,
) -> IntentClassificationResult

# T3.3 Product Classifier Rules Engine:
from src.classification.product_classifier import (
    ProductCategory,
    ProductClassificationInput,
    ProductClassificationResult,
    classify_product,
)

def classify_product(
    inputs: ProductClassificationInput,
) -> ProductClassificationResult

# T3.4 ABS Assessment Engine (called by backend T4.2):
from src.abs.abs_engine import (
    ABSRelevance,
    ApplicantType,
    AccessPurpose,
    ABSAssessmentInput,
    ABSAssessmentResult,
    assess_abs,
)

def assess_abs(
    inputs: ABSAssessmentInput,
) -> ABSAssessmentResult

# T3.5 Context Gathering Agent & Answer Parser (called by backend /api/v1/context):
from src.context_gathering.agent import (
    AnswerType,
    ContextQuestion,
    ExportContextObject,
    PatentContextObject,
    MedicinalContextObject,
    BusinessContextObject,
    ResearchContextObject,
    OtherContextObject,
    ContextObject,
    get_context_questions,
    parse_context_answers,
)

def get_context_questions(domain_intent: DomainIntent | str) -> list[ContextQuestion]
def parse_context_answers(domain_intent: DomainIntent | str, raw_answers: dict) -> ContextObject

# T3.6 Entity Extractor (called by Query Decomposer in T4.1):
from src.entity_extraction.extractor import (
    IPType,
    EntitySet,
    EntityExtractor,
    extract_entities,
)

def extract_entities(
    context: ContextObject | None = None,
    question: str = "",
) -> EntitySet
```

---

## ContextObject Schemas (API Contract with Frontend & Backend)

Cross-part schemas for structured context gathered from the user before retrieval:

1. **`EXPORT`** (`ExportContextObject`):
   ```python
   {
       "herbs": list[str],                # e.g., ["Withania somnifera", "Ocimum sanctum"]
       "destination": str,                # e.g., "European Union (EU)", "United States (USA)"
       "purpose": "COMMERCIAL" | "RESEARCH",
       "nba_approached": bool,
       "already_in_market": bool,
   }
   ```
2. **`PATENT`** (`PatentContextObject`):
   ```python
   {
       "novel_aspect": str,               # Specific technological advancement
       "type": "HERB" | "FORMULATION" | "PROCESS",
       "prior_art_search_needed": bool,
       "uses_biological_resources": bool,
   }
   ```
3. **`MEDICINAL`** (`MedicinalContextObject`):
   ```python
   {
       "formulation_type": "CLASSICAL" | "PROPRIETARY" | "UNKNOWN",
       "from_authoritative_text": bool,
       "new_ingredients": list[str],
   }
   ```
4. **`BUSINESS`** (`BusinessContextObject`):
   ```python
   {
       "product_type": str,               # e.g., "Ayurvedic Medicine (Class 5)"
       "brand_name": str | None,
       "target_market": "INDIA" | "INTERNATIONAL" | "BOTH",
   }
   ```
5. **`RESEARCH`** (`ResearchContextObject`):
   ```python
   {
       "research_type": "CLINICAL" | "PHYTOCHEMICAL" | "IP",
       "biological_resources": bool,
       "publish_internationally": bool,
   }
   ```
6. **`OTHER`** (`OtherContextObject`):
   ```python
   {
       "free_description": str,           # Unstructured free text description
   }
   ```

---

## Corpus manifest

Full authoritative manifest created at [`ai/data/corpus/manifest.md`](data/corpus/manifest.md):
- **Total documents**: 42 curated sources across 5 collections:
  - `legal_statutory` (16 documents): Indian Patents Act 1970 (Sec 3(p), 3(d), 3(e), 10(4), 25, 64), Patents Rules 2024, Trade Marks Act 1999, GI Act 1999, Biological Diversity Act 2002 (2023 amendment), BD Rules 2024, NBA ABS Guidelines 2014, Drugs and Cosmetics Act 1940 (Chapter IVA), Drugs Rules 1945 (Part XVI-XIX), FSSAI Ayurveda Aahara Regs 2022, Designs Act 2000, CSIR-TKDL Public Policy Framework.
  - `standards_formulations` (7 documents): Ayurvedic Pharmacopoeia of India (API Part I Single Drugs Vols I-IX), Ayurvedic Formulary of India (AFI Part I-III Classical Formulations), First Schedule list of 54 Authoritative Treatises, PCIM&H Testing Standards & Quality Parameters, CCRAS Phytochemical SOPs.
  - `procedural_forms` (8 documents): NBA Form I (Access), NBA Form II (Transfer of Research), NBA Form III (IPR Approval), NBA Form IV (Third-party transfer), SBB Prior Intimation Checklist, Form 24D (Manufacturing License), Form 24E (Loan License), CCPA AYUSH Advertising Checklist.
  - `international_export` (8 documents): WTO TRIPS Agreement (Art 27, 28, 29), CBD 1992 (Art 8(j), 15), Nagoya Protocol 2010, WIPO GRATK Treaty 2024 (Art 3 mandatory genetic resource disclosure), EU THMPD Directive 2004/24/EC, EU Food Supplement Regulation (EC) 1924/2006, US DSHEA 1994 / 21 CFR 111, CITES Appendices on medicinal plants.
  - `case_law_prior_art` (3 dossiers): Landmark CSIR/India TKDL revocation dossiers (Turmeric US 5,401,504, Neem EPO 0436257, Basmati US 5,663,484).

## Qdrant Payload Schemas per Collection

All 5 collections created on Qdrant Cloud with `vector_size=1024`, `distance=Cosine`.
Payload fields are stored directly at the top level for efficient metadata filtering:

1. **`legal_statutory`**:
   `{ chunk_id: str, document_id: str, corpus_collection: "legal_statutory", text: str, token_count: int, jurisdiction: "INDIA", act: str, chapter: str, section: str | null, subsection: str | null, document_version: str, authority: str }`
2. **`standards_formulations`**:
   `{ chunk_id: str, document_id: str, corpus_collection: "standards_formulations", text: str, token_count: int, jurisdiction: "INDIA", source: str, monograph_id: str, formulation_name: str, botanical_name: str | null, substance_type: str, parent_chunk_id: str | null }`
3. **`case_law_prior_art`**:
   `{ chunk_id: str, document_id: str, corpus_collection: "case_law_prior_art", text: str, token_count: int, jurisdiction: str, case_name: str, court: str, year: str, citation_ref: str, paragraph_index: int }`
4. **`procedural_forms`**:
   `{ chunk_id: str, document_id: str, corpus_collection: "procedural_forms", text: str, token_count: int, jurisdiction: "INDIA", form_name: str, section_heading: str, authority: str, governing_law: str }`
5. **`international_export`**:
   `{ chunk_id: str, document_id: str, corpus_collection: "international_export", text: str, token_count: int, jurisdiction: "INTERNATIONAL" | "EU" | "USA", treaty_name: str, article_number: str | null, paragraph: str | null, authority: str }`

---

## Log

### T3.6 — Entity extractor (2026-08-28)
Implemented `src/entity_extraction/extractor.py` and curated lookup table `ai/data/herb_names.yaml`:
- `EntityExtractor` and `extract_entities()` resolving botanical Latin binomials from vernacular/Sanskrit/common names across 35+ Ayurvedic herbs.
- Canonical jurisdiction extraction (`INDIA`, `EU`, `USA`, `UK`, `INTERNATIONAL`) always enforcing domestic Indian compliance.
- Extracts `IPType` enum values (`PATENT`, `TRADEMARK`, `GI`, `ABS`, `EXPORT`, `DRUG_REGULATION`, `FOOD_REGULATION`).
- Returns structured `EntitySet` (herbs, jurisdictions, ip_types, biological_resources, formulation_name, destination_country, regulatory_regime).
- Tested in `ai/tests/test_entity_extraction.py` (100% pass).
**Phase 3 complete!** All 6 classification, context gathering, and entity extraction tasks are verified.

### T3.5 — Context gathering agent (2026-08-28)
Implemented `src/context_gathering/agent.py` and versioned templates in `src/prompts/context_questions/`:
- `ContextGatheringAgent` pre-loads versioned YAML templates for all 6 domain intents (`BUSINESS`, `EXPORT`, `MEDICINAL`, `PATENT`, `RESEARCH`, `OTHER`) at startup.
- Exposes `get_context_questions()` returning structured `ContextQuestion` list with options, required flags, and answer types (`FREE_TEXT`, `SINGLE_SELECT`, `MULTI_SELECT`).
- Exposes `parse_context_answers()` returning strictly typed `ContextObject` dataclasses for entity extraction and query decomposition.
- Tested in `ai/tests/test_context_gathering.py` (100% pass).
Next task: Phase 3, T3.6 (`src/entity_extraction/extractor.py`).

### T3.4 — ABS assessment engine (2026-08-28)
Implemented `src/abs/abs_engine.py`:
- `ABSEngine` and `assess_abs()` implementing deterministic statutory rules under Biological Diversity Act 2002, 2023 Amendment Act, and 2024 Rules.
- Classifies ABS relevance (`HIGH`, `MEDIUM`, `LOW`, `NOT_APPLICABLE`).
- Resolves mandatory approval pathways: Section 6 IPR mandate (NBA Form III), Section 3 foreign access (NBA Form I), Section 4 research transfer (NBA Form II), Section 20 third-party transfer (NBA Form IV), and Section 7 Indian commercial manufacturing (SBB Prior Intimation).
- Encodes 2023 Amendment statutory exemptions (Registered Ayush practitioners, cultivated sources, and Section 40 Normally Traded Commodities).
- Returns benefit-sharing percentages and ordered action checklists.
- Tested across all statutory pathways in `ai/tests/test_abs.py` (100% pass).
Next task: Phase 3, T3.5 (`src/context_gathering/agent.py`).

### T3.3 — Deterministic product classifier rules engine (2026-08-28)
Implemented `src/classification/product_classifier.py`:
- `ProductClassifier` and `classify_product()` implementing an explicit, auditable statutory rules engine (no stochastic LLM inference).
- Encodes all statutory product categories: `CLASSICAL_AYURVEDIC_MEDICINE`, `PROPRIETARY_MEDICINE`, `NEW_NON_CLASSICAL_DRUG`, `PHYTOPHARMACEUTICAL`, `AYURVEDA_AAHARA`, `COSMETIC`, `UNCLEAR`.
- Encodes strict FSSAI Ayurveda Aahara 2022 food-vs-drug boundaries (prohibits synthetic vitamins/minerals and disease cure claims).
- Returns category, confidence, regulatory pathway, governing acts/rules, required licensing forms (Form 24D, Form 32, FSSAI), statutory authority, and full auditable `rules_fired` trail.
- Tested across all rule branches and edge cases in `ai/tests/test_classification.py` (100% pass).
Next task: Phase 3, T3.4 (`src/abs/abs_engine.py`).

### T3.2 — Two-level intent classifier (2026-08-28)
Implemented `src/classification/intent_classifier.py`:
- Level 1 UI Domain Intent (`BUSINESS`, `EXPORT`, `MEDICINAL`, `PATENT`, `RESEARCH`, `OTHER`) mapped directly from user selection or inferred.
- Level 2 Fine-Grained Legal Intents (`PATENT`, `TRADEMARK`, `GI`, `ABS`, `TKDL`, `DRUG_REGULATION`, `FOOD_REGULATION`, `EXPORT`, etc.) inferred from query text.
- Encodes coding_conventions.md Rule 11 mapping from intent to Qdrant target collections (`INTENT_TO_COLLECTIONS_MAP`).
- Tested across all 6 domain intents in `ai/tests/test_classification.py` (100% pass).
Next task: Phase 3, T3.3 (`src/classification/product_classifier.py`).

### T3.1 — Jurisdiction classifier (2026-08-28)
Implemented `src/classification/jurisdiction_classifier.py`:
- `JurisdictionClassifier` and `classify_jurisdiction()` resolving concrete jurisdiction filter values (`INDIA`, `USA`, `EU`, `INTERNATIONAL`).
- Respects UI jurisdiction toggle as primary ground truth, with explicit mismatch detection when question mentions foreign authorities (US FDA, EU THMPD, WIPO).
- Detects cross-border export intent (`is_export_query=True`, `target_export_country`).
- Tested in `ai/tests/test_classification.py` (100% pass).
Next task: Phase 3, T3.2 (`src/classification/intent_classifier.py`).

### T2.3 — Hybrid retrieval + reranking (2026-08-28)
Implemented `src/retrieval/hybrid_retriever.py`:
- `HybridRetriever` and `async def retrieve(query, collections, jurisdiction, top_k)` primitive.
- Hard jurisdiction filter applied directly at the Qdrant query level (`models.Filter(must=[FieldCondition(key="jurisdiction", match=...)])`).
- Reciprocal Rank Fusion (RRF with $k=60$) combining Qdrant dense vector search and BM25 sparse keyword search across specified collections.
- Optional Cohere Rerank (`rerank-v3.5`) support with graceful RRF passthrough fallback.
- Tested in `ai/tests/test_retrieval.py`:
  - Verified `jurisdiction="INDIA"` never leaks `jurisdiction="USA"` chunks.
  - Verified `asyncio.gather()` parallel sub-task retrieval across multiple collections (`legal_statutory`, `standards_formulations`).
Next task: Phase 3, T3.1 (`src/classification/jurisdiction_classifier.py`).

### T2.2 — BM25 keyword search index (2026-08-28)
Implemented `src/retrieval/keyword_search.py`:
- `legal_tokenize()` preserving legal section references (`Section 3(p)`, `10(4)(d)(ii)`, `27.3(b)`), botanical names, and Devanagari Hindi tokens.
- `BM25Index` wrapping `rank_bm25` (BM25Plus) with `build_index()`, `load_index()`, and `search(query, collection, top_k)`.
- Full persistence to disk via pickle serialization.
- Verified in `ai/tests/test_retrieval.py` that "Section 3(p)" queries cleanly retrieve Section 3(p) chunks with highest relevance score, and collection filtering works correctly.
Next task: Phase 2, T2.3 (`src/retrieval/hybrid_retriever.py`).

### T2.1 — Embedding generation + Qdrant Cloud indexing (2026-08-28)
Implemented `src/embeddings/indexer.py`:
- `QdrantIndexer` class with `ensure_collections()`, `index_chunks()`, `search()`, and `get_collection_stats()`.
- Provisioned all 5 collections (`legal_statutory`, `standards_formulations`, `case_law_prior_art`, `procedural_forms`, `international_export`) on live Qdrant Cloud cluster with 1024-dim Cosine vectors.
- Verified batch embedding with `BAAI/bge-m3` and payload metadata flattening across multiple collections in `ai/tests/test_embeddings.py` (100% pass).
Next task: Phase 2, T2.2 (`src/retrieval/bm25_search.py`).

### T1.3 — Collection-aware chunking (2026-08-28)
Implemented `src/ingestion/chunker.py`:
- Base `BaseChunkingStrategy` interface and `chunk_document()` dispatcher routing by `corpus_collection`.
- 5 Concrete strategy implementations:
  1. `LegalStatutoryChunker` (`legal_statutory`): Act -> Chapter -> Section -> Subsection hierarchy. Emits section and standalone clause chunks (Section 3(p), Section 10(4)(d)(ii)) with full statutory metadata.
  2. `StandardsFormulationsChunker` (`standards_formulations`): Monograph/formulation level chunks; child chunks for analytical testing standards linked via `parent_chunk_id`.
  3. `CaseLawChunker` (`case_law_prior_art`): Paragraph-level chunks with case name, court, year, and citation reference pinned to every chunk.
  4. `ProceduralFormsChunker` (`procedural_forms`): Form section / field-group level chunks with authority and governing act metadata.
  5. `InternationalExportChunker` (`international_export`): Treaty -> Article -> Paragraph chunks with international jurisdiction.
- Full test coverage in `ai/tests/test_ingestion.py` covering all 5 strategies and dispatcher routing.
Next task: Phase 2, T2.1 (`src/embeddings/qdrant_indexer.py`).

### T1.2 — Parsing pipeline (2026-08-28)
Implemented `src/ingestion/parser.py`:
- `DocumentParser` and convenience `parse_document()` handling PDF (PyMuPDF with pypdf fallback), HTML (BeautifulSoup with script/nav/footer cleaning), JSON/JSONL, and plain text/Markdown.
- Generates normalized intermediate representation `ParsedDocument` containing:
  `document_id`, `title`, `corpus_collection`, `jurisdiction`, `document_type`, `raw_text`, `sections` (with structural markers: chapters, sections, rules, articles, forms), and `metadata`.
- Tested in `ai/tests/test_ingestion.py` against statutory text, HTML regulations, synthetic PDFs, and seed JSONL datasets (100% passing).
Next task: Phase 1, T1.3 (`src/ingestion/chunker.py`).

### T1.1 — Curate initial corpus manifest (2026-08-28)
Assembled comprehensive manifest at [`ai/data/corpus/manifest.md`](data/corpus/manifest.md):
- 42 authoritative source documents mapped across all 5 Qdrant Cloud collections.
- Full legal metadata included: Document ID, Jurisdiction, Document Type, Issuing Authority, Governing Law/Sections, Official Source URLs, and Verification Status.
- Strict compliance with hard constraints: No scraping of restricted TKDL database; First Schedule classical treatises explicitly indexed as authority for product classification.
Next task: Phase 1, T1.2 (`src/ingestion/parser.py`).

### T0.3 — Embedding model smoke test (2026-08-28)
Implemented `src/embeddings/embedding_provider.py`:
- `EmbeddingProvider` abstract base class with batch `embed(texts)` and single-query `embed_query(text)`.
- `BGEM3EmbeddingProvider` wrapping `BAAI/bge-m3` via `sentence-transformers` with normalized output embeddings.
- Vector dimension is confirmed **1024** (multilingual dense embeddings, strong across Hindi + English).
- Live smoke test in `ai/tests/test_embeddings.py` verified against real model with English and Hindi sentences.
- **Cross-part note:** All 5 Qdrant Cloud collections in T2.1 must be created with `vector_size=1024` and `distance=Cosine`.
Next task: Phase 1, T1.1 (Corpus curation manifest across 5 collections).

### T0.2 — LLM provider abstraction (2026-08-28)
Implemented `src/reasoning/llm_provider.py`:
- `LLMProvider` abstract base class with sync `generate()` and async `generate_async()`.
- Concrete implementations:
  - `GeminiProvider`: Supports modern `google-genai` SDK, legacy `google.generativeai`, and direct REST API fallback.
  - `OpenAIProvider`: Supports standard and async `openai` SDK.
  - `AnthropicProvider`: Supports standard and async `anthropic` SDK.
- Factory `get_llm_provider(provider, model, api_key)` reading env vars `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`.
- Test suite in `ai/tests/test_reasoning.py` verified with mock parameter tests and live smoke test.
Next task: Phase 0, T0.3 (`src/embeddings/embedding_provider.py`).

### T0.1 — Project scaffold & cloud env setup (2026-08-28)
Scaffolded the `ai/` project:
- Created `ai/.env.example` with clear instructions & signup links for Qdrant Cloud, Supabase Postgres, Upstash Redis, LLM providers (Gemini/OpenAI/Anthropic), Cohere rerank (optional), and Neo4j AuraDB (optional).
- Created `ai/requirements.txt` with exact pinned dependencies.
- Created `ai/pytest.ini` with test paths and smoke/slow markers.
- Created `ai/src/` modular layout: `config.py` (pydantic-settings), `ingestion`, `embeddings`, `retrieval`, `classification`, `context_gathering`, `entity_extraction`, `abs`, `reasoning`, `citations`, `confidence`, `guardrails`, `multilingual`, `evaluation`, and versioned `prompts/`.
- Created `ai/tests/` skeleton with `test_config.py` passing unit checks.

### (seed dataset added — prior work)
Added `ai/data/corpus/seed/` (verified legal_knowledge, ipr_prior_art, ayush_tk
records + loader script) and `ai/tests/eval/questions_seed.jsonl` in response to
a request to build an embeddable dataset. Every record carries a
`verification_status` field distinguishing verified-facts-paraphrased-text from
verified-core-facts-some-fields-unconfirmed — read `ai/data/corpus/seed/README.md`
before treating any of it as citation-ready without the flagged confirmations.
Next task: Phase 0, T0.1 in `prompts/phases.md` (or run `load_seed.py` once T0.3's
embedding setup exists, to fast-track a working retrieval demo on real content).
