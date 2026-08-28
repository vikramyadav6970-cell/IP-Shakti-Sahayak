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

Full authoritative manifest created at [`ai/data/corpus/manifest.md`](data/corpus/manifest.md):
- **Total documents**: 42 curated sources across 5 collections:
  - `legal_statutory` (16 documents): Indian Patents Act 1970 (Sec 3(p), 3(d), 3(e), 10(4), 25, 64), Patents Rules 2024, Trade Marks Act 1999, GI Act 1999, Biological Diversity Act 2002 (2023 amendment), BD Rules 2024, NBA ABS Guidelines 2014, Drugs and Cosmetics Act 1940 (Chapter IVA), Drugs Rules 1945 (Part XVI-XIX), FSSAI Ayurveda Aahara Regs 2022, Designs Act 2000, CSIR-TKDL Public Policy Framework.
  - `standards_formulations` (7 documents): Ayurvedic Pharmacopoeia of India (API Part I Single Drugs Vols I-IX), Ayurvedic Formulary of India (AFI Part I-III Classical Formulations), First Schedule list of 54 Authoritative Treatises, PCIM&H Testing Standards & Quality Parameters, CCRAS Phytochemical SOPs.
  - `procedural_forms` (8 documents): NBA Form I (Access), NBA Form II (Transfer of Research), NBA Form III (IPR Approval), NBA Form IV (Third-party transfer), SBB Prior Intimation Checklist, Form 24D (Manufacturing License), Form 24E (Loan License), CCPA AYUSH Advertising Checklist.
  - `international_export` (8 documents): WTO TRIPS Agreement (Art 27, 28, 29), CBD 1992 (Art 8(j), 15), Nagoya Protocol 2010, WIPO GRATK Treaty 2024 (Art 3 mandatory genetic resource disclosure), EU THMPD Directive 2004/24/EC, EU Food Supplement Regulation (EC) 1924/2006, US DSHEA 1994 / 21 CFR 111, CITES Appendices on medicinal plants.
  - `case_law_prior_art` (3 dossiers): Landmark CSIR/India TKDL revocation dossiers (Turmeric US 5,401,504, Neem EPO 0436257, Basmati US 5,663,484).

---

## Log

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
