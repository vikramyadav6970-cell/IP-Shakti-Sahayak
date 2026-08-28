# ai/coding_conventions.md

Read `/context.md` and `/process.md` before this file. This file governs how code
is written inside `ai/` — the RAG/reasoning layer. **This is the part of the
project where the hard constraints in `context.md` §2 matter most.** Re-read them
before every task in this folder.

## Stack (authoritative)

- **Python 3.11+.**
- LLM access via a **provider abstraction** (`LLMProvider` interface with
  `OpenAIProvider` / `AnthropicProvider` / `GeminiProvider` implementations) —
  never call a provider SDK directly from pipeline code. Provider + model name
  come from env vars (`LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`).
- **Embeddings:** `BAAI/bge-m3` (multilingual, strong Hindi+English retrieval) as
  the default — 1024-dimensional. Keep this behind an `EmbeddingProvider`
  interface so swapping to a cloud embedding API later is a config change.
- **Vector store: Qdrant Cloud** (managed, free tier). Five named collections —
  one per corpus type (see `context.md §3a` for the full table and chunk-size
  guidance). Connection via `qdrant-client` using `QDRANT_URL` and `QDRANT_API_KEY`
  env vars. Do NOT use a local in-process Qdrant instance in prod — always connect
  to the cloud cluster. For unit tests, use `QdrantClient(":memory:")`.
- **Keyword search:** `rank_bm25` library — decoupled from the DB since we are not
  relying on Postgres FTS anymore (Qdrant is the vector layer). BM25 index is built
  in-memory from the corpus text at startup or maintained as a serialized artifact.
  Test specifically that "Section 3(p)" and similar section-reference tokens
  tokenize and retrieve correctly.
- **Reranker:** BGE cross-encoder (e.g. `BAAI/bge-reranker-v2-m3`) or Cohere
  Rerank (if `COHERE_API_KEY` is configured) — document which is active in
  `status.md`. Keep behind a `RerankerProvider` interface.
- **Relational metadata DB:** Supabase (managed Postgres). The AI layer reads
  document/version metadata from the same Supabase DB the backend uses. Use the
  `DATABASE_URL` (Supabase connection string, **transaction-mode pooler URL** for
  serverless/worker contexts) env var — never hardcode a DB URL.
- **Cache / job broker:** Upstash Redis. Use `redis-py` with the Upstash REST URL
  (`UPSTASH_REDIS_REST_URL` + `UPSTASH_REDIS_REST_TOKEN` env vars) or the standard
  `REDIS_URL` (Upstash provides a `rediss://` URL that `redis-py` and Celery accept
  directly).
- **Background execution:** Celery tasks (triggered by the backend per
  `backend/prompts/phases.md` T2.3), Celery broker = Upstash Redis.
- **Multilingual (Phase 5):** Bhashini APIs for Hindi ASR/translation/TTS.
- **Evaluation:** RAGAS or an equivalent custom harness.

## Hard rules — these encode the project's actual differentiator, follow them exactly

1. **The LLM never generates a legal claim without retrieved evidence backing it.**
   Every prompt to the LLM must include the retrieved evidence chunks, and the
   system prompt must instruct it to answer only from that evidence and to say so
   explicitly when evidence is insufficient (see `context.md §2` rule 3).
2. **Citations are IDs, not free text the LLM writes.** The LLM references evidence
   by the chunk/document IDs it was given; a separate citation validator step
   checks every citation ID in the LLM's output actually exists in the evidence
   set it was given (see Phase 4, T4.2). If a citation can't be validated, reject
   and regenerate (or abstain) — never pass an unvalidated citation through to the
   user.
3. **Product classification is a deterministic rules engine**, not an LLM
   judgment call (`context.md §2` rule 6). Encode rules as explicit, testable
   `if/elif` logic or a small rules-table — not a prompt asking the LLM to decide
   the category. The LLM may explain the classification in natural language
   afterward, but must not be the thing deciding it.
4. **Confidence is computed, not asked for.** Never use a raw "rate your
   confidence 0-100" LLM self-report as the confidence score. Compute a composite
   from retrieval score, citation validity, source authority, jurisdiction match,
   and evidence coverage (formula documented in Phase 4, T4.3).
5. **Jurisdiction metadata is mandatory on every chunk** at ingestion time
   (INDIA/USA/EU/INTERNATIONAL/etc.) and every retrieval call must filter by the
   jurisdiction the user asked about — cross-jurisdiction leakage into a single
   answer is a hard bug, not a style issue (`context.md §2` rule 2).
6. **Never claim full TKDL access.** Only public TKDL information may be indexed;
   represent TKDL-related answers as a "traditional knowledge pointer," and say so
   explicitly in any prompt/response template that touches TKDL (`context.md §5`).
7. **Chunking respects both legal document structure AND collection type.** See
   rule 11 below for the collection-specific chunking requirements. Never blindly
   split on a fixed token count without retaining structural metadata as chunk
   payload fields; citations need to reference an exact section, not "chunk #47."
8. **No fabricated dates, section numbers, case names, or patent numbers** may
   appear anywhere in a prompt template as an "example" that could leak into
   output — even few-shot examples in prompts must use clearly fictional
   placeholders (e.g. "Example Act, Section X") so the LLM never confuses a
   few-shot example with real law.
9. **Prompts are versioned code, not scratch strings.** Keep every system/user
   prompt template in `ai/src/prompts/` (the *runtime* prompts directory — distinct
   from this `ai/prompts/phases.md` *task* file, don't confuse the two) as a
   separate file with a version comment, not inlined as a Python string literal
   scattered across the codebase.
10. **No custom reimplementation of BM25, cross-encoder inference, or embedding
    math** — use the established libraries named in the Stack section above.
11. **Collection routing is mandatory.** Every ingestion call must specify which
    Qdrant collection a chunk belongs to (derived from the document's `corpus_type`
    field in the manifest). Every retrieval call must include the target collection(s)
    — determined by the intent classifier. Never query all five collections
    indiscriminately on a single retrieval call; always filter by the 1–2 most
    relevant collections for the detected intent. Allowed intent → collection
    mappings:
    - PATENT, TRADEMARK, GI, COPYRIGHT, DESIGN, DRUG_REGULATION → `legal_statutory`
    - PRODUCT_CLASSIFICATION, FOOD_REGULATION, COSMETIC → `legal_statutory` +
      `standards_formulations`
    - ABS, EXPORT → `legal_statutory` + `international_export`
    - INTERNATIONAL_IP → `international_export` + `legal_statutory`
    - TKDL → `standards_formulations` + `legal_statutory`
    - GENERAL → all collections (broad search, last resort)
    - Forms/checklist queries → `procedural_forms`
12. **Collection-specific chunking strategies** (encode in `chunker.py` as
    strategy classes dispatched by `corpus_type`):
    - **`legal_statutory`**: Act → Chapter → Section → Subsection → Clause
      hierarchy. One chunk per Section or Subsection (200–800 tokens). Never split
      mid-clause. Metadata: `{act, chapter, section, subsection, jurisdiction}`.
    - **`standards_formulations`**: One chunk per monograph/formulation entry (the
      full entry for a single herb/formulation). Supplementary notes become child
      chunks linked via `parent_chunk_id`. Metadata: `{source, monograph_id,
      formulation_name, substance_type}`.
    - **`case_law_prior_art`**: Paragraph-level chunks. Full case metadata
      (`{case_name, court, year, citation}`) duplicated on every chunk so any
      chunk can stand alone as a citation. (Collection created empty for MVP —
      ingested later when data is available.)
    - **`procedural_forms`**: Form section / field-group level (150–400 tokens).
      Keep form name and section heading as metadata. Short chunks are intentional
      here — these are dense, structured instructions.
    - **`international_export`**: Treaty → Article → Paragraph hierarchy. One chunk
      per Article (300–800 tokens). Metadata: `{document_id, corpus_collection,
      treaty_name, article_number, paragraph, jurisdiction: "INTERNATIONAL"}`.
13. **Parallel multi-collection retrieval is mandatory for multi-task queries.**
    When query decomposition produces N sub-tasks (from T3.6 + T4.1), run them
    with `asyncio.gather(*[retrieve(task) for task in sub_tasks])` — never loop
    sequentially. Sub-task results are then merged by the evidence assembler before
    the LLM call. Sequential retrieval is only acceptable for single-collection,
    single-task queries (simple/fast path). Always document which path a query took
    in the structured log ("fast_path" vs. "decomposed").
14. **The 6 UI domain intents are the public API of the pipeline.** The
    `context_gathering_agent` (T3.5) and `entity_extractor` (T3.6) each receive the
    UI intent as a typed enum (`BUSINESS/EXPORT/MEDICINAL/PATENT/RESEARCH/OTHER`)
    and must hard-code their behavior per intent. No LLM should be asked to
    determine what context questions to generate for a known intent at runtime —
    the question templates per intent are versioned code in `src/prompts/`, not
    dynamically invented.

## Folder structure

```
ai/
├── coding_conventions.md
├── status.md
├── prompts/
│   └── phases.md              # THIS folder's task prompts (what you're reading)
├── requirements.txt
├── src/
│   ├── ingestion/              # parsing, chunking (collection-aware strategies)
│   ├── embeddings/             # EmbeddingProvider, Qdrant indexer (5 collections)
│   ├── retrieval/              # hybrid search (BM25 + Qdrant), reranking, collection routing
│   ├── classification/         # deterministic rules engine, jurisdiction/intent classifiers
│   ├── context_gathering/      # T3.5 — intent-specific question templates + response parser
│   ├── entity_extraction/      # T3.6 — herb/jurisdiction/IP-type NER from context answers
│   ├── abs/
│   ├── reasoning/              # LLM provider abstraction, query decomposer, answer generator
│   ├── citations/              # citation validator
│   ├── confidence/
│   ├── guardrails/
│   ├── multilingual/
│   ├── evaluation/
│   └── prompts/                # RUNTIME prompt templates (versioned), not task prompts
│       ├── context_questions/  # one .txt per UI intent (BUSINESS.txt, EXPORT.txt, etc.)
│       └── answer_synthesis/   # LLM synthesis prompts per intent
├── data/
│   └── corpus/                 # curated source documents (or pointers/manifests to them)
└── tests/
    └── eval/                   # the evaluation question set + expected answers
```

## Definition of done for any AI-layer task

- Has at least one automated test (unit test for rules/parsing logic; an eval-set
  regression check for anything retrieval/generation related, once Phase 5's
  harness exists — before that, a small manual smoke test documented in
  `status.md` is acceptable).
- Every new function/module has a docstring stating its inputs/outputs and, for
  anything touching evidence/citations, explicitly states what guarantee it
  provides (e.g. "guarantees every citation ID returned exists in the input
  evidence set").
- `status.md` and `process.md` updated, including the exact function signature/
  interface if backend depends on calling into this code.
- No hardcoded credentials — all cloud service keys (`QDRANT_URL`, `QDRANT_API_KEY`,
  `UPSTASH_REDIS_REST_URL`, `DATABASE_URL`, `LLM_API_KEY`) come from env vars only.
  Add any new vars to `ai/.env.example` with a comment on where to get them.
