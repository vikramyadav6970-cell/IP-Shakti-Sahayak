# ai/prompts/phases.md

Ready-to-paste prompts for an AI coding agent, one per task. This is the most
domain-sensitive part of the project — every task prompt below tells the agent to
re-read `context.md` §2 and `ai/coding_conventions.md` because getting these wrong
silently produces a system that looks like it works but fabricates law. Don't skip
that instruction when pasting these.

**Cloud stack reminder (read before every task):**
- Vector store → **Qdrant Cloud** (5 collections: `legal_statutory`,
  `standards_formulations`, `case_law_prior_art`, `procedural_forms`,
  `international_export`). See `context.md §3a` for the full table.
- Relational DB → **Supabase** (Postgres). `DATABASE_URL` env var.
- Cache / broker → **Upstash Redis**. `REDIS_URL` env var.
- No Docker, no local service containers.

**Primary pipeline (read before every task):**
The core user flow is intent-first → context gathering → entity extraction +
query decomposition → parallel multi-collection RAG → evidence assembly →
LLM synthesis. See `context.md §1` and `§3b` for the full flow and intent→collection
mapping. Tasks in Phase 3 build the new stages; T4.1 wires them all together.

---

## Phase 0 — Environment & setup

### T0.1 — Project scaffold & cloud env setup

**Manual prerequisite:**
1. Python 3.11+ installed.
2. Create a **Qdrant Cloud** account at cloud.qdrant.io — create a cluster (free
   tier is fine). Copy the cluster URL and API key to your `.env`.
3. Create a **Supabase** project at supabase.com — copy the **transaction-mode
   pooler** connection string (Supabase dashboard → Project Settings → Database →
   Connection string → Transaction mode) as `DATABASE_URL`.
4. Create an **Upstash Redis** database at console.upstash.com — copy the
   `rediss://` URL (Upstash console → Details → Redis URL) as `REDIS_URL`.
5. Get an LLM API key for at least one provider (Anthropic / OpenAI / Google).

**Prompt:**
```
Read /context.md, /process.md, and /ai/coding_conventions.md in full first.

Task: Scaffold the `ai/` Python project per the folder structure documented in
ai/coding_conventions.md. Include requirements.txt pinning exact versions of every
dependency named in that file's Stack section (and nothing beyond it without
flagging why):
  - qdrant-client
  - sentence-transformers (for BAAI/bge-m3)
  - rank_bm25
  - redis (redis-py, for Upstash)
  - celery
  - sqlalchemy[asyncio], asyncpg (for Supabase Postgres)
  - langchain-community (for document loaders only — flag any other use)
  - ragas (evaluation)
  - spacy (for entity extraction in T3.6 — download en_core_web_sm and
    xx_ent_wiki_sm for multilingual NER support)

Create ai/.env.example listing every required env var with a one-line comment
on where to get it:
  - QDRANT_URL — Qdrant Cloud cluster URL
  - QDRANT_API_KEY — Qdrant Cloud API key
  - DATABASE_URL — Supabase transaction-mode pooler connection string
  - REDIS_URL — Upstash Redis rediss:// URL
  - LLM_PROVIDER — one of: openai | anthropic | gemini
  - LLM_MODEL — model name for the chosen provider
  - LLM_API_KEY — API key for LLM provider
  - EMBEDDING_MODEL — default: BAAI/bge-m3

Set up pytest configuration and a `tests/` folder skeleton matching the src/
structure. For Qdrant unit tests, use `QdrantClient(":memory:")`.

When done: update /ai/status.md and flip T0.1 to [x] in /process.md.
```

### T0.2 — LLM provider abstraction

**Manual prerequisite:** An LLM API key set in `.env`.

**Prompt:**
```
Read /context.md §3 and /ai/coding_conventions.md first.

Task: Implement `src/reasoning/llm_provider.py`: an `LLMProvider` abstract
interface with `generate(system_prompt: str, user_prompt: str, **kwargs) -> str`,
and concrete implementations for at least one provider reading from `LLM_PROVIDER`
and `LLM_MODEL` env vars. Write a smoke test that calls the real API once (skip
automatically in CI if no key is present).

When done: update /ai/status.md and flip T0.2 to [x] in /process.md.
```

### T0.3 — Embedding model smoke test

**Prompt:**
```
Read /ai/coding_conventions.md first.

Task: Implement `src/embeddings/embedding_provider.py` wrapping `BAAI/bge-m3`
behind an `EmbeddingProvider` interface (`embed(texts: list[str]) ->
list[list[float]]`). Smoke test: embed a small English sentence and a small Hindi
sentence, assert output dimensionality = 1024, assert vectors are not all-zero.

Note the dimension (1024) in status.md — this is what every Qdrant collection in
T2.1 must be configured with. Flag as a Cross-part note in /process.md.

When done: update /ai/status.md and flip T0.3 to [x] in /process.md.
```

---

## Phase 1 — Corpus & ingestion

### T1.1 — Curate the initial corpus

**Manual prerequisite:** Human research task — an agent can assist but a human
must sanity-check legal accuracy. Budget real time.

**Prompt:**
```
Read /context.md §4 (build order), §3a (5 collections), §3b (intent→collection
mapping), and §5 (official sources) first. Also read /ai/coding_conventions.md
rules 11 and 12 (collection routing and chunking strategies).

Task: Assemble a curated manifest of 20-50 authoritative source documents for the
MVP legal/IP corpus. Store in ai/data/corpus/manifest.md. For each entry record:
title, corpus_collection, jurisdiction, document_type, issuing authority, official
source URL, file (download if allowed).

Collection assignment per document type:
- Indian statutes and rules → legal_statutory
- API/AFI monographs, First-Schedule classical texts → standards_formulations
- NBA/CCPA forms, checklists → procedural_forms
- TRIPS, CBD/Nagoya, WIPO GRATK, export regime guides → international_export
- Case law and prior art → case_law_prior_art (DEFERRED — empty for MVP)

Pull from these official sources:
- India Code: Patents Act 1970 + 2024 Rules (flag Section 3(p)), Trade Marks Act,
  Biological Diversity Act (2023 amendment) + 2024 Rules, GI Act, Designs Act,
  Copyright Act. → legal_statutory
- IP India: Manual of Patent Office Practice, GI Registry records. → legal_statutory
- National Biodiversity Authority: ABS Guidelines; application/intimation forms.
  → procedural_forms (forms) + legal_statutory (regulations)
- FSSAI: Ayurveda-Aahara Regulations. → legal_statutory
- WIPO/CBD: TRIPS, CBD+Nagoya Protocol, WIPO GRATK Treaty (2024). → international_export
- CCRAS / NIIMH e-Samhita / APTA Digital Library: First-Schedule classical texts
  and API/AFI monographs. → standards_formulations
- TKDL public informational pages only (not the restricted DB). → legal_statutory

Do not scrape the restricted TKDL database. Do not substitute clinical Ayurveda
datasets (IMPPAT, AyurParam) for this legal corpus.

When done: update /ai/status.md and flip T1.1 to [x] in /process.md.
```

### T1.2 — Parsing pipeline

**Prompt:**
```
Read /ai/coding_conventions.md first.

Task: Implement `src/ingestion/parser.py`: given a source file (PDF or HTML) and
its manifest metadata (including corpus_collection), extract clean text. Use
PyMuPDF for PDF, BeautifulSoup for HTML, Tesseract as OCR fallback only when no
text layer is detected. Output a normalized intermediate representation with plain
text + structural markers (headings, numbered clauses) + corpus_collection passed
through — the chunker needs it to pick the correct strategy.

Write tests against 2-3 sample documents covering both PDF and HTML sources.

When done: update /ai/status.md and flip T1.2 to [x] in /process.md.
```

### T1.3 — Collection-aware chunking

**Prompt:**
```
Read /ai/coding_conventions.md rules 7, 11, and 12 VERY carefully before writing
any code — the chunking strategies differ per collection and this file is where they
are all implemented.

Task: Implement `src/ingestion/chunker.py` as a dispatcher pattern: given the
parser's output (including corpus_collection), instantiate and run the correct
strategy class. Implement five concrete strategy classes:

1. `LegalStatutoryChunker` (legal_statutory):
   - Detects Act → Chapter → Section → Subsection hierarchy via numbering patterns.
   - One chunk per Section/Subsection (200–800 tokens). Never split mid-clause.
   - Chunk metadata: {document_id, corpus_collection, act, chapter, section,
     subsection, jurisdiction, document_version, text}
   - Test: mock "Section 3, subsection (p)" produces one chunk with section="3",
     subsection="p".

2. `StandardsFormulationsChunker` (standards_formulations):
   - One chunk per monograph/formulation entry. Supplementary notes become child
     chunks linked via parent_chunk_id.
   - Metadata: {document_id, corpus_collection, source, monograph_id,
     formulation_name, substance_type, jurisdiction, text}

3. `CaseLawChunker` (case_law_prior_art):
   - Paragraph-level. Full case metadata on every chunk.
   - Metadata: {document_id, corpus_collection, case_name, court, year,
     citation_ref, paragraph_index, jurisdiction, text}
   - (Empty at MVP — implement ready, no documents yet.)

4. `ProceduralFormsChunker` (procedural_forms):
   - Form section/field-group level (150–400 tokens).
   - Metadata: {document_id, corpus_collection, form_name, section_heading,
     authority, jurisdiction, text}

5. `InternationalExportChunker` (international_export):
   - Article-level (300–800 tokens).
   - Metadata: {document_id, corpus_collection, treaty_name, article_number,
     paragraph, jurisdiction: "INTERNATIONAL", text}

Write at least one test per strategy with a representative document fragment.

When done: update /ai/status.md and flip T1.3 to [x] in /process.md.
```

---

## Phase 2 — Retrieval

### T2.1 — Embedding generation + Qdrant Cloud indexing

**Prompt:**
```
Read /ai/coding_conventions.md (Stack and rules 11-12) and /context.md §3a first.
Confirm embedding dimension from T0.3's status.md note before creating collections.

Task: Implement `src/embeddings/indexer.py`: takes chunks from T1.3, embeds via
the T0.3 EmbeddingProvider, and upserts into the correct Qdrant Cloud collection
based on each chunk's corpus_collection.

Requirements:
- Connect via QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY). Unit tests
  use QdrantClient(":memory:").
- Ensure all 5 collections exist on startup (create if absent, idempotent):
  legal_statutory, standards_formulations, case_law_prior_art, procedural_forms,
  international_export. Each: vector_size=1024, distance=Cosine.
- All chunk metadata fields stored as Qdrant payload fields (not buried in JSON
  blob) — these are what retrieval filters against.
- Batch upsert for efficiency.
- Test: index 3 mock chunks across 2 collections, verify correct collection + payload.

When done: update /ai/status.md with the finalized payload schema per collection
and flip T2.1 to [x] in /process.md.
```

### T2.2 — BM25 keyword index

**Prompt:**
```
Read /ai/coding_conventions.md (Stack — rank_bm25) first.

Task: Implement `src/retrieval/keyword_search.py` using rank_bm25 (BM25Okapi).
Build the BM25 index from all chunk texts + IDs at ingestion time, serialize to
disk (pickle or joblib) for reload without re-indexing. Expose:
  - build_index(chunks) / load_index(path) / search(index, query, collection, top_k)

Test that "Section 3(p)" retrieves chunks containing "Section 3(p)" — legal
section references with parentheticals are a tokenization edge case. If default
tokenizer fails, implement a custom tokenizer preserving "3(p)" as one token.

When done: update /ai/status.md and flip T2.2 to [x] in /process.md.
```

### T2.3 — Hybrid retrieval + reranking

**Prompt:**
```
Read /context.md §2 and /ai/coding_conventions.md rules 5, 11, 13 first.

Task: Implement `src/retrieval/hybrid_retriever.py`. This is the core retrieval
primitive called by the query pipeline (T4.1) for EACH sub-task.

Function signature:
  async def retrieve(
    query: str,
    collections: list[str],
    jurisdiction: str,        # HARD filter applied at Qdrant query level
    top_k: int = 8,
  ) -> list[EvidenceChunk]

Steps:
1. Qdrant vector search in each collection in `collections`, with a Qdrant payload
   filter `jurisdiction == jurisdiction` applied at query time (not post-hoc Python
   filtering — this enforces context.md §2 rule 2).
2. BM25 keyword search (T2.2) in the same collections.
3. Merge via Reciprocal Rank Fusion (RRF).
4. Rerank with BGE cross-encoder or Cohere Rerank (if COHERE_API_KEY is set).
5. Return top_k EvidenceChunks.

This function is `async` so T4.1 can call multiple instances in parallel via
asyncio.gather (see coding_conventions rule 13).

Test (using QdrantClient(":memory:")): chunks across 2 collections + 2
jurisdictions; query with jurisdiction="INDIA" must never return a
payload.jurisdiction="USA" chunk.

When done: update /ai/status.md with the finalized signature and flip T2.3 to
[x] in /process.md.
```

---

## Phase 3 — Classification, context gathering & entity extraction

### T3.1 — Jurisdiction classifier

**Prompt:**
```
Read /context.md §2 rule 2 and /ai/coding_conventions.md first.

Task: Implement `src/classification/jurisdiction_classifier.py`: given a user
question and the jurisdiction explicitly selected in the UI (frontend's jurisdiction
toggle is the primary signal), resolve the concrete jurisdiction filter value(s)
for retrieval ("INDIA", "USA", "INTERNATIONAL", etc.). Rule-based mapping with
light LLM/keyword assist only when a question explicitly names a different
jurisdiction than the one selected — surface it clearly, don't silently switch.

When done: update /ai/status.md and flip T3.1 to [x] in /process.md.
```

### T3.2 — Intent classifier

**Prompt:**
```
Read /ai/coding_conventions.md rules 11 and 14 before writing any code.

Task: Implement `src/classification/intent_classifier.py`. Two classification
levels:

Level 1 — UI intent (maps to DomainIntent enum):
  BUSINESS | EXPORT | MEDICINAL | PATENT | RESEARCH | OTHER
  Input: the intent the user explicitly selected in the frontend. This is a
  direct mapping, not an inference — the UI selection IS the Level 1 intent.

Level 2 — Fine-grained intent (maps to collection routing):
  PATENT, TRADEMARK, GI, COPYRIGHT, DESIGN, PLANT_VARIETY, TRADE_SECRET,
  ABS, TKDL, PRODUCT_CLASSIFICATION, DRUG_REGULATION, FOOD_REGULATION,
  COSMETIC, EXPORT, INTERNATIONAL_IP, GENERAL.
  Inferred from the user's full question text (keyword/rule-based first, LLM
  fallback for ambiguous).

Return both levels plus target_collections (list[str]) from rule 11's mapping.
The intent→collection map must be a named constant in this file.

Tests: one per DomainIntent, asserting correct Level 2 intents and
target_collections are returned.

When done: update /ai/status.md and flip T3.2 to [x] in /process.md.
```

### T3.3 — Deterministic product classification rules engine

**Prompt:**
```
Read /context.md §2 rule 6 and §5 (FSSAI Ayurveda-Aahara distinction), then
/ai/coding_conventions.md rule 3.

Task: Implement `src/classification/product_classifier.py` as an explicit,
auditable rules engine (not an LLM prompt) taking wizard answers (product type,
derived-from-authoritative-text, formulation novelty, biological resources) and
returning: classification label (CLASSICAL_AYURVEDIC_MEDICINE / PROPRIETARY_MEDICINE
/ NEW_NON_CLASSICAL_DRUG / PHYTOPHARMACEUTICAL / AYURVEDA_AAHARA / COSMETIC /
UNCLEAR), regulatory pathway description, and rules_fired list (for the audit
field). Encode the FSSAI Ayurveda-Aahara food-vs-drug distinction as an explicit
rule, not LLM inference.

Tests: one per rule branch + edge cases returning UNCLEAR.
Document exact signature + return shape in status.md (backend T4.1 calls this).

When done: update /ai/status.md and flip T3.3 to [x] in /process.md.
```

### T3.4 — ABS assessment engine

**Prompt:**
```
Read /context.md §5 (Biological Diversity Act facts) first.

Task: Implement `src/abs/abs_engine.py`: given biological resources, origin,
purpose, and whether research/access already occurred, return a relevance label
(HIGH/MEDIUM/LOW/NOT_APPLICABLE) and ordered next-steps list. Primarily rule-based
— document any LLM usage and why.

Document the function signature in status.md (backend T4.2 depends on it).

When done: update /ai/status.md and flip T3.4 to [x] in /process.md.
```

### T3.5 — Context gathering agent

**Prompt:**
```
Read /context.md §1 (intent-first pipeline) and §3b (intent→context questions
table), and /ai/coding_conventions.md rule 14 first.

Task: Implement `src/context_gathering/agent.py`.

This module sits between intent selection (T3.2) and entity extraction (T3.6). Its
job is to generate the 2–4 follow-up questions the AI asks the user to collect
structured context before retrieval begins.

Requirements:
1. Implement a `ContextGatheringAgent` with a method:
   `get_questions(domain_intent: DomainIntent) -> list[ContextQuestion]`
   where ContextQuestion = {question_id, question_text, answer_type
   (FREE_TEXT | SINGLE_SELECT | MULTI_SELECT), options (if select), required: bool}.

2. Question templates per intent must be **versioned files in
   `src/prompts/context_questions/`** — one file per intent
   (BUSINESS.yaml, EXPORT.yaml, MEDICINAL.yaml, PATENT.yaml, RESEARCH.yaml,
   OTHER.yaml). The agent loads these at startup, not at runtime per request.
   The OTHER intent file contains only one question: a free-text description.
   DO NOT use an LLM to generate context questions at request time — templates are
   code, not generated content (coding_conventions rule 14).

3. Implement `parse_answers(domain_intent, raw_answers: dict) -> ContextObject`
   where ContextObject is a typed dataclass holding the structured answers that
   the entity extractor (T3.6) and query decomposer (T4.1) will consume.

4. For each intent, define the expected ContextObject schema:
   - EXPORT: {herbs: list[str], destination: str, purpose: COMMERCIAL|RESEARCH,
              nba_approached: bool, already_in_market: bool}
   - PATENT: {novel_aspect: str, type: HERB|FORMULATION|PROCESS,
              prior_art_search_needed: bool, uses_biological_resources: bool}
   - MEDICINAL: {formulation_type: CLASSICAL|PROPRIETARY|UNKNOWN,
                 from_authoritative_text: bool, new_ingredients: list[str]}
   - BUSINESS: {product_type: str, brand_name: str|None,
                target_market: INDIA|INTERNATIONAL|BOTH}
   - RESEARCH: {research_type: CLINICAL|PHYTOCHEMICAL|IP,
                biological_resources: bool, publish_internationally: bool}
   - OTHER: {free_description: str}

5. Write sample question files for EXPORT and PATENT intents — these will be
   reviewed and extended by the human for accuracy. Mark the others as TODO(human).

6. Tests: assert EXPORT intent returns exactly the expected questions with correct
   answer_types; assert parse_answers on a mock EXPORT answer dict produces a
   correctly typed ContextObject.

When done: update /ai/status.md with the ContextObject schemas (backend and
frontend need to match them in their API contracts) and flip T3.5 to [x] in
/process.md. Add a Cross-part note — frontend needs these schemas for the
context-gathering UI and backend needs them for the /api/v1/context endpoint.
```

### T3.6 — Entity extractor

**Prompt:**
```
Read /context.md §1 (pipeline stage 3) and /ai/coding_conventions.md rule 14 first.

Task: Implement `src/entity_extraction/extractor.py`.

This module takes a ContextObject (from T3.5) and the user's free-form question
text and extracts a structured EntitySet used by the query decomposer in T4.1.

Requirements:
1. Implement `extract(context: ContextObject, question: str) -> EntitySet`
   where EntitySet contains:
   - herbs: list[str]           — botanical names where possible (use a curated
                                  herb name list + spaCy NER for extraction from
                                  free text; the curated list takes precedence)
   - jurisdictions: list[str]   — e.g. ["INDIA", "EU", "INTERNATIONAL"]
   - ip_types: list[IPType]     — e.g. [PATENT, TRADEMARK]
   - biological_resources: list[str]
   - formulation_name: str|None
   - destination_country: str|None
   - regulatory_regime: str|None — e.g. "EU dietary supplements", "FSSAI Ayurveda"

2. Herb name resolution:
   - Maintain a curated herb lookup table (common name → botanical name) as a YAML
     file in `ai/data/herb_names.yaml`. Seed it with at least 30 common Ayurvedic
     herbs (Ashwagandha→Withania somnifera, Tulsi→Ocimum sanctum, etc.).
   - Use spaCy (xx_ent_wiki_sm or en_core_web_sm) for NER on free text.
   - Combine: curated lookup first, spaCy NER as fallback for unrecognized names.

3. Jurisdiction extraction:
   - If ContextObject.destination is set (e.g. "EU"), map to a canonical
     jurisdiction ("EU" → "EU", "United States" → "USA", etc.) using a curated
     mapping table.
   - Always include "INDIA" for domestic regulatory questions regardless of
     destination.

4. The EntitySet is the input to the query decomposer — document its schema in
   status.md. Backend and frontend don't directly consume this, but its content
   drives what sub-tasks get created.

5. Tests:
   - "Export Ashwagandha and Tulsi supplement to the EU" → herbs=["Withania
     somnifera", "Ocimum sanctum"], jurisdictions=["INDIA","EU"], destination="EU"
   - A question mentioning "Section 3(p)" → ip_types=[PATENT]

When done: update /ai/status.md and flip T3.6 to [x] in /process.md.
```

---

## Phase 4 — Reasoning & trust layer

### T4.1 — Query pipeline (intent-first agentic pipeline)

**Prompt:**
```
Read /context.md §1 (6-stage pipeline), §2 rules 1 and 3, §3b (intent routing),
and /ai/coding_conventions.md rules 1, 8, 9, 11, 13, 14 before writing any code.
Also check /ai/status.md for the finalized signatures of T3.5 (ContextObject),
T3.6 (EntitySet), T3.2 (intent classifier), and T2.3 (retrieve function).

Task: Implement `src/reasoning/query_pipeline.py` — the top-level entrypoint that
backend's Phase 3 T3.1 calls into.

Main entrypoint:
  async def query(
    question: str,
    domain_intent: DomainIntent,   # from UI — BUSINESS|EXPORT|MEDICINAL|PATENT|RESEARCH|OTHER
    context: ContextObject,        # from T3.5 context-gathering answers
    jurisdiction: str,             # from UI jurisdiction toggle
    language: str,                 # "en" or "hi"
    conversation_history: list,
  ) -> QueryResult

Implementation — follow this sequence EXACTLY:

STEP 1 — Jurisdiction resolution:
  resolved_jurisdictions = jurisdiction_classifier.resolve(question, jurisdiction)

STEP 2 — Fine-grained intent + collection routing:
  intent_result = intent_classifier.classify(question, domain_intent)
  # intent_result.target_collections is a list[str] from the routing table

STEP 3 — Entity extraction (if not already done upstream):
  entity_set = entity_extractor.extract(context, question)

STEP 4 — Query decomposition:
  Implement `decompose(intent_result, entity_set, context) -> list[SubTask]`
  Each SubTask = {query_text: str, collection: str, jurisdiction: str,
                  sub_task_label: str}

  Decomposition rules (encode explicitly — not LLM-generated at runtime):
  - For each unique collection in intent_result.target_collections, generate a
    targeted sub-task query from the EntitySet. Examples:
    * standards_formulations sub-task: "botanical profile of {herb}" for each herb
    * legal_statutory sub-task: "{ip_type} regulations for {product_type} under
      Indian law"
    * international_export sub-task: "{destination} regulatory requirements for
      {product_type} export"
    * procedural_forms sub-task: "NBA intimation/approval checklist for {purpose}"
  - If entity_set.herbs is non-empty AND collection is standards_formulations,
    generate one sub-task per herb (not one for all herbs together).
  - If decomposition produces > 6 sub-tasks, merge sub-tasks in the same
    collection into one query (too many parallel calls degrades latency).

STEP 5 — Parallel retrieval (CORE — do not make this sequential):
  sub_results = await asyncio.gather(
    *[retriever.retrieve(
        query=task.query_text,
        collections=[task.collection],
        jurisdiction=task.jurisdiction,
      ) for task in sub_tasks]
  )
  Log "path=decomposed, sub_task_count={n}" in structured log.

  FAST PATH: if decomposition produces exactly 1 sub-task, skip asyncio.gather
  overhead and call retrieve() directly. Log "path=fast_path".

STEP 6 — Evidence assembly:
  Merge all sub_results into a single evidence list, deduplicate by chunk_id,
  sort by reranker score. If total evidence < MIN_EVIDENCE_THRESHOLD (define a
  constant — start at 3 chunks), return explicit abstention result
  ("insufficient authoritative evidence") — do NOT call the LLM.

STEP 7 — LLM synthesis:
  Build a structured prompt from `src/prompts/answer_synthesis/` (versioned
  template, per coding_conventions rule 9) that:
  - Organizes evidence by sub-task label (so the LLM knows which source each
    chunk came from)
  - Instructs the LLM to answer only from provided evidence, citing chunk IDs
  - Instructs the LLM to structure the answer by jurisdiction if evidence spans
    multiple jurisdictions
  - Instructs explicit "cannot answer from evidence" flagging where evidence is
    insufficient for a sub-task

STEP 8 — Citation validation (T4.2) — never skip once T4.2 exists.

STEP 9 — Confidence scoring (T4.3).

STEP 10 — Guardrails (T4.4).

STEP 11 — Return QueryResult matching backend's /api/v1/chat contract.

QueryResult must include: answer, confidence, confidence_label, classification
(if product classifier ran), citations[], requires_human_review, sub_tasks_run
(list of SubTask labels — for the frontend's evidence map visualization),
sources_by_collection (dict mapping collection → list of documents used).

When done: update /ai/status.md with the FULL QueryResult schema (this is the
contract backend T3.1 and frontend T2.1/T2.2 both depend on) and flip T4.1 to
[x] in /process.md. Add Cross-part notes for both backend and frontend.
```

### T4.2 — Citation validator

**Prompt:**
```
Read /ai/coding_conventions.md rule 2 first.

Task: Implement `src/citations/validator.py`: given the LLM's raw answer (with
inline citation markers referencing chunk IDs) and the actual evidence chunk set,
verify every citation ID exists in the evidence set and that the cited chunk's
text plausibly supports the citing sentence (similarity/overlap check for MVP;
optional LLM fallback for ambiguous cases — document the tradeoff). If any
citation fails: strip the unsupported sentence + note the reduction, OR trigger
regeneration/abstention if too much is affected (define and document the threshold).

Tests: all-valid citations pass unchanged; fabricated citation ID is caught and
handled per documented policy.

When done: update /ai/status.md and flip T4.2 to [x] in /process.md.
```

### T4.3 — Composite confidence scorer

**Prompt:**
```
Read /ai/coding_conventions.md rule 4 first.

Task: Implement `src/confidence/scorer.py`. Composite score from:
- retrieval_score: top result's Qdrant distance score
- citation_score: fraction of citations that passed T4.2
- source_authority_score: statute/treaty > guideline > secondary (explicit ranking
  table — define as a constant)
- jurisdiction_match: exact vs. inferred
- answer_evidence_coverage: fraction of answer claims carrying a citation
- sub_task_coverage: fraction of decomposed sub-tasks that returned evidence
  (new factor for the multi-task pipeline — a query that got evidence for 3/4
  sub-tasks is less complete than one with 4/4)

Document exact weights + formula in a comment at the top of the file and in
status.md — must be explainable. Document the LOW threshold that triggers
requires_human_review=true.

When done: update /ai/status.md and flip T4.3 to [x] in /process.md.
```

### T4.4 — Guardrails / abstention rules

**Prompt:**
```
Read /context.md §2 and §5 (TKDL restriction) and /ai/coding_conventions.md
rules 6 and 8 first.

Task: Implement `src/guardrails/rules.py`:
- Abstain if evidence below MIN_EVIDENCE_THRESHOLD (from T4.1).
- TKDL guard: never imply full database access — enforce via template-level check,
  not just prompt instruction.
- Jurisdiction mixing guard: if evidence from > 1 jurisdiction was used, the
  answer must visibly separate them — enforce structurally.
- Always append "information, not legal advice" disclaimer at pipeline level.

Tests: deliberately adversarial inputs for each guardrail.

When done: update /ai/status.md and flip T4.4 to [x] in /process.md.
```

---

## Phase 5 — Multilingual, evaluation, stretch

### T5.1 — Hindi support via Bhashini

**Manual prerequisite:** Bhashini API credentials from bhashini.gov.in.

**Prompt:**
```
Read /context.md and /ai/coding_conventions.md first.

Task: Implement `src/multilingual/bhashini_client.py` wrapping Bhashini translation
APIs. Wire into T4.1: `language="hi"` input → translate question + context answers
to English for retrieval → run pipeline → translate final answer back to Hindi. Do
NOT translate citation source titles/section references — those remain in their
original form tied to the authoritative source. Stub behind the interface and mark
`[!]` blocked if credentials aren't yet available.

When done: update /ai/status.md and flip T5.1 to [x] or [!] in /process.md.
```

### T5.2 — Evaluation harness

**Prompt:**
```
Read /context.md §4 and /ai/coding_conventions.md first.

Task: Build ai/tests/eval/questions.jsonl: 100 questions (25 Patent / 20
Regulatory / 15 ABS / 10 Trademark / 10 Product classification / 10 International
/ 10 TKDL), each with: expected_answer_summary, expected_source (document + section),
expected_jurisdiction, expected_collection, expected_classification (where applicable),
and domain_intent (which of the 6 UI intents this question maps to — for testing the
context-gathering path).

Implement `src/evaluation/run_eval.py` measuring:
- retrieval_accuracy (correct source chunk in top-k)
- collection_routing_accuracy (intent → correct collections)
- context_gathering_accuracy (did the right context questions get generated)
- citation_accuracy (citations pass T4.2)
- answer_accuracy (LLM-as-judge against expected_answer_summary — document if so)
- abstention_accuracy (correctly abstains on unanswerable questions)
- sub_task_decomposition_accuracy (correct sub-tasks generated for a query)
- multilingual_quality (Hindi subset via T5.1 when available)

Output summary JSON report.

When done: update /ai/status.md with eval results and flip T5.2 to [x] in
/process.md.
```

### T5.3 — TKDL public-information pointer

**Prompt:**
```
Read /context.md §2 rule 5 and §5.

Task: Implement `src/reasoning/tkdl_pointer.py`: a fixed, code-controlled response
template (not free LLM generation) for TKDL-intent queries, stating that full TKDL
access is restricted to patent offices, surfacing only publicly available TKDL
information from the `standards_formulations` and `legal_statutory` collections,
and directing users to tkdl.res.in. Wire into T4.1 so TKDL-intent queries always
pass through this template.

When done: update /ai/status.md and flip T5.3 to [x] in /process.md.
```

### T5.4 — Stretch: knowledge graph

**Prompt (do not start until Phases 0-4 and T5.1-T5.3 are `[x]`):**
```
Read /context.md §4 — confirm Phases 0-4 and T5.1-T5.3 are done in /process.md
before starting.

Task: Use Neo4j AuraDB (free tier at neo4j.com/cloud/aura-free — not a Docker
container) to model relationships: Product-contains->BiologicalResource,
Product-based_on->AyurvedicText, Law-has_section->Section,
Section-governs->ProductCategory. Add NEO4J_URI and NEO4J_PASSWORD to .env.example.

Use the graph to answer multi-hop questions (e.g. "does my GI-tagged formulation
also need Nagoya clearance for export to the EU?") that parallel Qdrant retrieval
alone struggles with. Graph-derived claims still trace to Qdrant source chunks —
the graph adds hops, not new unsourced claims.

Note: The agentic orchestration (query decomposition + parallel retrieval) has been
promoted to the core T4.1 pipeline — this stretch task adds only the knowledge
graph layer on top of that existing infrastructure.

When done: update /ai/status.md and flip T5.4 to [x] in /process.md.
```
