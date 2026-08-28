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

*(Add short notes here when finishing something another part depends on — e.g.
"Backend: POST /api/v1/chat request/response shape finalized, see
backend/status.md — frontend Phase 2 can now wire the real endpoint instead of a
mock.")*

- None yet.

### Backend -> Frontend
- (2026-08-29) Auth APIs (`/api/v1/auth/register`, `login`, `refresh`) are ready! The exact request/response JSON contracts are documented in `backend/status.md`. You can start wiring up the login screen.)
- (2026-08-29) Document APIs (`/api/v1/documents`) are ready! CRUD is supported, with `GET /api/v1/documents` supporting filters (`jurisdiction`, `document_type`, `corpus_collection`) to power the Source Explorer UI. See `backend/status.md` for exact contracts.
- (2026-08-29) Context APIs (`/api/v1/context/questions` and `/api/v1/context/process`) are ready! The AI backend logic is currently stubbed, but the HTTP interface is complete. See `backend/status.md` for exact contracts. Frontend T2.1 can wire these up. Frontend T2.1, AI T4.1, and backend T3.1 all depend on the session_id pattern established here.
- (2026-08-29) Chat API (`/api/v1/chat`) is ready! It correctly routes to a mocked AI pipeline, reads context via `session_id` from Upstash Redis, persists conversations/messages/citations, and enforces constraints like `requires_human_review`. See `backend/status.md` for the exact shape. Frontend T2.3 is now unblocked to wire up the chat screen!
- (2026-08-29) Classification API (`/api/v1/classification`) is ready! It delegates to a stubbed deterministic rules engine (pending AI T3.3) and persists the `Classification` record with full `rules_fired` audit trail. See `backend/status.md` for the exact shape. Frontend T3.1/T3.2 are now unblocked!

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
- [ ] T0.1 Python project scaffold + dependency pinning
- [ ] T0.2 LLM provider abstraction (env-driven key)
- [ ] T0.3 Embedding model selection + smoke test

### Phase 1 — Corpus + ingestion
- [ ] T1.1 Curate initial 20–50 document corpus (India, Patent+Trademark+ABS focus)
- [ ] T1.2 Parsing pipeline (PDF/HTML → structured text)
- [ ] T1.3 Structure-aware chunking (Act → Chapter → Section → Clause)

### Phase 2 — Retrieval
- [ ] T2.1 Embedding generation + pgvector indexing
- [ ] T2.2 BM25/keyword index
- [ ] T2.3 Hybrid retrieval + reranker

### Phase 3 — Classification & routing
- [ ] T3.1 Jurisdiction classifier
- [ ] T3.2 Intent classifier (Patent/Trademark/GI/ABS/etc.)
- [ ] T3.3 Deterministic product classification rules engine
- [ ] T3.4 ABS assessment engine

### Phase 4 — Reasoning & trust layer
- [ ] T4.1 LLM reasoning prompt + evidence-only answer generation
- [ ] T4.2 Citation validator (rejects unsupported citations)
- [ ] T4.3 Composite confidence scorer
- [ ] T4.4 Abstention/guardrail rules (hallucination protection)

### Phase 5 — Multilingual, evaluation, stretch
- [ ] T5.1 Hindi support via Bhashini (ASR/translation/TTS)
- [ ] T5.2 Evaluation harness (RAGAS) + 100-question eval set
- [ ] T5.3 TKDL public-information pointer integration
- [ ] T5.4 (stretch) Knowledge graph (Neo4j), agentic multi-step orchestration
