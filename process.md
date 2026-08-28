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

## Cross-part notes

- **AI Layer / Embeddings (T0.3 — 2026-08-28):** Verified `BAAI/bge-m3` embedding model. Vector output dimensionality is **1024** (dense vectors, normalized). All 5 Qdrant Cloud collections in T2.1 and any vector schema in DB/backend must be configured with dimension = 1024, Cosine distance.

---

## Frontend

### Phase 0 — Setup
- [ ] T0.1 Scaffold Vite + React + TS project, base tooling
- [ ] T0.2 Tailwind + shadcn/ui installed and themed
- [ ] T0.3 Env config, API client base, routing skeleton

### Phase 1 — Core shell
- [ ] T1.1 App shell/layout, nav, disclaimer banner
- [ ] T1.2 Jurisdiction toggle component + global state
- [ ] T1.3 Landing page

### Phase 2 — Chat / RAG interface
- [ ] T2.1 Chat UI with streaming
- [ ] T2.2 Citation card + confidence badge components
- [ ] T2.3 API service layer wired to backend `/chat` (mocked until backend ready)

### Phase 3 — Product classification wizard
- [ ] T3.1 Multi-step wizard shell
- [ ] T3.2 Classification result view + IP protection map

### Phase 4 — ABS / Source Explorer / Escalation / Dashboard
- [ ] T4.1 ABS compliance wizard
- [ ] T4.2 Source Explorer page
- [ ] T4.3 Human expert escalation flow
- [ ] T4.4 Admin/IP dashboard (corpus stats, accuracy metrics)

### Phase 5 — Auth, i18n, polish, deploy
- [ ] T5.1 Auth UI (login/roles)
- [ ] T5.2 Hindi/English i18n
- [ ] T5.3 Accessibility + responsive pass
- [ ] T5.4 Deploy to Vercel

---

## Backend

### Phase 0 — Setup
- [ ] T0.1 Docker Compose (Postgres+pgvector, Redis, MinIO)
- [ ] T0.2 FastAPI project scaffold, settings/env management
- [ ] T0.3 Alembic wired up, first migration

### Phase 1 — Data model + auth
- [ ] T1.1 Core SQLAlchemy models (users, documents, conversations, citations, etc.)
- [ ] T1.2 JWT auth + RBAC (USER/ADMIN/IP_FACILITATOR/CONTENT_MANAGER/RESEARCHER)
- [ ] T1.3 User management endpoints

### Phase 2 — Documents + ingestion trigger
- [ ] T2.1 Document + document_version models, metadata schema
- [ ] T2.2 Object storage integration (S3/MinIO)
- [ ] T2.3 Ingestion trigger endpoint (calls into `ai/` pipeline via Celery task)

### Phase 3 — Chat/query API
- [ ] T3.1 `/api/v1/chat` endpoint contract + implementation calling AI layer
- [ ] T3.2 Conversation/message/citation persistence
- [ ] T3.3 Feedback endpoint

### Phase 4 — Classification / IP / ABS / sources / expert
- [ ] T4.1 `/api/v1/classification` endpoint
- [ ] T4.2 `/api/v1/ip` and `/api/v1/abs` endpoints
- [ ] T4.3 `/api/v1/sources` (Source Explorer backing API)
- [ ] T4.4 `/api/v1/expert` escalation endpoint + audit_log wiring

### Phase 5 — Security, ops, deploy
- [ ] T5.1 Rate limiting, input validation hardening
- [ ] T5.2 Structured audit logging pass (DPDP-aligned)
- [ ] T5.3 Monitoring (Sentry) + health checks
- [ ] T5.4 Deploy (Render/Railway) + CI

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
- [ ] T3.1 Jurisdiction classifier
- [ ] T3.2 Two-level intent classifier (UI domain intent + fine-grained intent)
- [ ] T3.3 Deterministic product classification rules engine
- [ ] T3.4 ABS assessment engine
- [ ] T3.5 Context gathering agent (intent-specific question templates)
- [ ] T3.6 Entity extractor (herbs, jurisdictions, IP types)

### Phase 4 — Reasoning & trust layer
- [ ] T4.1 Query pipeline (intent-first agentic pipeline, parallel retrieval, synthesis)
- [ ] T4.2 Citation validator (rejects unsupported citations)
- [ ] T4.3 Composite confidence scorer (with sub-task coverage)
- [ ] T4.4 Abstention/guardrail rules (hallucination protection, TKDL pointer)

### Phase 5 — Multilingual, evaluation, stretch
- [ ] T5.1 Hindi support via Bhashini (ASR/translation/TTS)
- [ ] T5.2 Evaluation harness (RAGAS) + 100-question eval set
- [ ] T5.3 TKDL public-information pointer integration
- [ ] T5.4 (stretch) Knowledge graph (Neo4j AuraDB)
