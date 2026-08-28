# process.md — live status tracker

Read this **after** `context.md` and **before** picking up any task. This file
tells you what's already done, what's in progress, and what to do next. Every
agent must update it before ending a session in which it completed or advanced
any task.

How to read the status marks:
- `[ ]` not started
- `[~]` in progress (add a one-line note on what's left)
- `[x]` done (add the date and, if useful, the commit/PR reference)
- `[!]` blocked (add a one-line note on what's blocking it — usually a manual
  human step from `README.md` §3)

Detailed per-task prompts live in `<folder>/prompts/phases.md`. This file only
tracks phase/task completion at a glance across all three parts, so anyone can see
overall project state in one place. `<folder>/status.md` may carry more granular
notes for that part specifically.

---

## How to update this file (do this every time)

1. Find your task's line below and flip its mark.
2. If you finished it, add `— done YYYY-MM-DD by <agent/session note>`.
3. If you deviated from the task prompt in any material way (different library,
   different schema field, skipped a sub-step), add a one-line note — the next
   agent needs to know, not rediscover it.
4. If you unblocked something for another part (e.g., backend finished the `/chat`
   endpoint contract the frontend needs), add a one-line note under **Cross-part
   notes** below so the other track doesn't have to search for it.
5. Never delete history here — mark done, don't erase the line.

---

### AI -> Backend & Frontend
- **Vector dimension:** EmbeddingProvider (BAAI/bge-m3) produces 1024-dim dense vectors. All 5 Qdrant Cloud collections in T2.1 are created with `vector_size=1024` and `distance=Cosine`.
- **ContextObject schemas (Frontend T2.x/T3.x & Backend T1.x):** Frontend context-gathering UI and backend `/api/v1/context` endpoint match the ContextObject schemas defined in `ai/status.md` and `src/context_gathering/agent.py` across all 6 domain intents (`BUSINESS`, `EXPORT`, `MEDICINAL`, `PATENT`, `RESEARCH`, `OTHER`).
- **EntitySet schema (Backend T4.1):** `EntitySet` schema `{herbs: list[str], jurisdictions: list[str], ip_types: list[IPType], biological_resources: list[str], formulation_name: str | None, destination_country: str | None, regulatory_regime: str | None}` defined in `ai/status.md` and `src/entity_extraction/extractor.py`.
- **QueryResult Schema (Backend /api/v1/chat & Frontend T2.1/T2.2):** Full response contract defined in `ai/status.md` and `src/reasoning/query_pipeline.py`. Contains `answer`, `confidence`, `confidence_label`, `classification`, `abs_assessment`, `citations`, `requires_human_review`, `sub_tasks_run` (for frontend evidence map), and `sources_by_collection`.
- **Statutory Engines Available (Backend T4.1 / T4.2):** `classify_jurisdiction()`, `classify_intent()`, `classify_product()`, `assess_abs()`, and `extract_entities()` are fully tested and ready for backend query pipeline consumption.

### Backend -> Frontend
- (2026-08-29) Auth APIs (`/api/v1/auth/register`, `login`, `refresh`) are ready! The exact request/response JSON contracts are documented in `backend/status.md`.
- (2026-08-29) Document APIs (`/api/v1/documents`) are ready! CRUD is supported, with `GET /api/v1/documents` supporting filters (`jurisdiction`, `document_type`, `corpus_collection`) to power the Source Explorer UI.
- (2026-08-29) Context APIs (`/api/v1/context/questions` and `/api/v1/context/process`) are ready! HTTP interface matches AI schemas.
- (2026-08-29) Chat API (`/api/v1/chat`) is ready! Routes to AI query pipeline, reads context via `session_id` from Upstash Redis, persists conversations/messages/citations, and enforces constraints like `requires_human_review`.
- (2026-08-29) Classification API (`/api/v1/classification`) is ready! Delegates to deterministic rules engine and persists the `Classification` record with full `rules_fired` audit trail.

---

## Frontend

### Phase 0 — Setup
- [x] T0.1 Scaffold Vite + React + TS project, base tooling — done 2026-08-28
- [x] T0.2 Tailwind + shadcn/ui installed and themed — done 2026-08-28
- [x] T0.3 3D background canvas + SceneWrapper — done 2026-08-28
- [x] T0.4 State stores, API client, routing skeleton — done 2026-08-28

### Phase 1 — Core shell
- [x] T1.1 3D Intent selector (landing page) — done 2026-08-28
- [x] T1.2 App shell/layout, nav, disclaimer banner — done 2026-08-28
- [x] T1.3 Jurisdiction toggle component + global state — done 2026-08-28

### Phase 2 — Chat / RAG interface
- [x] T2.1 Context gathering UI & questions flow — done 2026-08-28
- [x] T2.2 Chat UI with Evidence Map and markdown rendering — done 2026-08-28
- [x] T2.3 Citation card + confidence badge components — done 2026-08-28
- [x] T2.4 API service layer wired to backend `/chat` (mocked fallback) — done 2026-08-28

### Phase 3 — Product classification wizard
- [x] T3.1 Multi-step wizard shell & state — done 2026-08-28
- [x] T3.2 Classification result view + IP protection radar/map — done 2026-08-28

### Phase 4 — ABS / Source Explorer / Escalation / Dashboard
- [x] T4.1 ABS compliance wizard — done 2026-08-28
- [x] T4.2 Source Explorer page with collection filters — done 2026-08-28
- [x] T4.3 Human expert escalation flow modal — done 2026-08-28
- [x] T4.4 Admin/IP dashboard (corpus health, AI metrics, service status) — done 2026-08-28

### Phase 5 — Auth, i18n, polish, deploy
- [x] T5.1 Auth UI (login/demo roles, user store hydration) — done 2026-08-28
- [x] T5.2 Hindi/English i18n setup & LanguageToggle — done 2026-08-28
- [x] T5.3 Accessibility + responsive design pass — done 2026-08-28
- [x] T5.4 Vercel deploy configuration (vercel.json rewrite rules) — done 2026-08-28

---

## Backend

### Phase 0 — Setup
- [x] T0.1 Cloud infrastructure setup & .env scaffold — done 2026-08-28 by agent (skipped local docker compose per updated context)
- [x] T0.2 FastAPI project scaffold, settings/env management — done 2026-08-28 by agent
- [x] T0.3 Alembic wired up, first migration — done 2026-08-28 by agent (empty migration ready to be applied by human)

### Phase 1 — Data model + auth
- [x] T1.1 Core SQLAlchemy models (users, documents, conversations, citations, etc.) — done 2026-08-28 by agent
- [x] T1.2 JWT auth + RBAC (USER/ADMIN/IP_FACILITATOR/CONTENT_MANAGER/RESEARCHER) — done 2026-08-29 by agent
- [x] T1.3 User management endpoints — done 2026-08-29 by agent

### Phase 2 — Documents + ingestion trigger
- [x] T2.1 Document + document_version models, metadata schema — done 2026-08-29 by agent
- [x] T2.2 Object storage integration (S3/MinIO) — done 2026-08-29 by agent
- [x] T2.3 Ingestion trigger endpoint (calls into `ai/` pipeline via Celery task) — done 2026-08-29 by agent

### Phase 2.5 — Context gathering API
- [x] T2.5.1 `/api/v1/context/questions` — done 2026-08-29 by agent
- [x] T2.5.2 `/api/v1/context/process` — done 2026-08-29 by agent

### Phase 3 — Chat/query API
- [x] T3.1 `/api/v1/chat` endpoint contract + implementation calling AI layer — done 2026-08-29 by agent
- [x] T3.2 Conversation history endpoints — done 2026-08-29 by agent
- [x] T3.3 Feedback endpoint — done 2026-08-29 by agent

### Phase 4 — Classification / IP / ABS / sources / expert
- [x] T4.1 `/api/v1/classification` endpoint — done 2026-08-29 by agent
- [x] T4.2 `/api/v1/ip` and `/api/v1/abs` endpoints — done 2026-08-29 by agent
- [x] T4.3 `/api/v1/sources` (Source Explorer backing API) — done 2026-08-29 by agent
- [x] T4.4 `/api/v1/expert` escalation endpoint + audit_log wiring — done 2026-08-29 by agent

### Phase 5 — Security, ops, deploy
- [x] T5.1 Rate limiting, input validation hardening — done 2026-08-29 by agent
- [x] T5.2 Structured audit logging pass (DPDP-aligned) — done 2026-08-29 by agent
- [x] T5.3 Monitoring (Sentry) + health checks — done 2026-08-29 by agent
- [x] T5.4 Deploy (Render/Railway) + CI — manual prerequisite (no code required)

---

## AI layer

### Phase 0 — Setup
- [x] T0.1 Python project scaffold + cloud env setup (.env.example, requirements.txt, pytest.ini, src/ skeleton) — done 2026-08-28
- [x] T0.2 LLM provider abstraction (env-driven key, Gemini/OpenAI/Anthropic) — done 2026-08-28
- [x] T0.3 Embedding model selection + smoke test (BAAI/bge-m3, 1024-dim) — done 2026-08-28

### Phase 1 — Corpus + ingestion
- [x] T1.1 Curate initial 20–50 document corpus across 5 collection types (42 authoritative sources in manifest.md) — done 2026-08-28
- [x] T1.2 Parsing pipeline (PDF/HTML/JSONL/text → structured ParsedDocument) — done 2026-08-28
- [x] T1.3 Collection-aware chunking (5 distinct chunking strategies) — done 2026-08-28

### Phase 2 — Retrieval
- [x] T2.1 Embedding generation + Qdrant Cloud indexing (5 collections provisioned on cluster) — done 2026-08-28
- [x] T2.2 BM25 keyword index (rank_bm25 with custom legal tokenizer) — done 2026-08-28
- [x] T2.3 Hybrid retrieval + reranker (asyncio parallel multi-collection) — done 2026-08-28

### Phase 3 — Classification, context gathering & entity extraction
- [x] T3.1 Jurisdiction classifier — done 2026-08-28
- [x] T3.2 Two-level intent classifier (UI domain intent + fine-grained intent) — done 2026-08-28
- [x] T3.3 Deterministic product classification rules engine — done 2026-08-28
- [x] T3.4 ABS assessment engine — done 2026-08-28
- [x] T3.5 Context gathering agent (intent-specific question templates) — done 2026-08-28
- [x] T3.6 Entity extractor (herbs, jurisdictions, IP types) — done 2026-08-28

### Phase 4 — Reasoning & trust layer
- [x] T4.1 Query pipeline (intent-first agentic pipeline, parallel retrieval, synthesis) — done 2026-08-28
- [x] T4.2 Citation validator (rejects unsupported citations) — done 2026-08-28
- [x] T4.3 Composite confidence scorer (with sub-task coverage) — done 2026-08-28
- [x] T4.4 Abstention/guardrail rules (hallucination protection, TKDL pointer) — done 2026-08-28

### Phase 5 — Multilingual, evaluation, stretch
- [x] T5.1 Hindi support via Bhashini (ULCA API wrapper + LLM translation fallback, citation protection) — done 2026-08-28
- [x] T5.2 Evaluation harness (100-question eval set + 8-dimension benchmark runner) — done 2026-08-28
- [x] T5.3 TKDL public-information pointer integration — done 2026-08-28
- [x] T5.4 (stretch) Knowledge graph (Neo4j AuraDB & multi-hop engine) — done 2026-08-28
