# ai/status.md

Granular status log + the authoritative record of interfaces/function signatures
the backend calls into (e.g. the ingestion task signature, the query pipeline
entrypoint). Populate as you go — don't make backend guess your function shapes.

---

## Interfaces backend depends on

*(none finalized yet — populate as they're built, e.g.:)*
```
# example of what an entry here should look like once real:
# ingest_document(document_version_id: str, storage_key: str) -> IngestResult
# query(question: str, jurisdiction: str, language: str) -> QueryResult
```

---

## Corpus manifest

**Seed dataset added** (see `ai/data/corpus/seed/README.md` for full detail and
verification-tier explanation): 11 real records across `legal_knowledge.jsonl`
(6), `ipr_prior_art.jsonl` (3 \u2014 the turmeric/neem/basmati TK-prior-art cases),
`ayush_tk.jsonl` (2), plus a `load_seed.py` embedding/insertion script and an
8-question grounded eval set at `ai/tests/eval/questions_seed.jsonl`. `case_law`
deliberately left empty (see `case_law_STUB.md` \u2014 no verified real Indian court
judgment on point was found; do not fill with a fabricated one).
**This is a proof-of-pipeline seed, not the full T1.1 corpus** \u2014 T1.1 (20-50
document curation) is still open.

*(track the full T1.1 corpus here as it's built, or in
data/corpus/manifest.md linked from here)*

---

## Log

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
