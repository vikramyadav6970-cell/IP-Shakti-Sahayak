# backend/prompts/phases.md

Ready-to-paste prompts for an AI coding agent, one per task. Manual/human steps
are called out explicitly.

**Cloud stack reminder (read before every task):**
- Database → **Supabase** (managed Postgres + pgvector). `DATABASE_URL` = Supabase
  transaction-mode pooler connection string.
- Cache / broker → **Upstash Redis**. `REDIS_URL` = Upstash `rediss://` URL.
- Object storage → **Supabase Storage** (S3-compatible). `SUPABASE_STORAGE_*` vars.
- No Docker, no local service containers — all services are cloud-managed.
- Vector store lives in **Qdrant Cloud** (managed by the `ai/` layer — backend does
  not query Qdrant directly, only the AI layer does).

---

## Phase 0 — Environment & setup

### T0.1 — Cloud infrastructure setup & .env scaffold

**Manual prerequisites (human must do these before running the agent):**

1. **Supabase project**: Create a project at supabase.com. From the dashboard:
   - Project Settings → Database → Connection string → **Transaction mode** → copy
     as `DATABASE_URL` (the pooler URL, not the direct connection URL).
   - Storage → S3 access → enable, copy the endpoint, access key, and secret.
   - Confirm the `vector` extension is enabled: Supabase dashboard → Database →
     Extensions → search "vector" → enable if not already on.

2. **Upstash Redis**: Create a database at console.upstash.com. Copy the
   `rediss://` URL (Upstash console → Details → Connection → Redis URL) as
   `REDIS_URL`.

3. **Supabase Storage bucket**: In Supabase dashboard → Storage → New bucket →
   name it `corpus-documents` (or your preferred name). Note it as
   `SUPABASE_STORAGE_BUCKET`.

**Prompt:**
```
Read /context.md, /process.md, and /backend/coding_conventions.md in full first.

Task: Set up the backend project environment for cloud-first development.

1. Create `backend/.env.example` listing every required env var with a one-line
   comment on where to get each value:

   DATABASE_URL=<Supabase transaction-mode pooler URL — Project Settings → Database → Connection string → Transaction mode>
   REDIS_URL=<Upstash Redis rediss:// URL — Upstash console → Details → Redis URL>
   SUPABASE_STORAGE_URL=<Supabase Storage S3 endpoint — Storage → S3 access>
   SUPABASE_STORAGE_KEY=<Supabase Storage S3 access key>
   SUPABASE_STORAGE_SECRET=<Supabase Storage S3 secret key>
   SUPABASE_STORAGE_BUCKET=<bucket name you created, e.g. corpus-documents>
   JWT_SECRET=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
   LLM_API_KEY=<API key for your LLM provider>
   QDRANT_URL=<Qdrant Cloud cluster URL — managed by ai/ layer; backend does not call Qdrant directly but needs the URL for health checks>
   QDRANT_API_KEY=<Qdrant Cloud API key>

2. Create `backend/app/config.py`: a pydantic-settings `Settings` class reading
   all vars above from `.env`. Every var must be typed. Add a `settings` singleton
   at the bottom (do not instantiate Settings multiple times across the app).

3. Create `backend/app/db.py`: async SQLAlchemy engine + session factory using
   `DATABASE_URL` from Settings. The engine must use asyncpg as the driver.

4. Create a minimal `backend/requirements.txt` pinning exact versions of every
   dependency in backend/coding_conventions.md's Stack section:
   - fastapi, uvicorn[standard]
   - sqlalchemy[asyncio], asyncpg, alembic
   - pydantic[email], pydantic-settings
   - redis (redis-py — for Upstash)
   - celery
   - boto3 (for Supabase Storage S3-compatible interface)
   - python-jose[cryptography] or PyJWT
   - passlib[bcrypt]
   - sentry-sdk[fastapi]

Do not add docker-compose.yml — there is no local service infra; all services are
cloud-managed.

When done: update /backend/status.md and flip T0.1 to [x] in /process.md.
```

### T0.2 — FastAPI project scaffold

**Prompt:**
```
Read /context.md, /process.md, and /backend/coding_conventions.md first.

Task: Scaffold the FastAPI project inside `backend/` following the exact folder
structure in backend/coding_conventions.md. Include:
- app/main.py: FastAPI app instance, CORS configured for the frontend's dev origin
  (read from a FRONTEND_ORIGIN env var, not hardcoded), a `/health` endpoint
  returning per-service connectivity status for: Supabase DB, Upstash Redis, and
  Supabase Storage (not just a static "ok" — actually attempt a lightweight
  connectivity probe for each), and the `/api/v1` router mounted (empty router is
  fine for now).
- A minimal Dockerfile for the backend service itself (this is for deploying the
  API to Render/Railway — not for local service infra, which doesn't exist).

The Dockerfile should:
  - Use python:3.11-slim as the base.
  - Copy requirements.txt and install deps.
  - Expose port 8000.
  - Run `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

When done: update /backend/status.md and flip T0.2 to [x] in /process.md.
```

### T0.3 — Alembic setup

**Prompt:**
```
Read /backend/coding_conventions.md first.

Task: Wire up Alembic against the async SQLAlchemy setup from T0.2 (use Alembic's
async migration template — not the sync default; confirm async_mode is set
correctly). The target database is Supabase — `DATABASE_URL` in your `.env` must
point to the Supabase connection string.

Create and apply an initial empty migration to prove the pipeline works end to end
against the live Supabase DB. Confirm in status.md that `alembic upgrade head`
runs clean against Supabase (not a local container).

When done: update /backend/status.md and flip T0.3 to [x] in /process.md.
```

---

## Phase 1 — Data model + auth

### T1.1 — Core SQLAlchemy models

**Prompt:**
```
Read /context.md (especially §2 and §5) and /backend/coding_conventions.md first.

Task: Define SQLAlchemy models for the following entities (use UUID primary keys,
created_at/updated_at timestamps on all, and appropriate foreign keys/indexes).
Target DB is Supabase Postgres:

- User: id, name, email (unique), hashed_password, language, organization, role
  (enum: USER/ADMIN/IP_FACILITATOR/CONTENT_MANAGER/RESEARCHER), created_at.
- Conversation: id, user_id (FK), created_at.
- Message: id, conversation_id (FK), role (user/assistant), content, jurisdiction,
  confidence_score, confidence_label, requires_human_review, created_at.
- Citation: id, message_id (FK), document_title, section_ref, source_url,
  jurisdiction, document_type, corpus_collection (which Qdrant collection the
  chunk came from — one of the 5 values from context.md §3a).
- Document: id, title, jurisdiction, document_type (enum: STATUTE/RULE/TREATY/
  REGISTRY_RECORD/CASE_LAW/GUIDELINE/FORM), authority, language, source_url,
  corpus_collection (which Qdrant collection this document's chunks go into).
- DocumentVersion: id, document_id (FK), version_label, effective_from,
  storage_key (points to the raw file in Supabase Storage), is_current (bool),
  ingestion_status (enum: PENDING/PROCESSING/INDEXED/FAILED).
- Product: id, user_id (FK), name, description, raw_ingredients (jsonb).
- Classification: id, product_id (FK), category, regulatory_pathway, rules_fired
  (jsonb — for auditability of the deterministic rules engine per context.md §2
  rule 6), created_at.
- IPAssessment: id, product_id (FK), ip_type, relevance_label, reasoning,
  legal_provisions (jsonb), created_at.
- ABSAssessment: id, product_id (FK), biological_resources (jsonb), origin,
  purpose, relevance_label, next_steps (jsonb), created_at.
- AuditLog: id, user_id (FK, nullable), action, resource_type, resource_id,
  metadata (jsonb), created_at. (Append-only — no update/delete path for this
  table, ever.)
- Feedback: id, message_id (FK), user_id (FK), rating, comment, created_at.
- ExpertRequest: id, user_id (FK), message_id (FK, nullable), status (enum:
  OPEN/IN_PROGRESS/RESOLVED), context, created_at.

Write the Alembic migration and run it against the live Supabase DB (not a local
container). Add indexes on all foreign keys and on frequently-filtered columns
(jurisdiction, document_type, corpus_collection, role, ingestion_status).

When done: update /backend/status.md with the final schema and flip T1.1 to [x]
in /process.md.
```

### T1.2 — JWT auth + RBAC

**Manual prerequisite:** Generate a strong `JWT_SECRET` value
(`python -c "import secrets; print(secrets.token_hex(32))"`) and set it in your
local `.env` — never commit it.

**Prompt:**
```
Read /backend/coding_conventions.md (rule 8 — don't reinvent auth/crypto) first.

Task: Implement JWT-based authentication:
- Password hashing via passlib/bcrypt.
- `/api/v1/auth/register`, `/api/v1/auth/login` (returns access + refresh token),
  `/api/v1/auth/refresh` endpoints.
- A FastAPI dependency (`get_current_user`) that validates the JWT and loads the
  User, and a `require_role(*roles)` dependency factory for RBAC-gated endpoints.
- Rate-limit the login endpoint specifically using Upstash Redis (`REDIS_URL`) to
  blunt brute-force attempts. Use redis-py with the `REDIS_URL` env var — the
  Upstash `rediss://` URL works with redis-py directly.

Write tests covering: successful register/login, wrong password rejected, expired/
invalid token rejected, role-gated endpoint rejects wrong role.

When done: update /backend/status.md with the exact request/response shape for
each auth endpoint (this is a contract the frontend depends on), and flip T1.2 to
[x] in /process.md. Add a Cross-part note so frontend knows auth is ready.
```

### T1.3 — User management endpoints

**Prompt:**
```
Read /backend/coding_conventions.md first.

Task: Implement `/api/v1/users/me` (get current user profile) and
`/api/v1/users` (admin-only list, RBAC-gated to ADMIN) with pagination.

When done: update /backend/status.md with the contract shapes and flip T1.3 to
[x] in /process.md.
```

---

## Phase 2 — Documents & ingestion trigger

### T2.1 — Document metadata endpoints

**Prompt:**
```
Read /context.md §5 (known source list) and §3a (5-collection design), and
/backend/coding_conventions.md first.

Task: Implement `/api/v1/documents` (CRUD, RBAC-gated to CONTENT_MANAGER/ADMIN for
write, open read for listing/browsing — this backs the frontend's Source Explorer)
and `/api/v1/documents/{id}/versions`. Support filtering by jurisdiction,
document_type, AND corpus_collection on the list endpoint, matching what frontend
T4.2 needs. The corpus_collection filter lets users browse the corpus by which of
the 5 Qdrant collections a document belongs to.

When done: update /backend/status.md with the contract shape and flip T2.1 to [x]
in /process.md. Add a Cross-part note.
```

### T2.2 — Object storage integration (Supabase Storage)

**Manual prerequisite:** Supabase Storage S3 credentials set in `.env` (from T0.1
manual setup steps).

**Prompt:**
```
Read /backend/coding_conventions.md (Stack section — Supabase Storage) first.

Task: Implement `app/services/storage.py` with a single abstraction (`upload`,
`get_url`, `delete`) implemented against Supabase Storage's S3-compatible API
using boto3, configured via `SUPABASE_STORAGE_URL`, `SUPABASE_STORAGE_KEY`,
`SUPABASE_STORAGE_SECRET`, and `SUPABASE_STORAGE_BUCKET` env vars. Keep the
interface abstract so swapping to Cloudflare R2 or AWS S3 later is a config change,
not a code change.

Wire document upload into the DocumentVersion creation flow from T2.1: uploading a
new version stores the raw file in Supabase Storage and records the storage key on
the DocumentVersion row.

When done: update /backend/status.md and flip T2.2 to [x] in /process.md.
```

### T2.3 — Ingestion trigger endpoint

**Prompt:**
```
Read /context.md (build order §4) and /backend/coding_conventions.md first.

Task: Implement `/api/v1/documents/{version_id}/ingest` (RBAC-gated to
CONTENT_MANAGER/ADMIN), which enqueues a Celery task calling into the `ai/`
ingestion pipeline (actual parsing/chunking/embedding logic lives in `ai/` — this
task is only the trigger + status tracking). The Celery broker is Upstash Redis
(`REDIS_URL` env var — works with Celery's `broker_url` setting directly).

Track ingestion status on DocumentVersion.ingestion_status (PENDING/PROCESSING/
INDEXED/FAILED — should already exist from T1.1's migration). Expose
`/api/v1/documents/{version_id}/ingest/status`.

Coordinate with whoever is doing ai/prompts/phases.md Phase 1 on the exact Celery
task signature the worker expects — document the agreed interface in both
backend/status.md and ai/status.md.

When done: update /backend/status.md and flip T2.3 to [x] in /process.md.
```

---

## Phase 2.5 — Context gathering API

These endpoints feed the frontend's `/context` screen (frontend T2.1). They call
into the AI layer's context gathering agent (ai/ T3.5) and entity extractor (T3.6).
Build these in parallel with or immediately after backend Phase 2.

### T2.5.1 — `/api/v1/context/questions`

**Prompt:**
```
Read /context.md §3b (6 domain intents and their context questions), ai/status.md
(check T3.5's ContextQuestion schema once available), and
/backend/coding_conventions.md first.

Task: Implement `GET /api/v1/context/questions?intent={domain_intent}` — returns
the list of context-gathering questions for the given intent.

- Route is public (no auth required — it's called at the start of a session before
  the user has logged in).
- The service layer calls into the AI layer's ContextGatheringAgent (ai/ T3.5)
  `get_questions(domain_intent)` method. If ai/ T3.5 isn't ready, stub the response
  using the schemas documented in ai/prompts/phases.md T3.5, and mark it clearly.
- Response: `{ intent: str, questions: [{ question_id, question_text, answer_type,
  options, required }] }`
- Validate that `intent` is one of: BUSINESS | EXPORT | MEDICINAL | PATENT |
  RESEARCH | OTHER (reject 422 otherwise).

When done: update /backend/status.md with the confirmed contract and flip T2.5.1
to [x] in /process.md. Add a Cross-part note — frontend T2.1 depends on this.
```

### T2.5.2 — `/api/v1/context/process`

**Prompt:**
```
Read /context.md §1 (pipeline stages 2–3) and /backend/coding_conventions.md first.
Check ai/status.md for the EntitySet and ContextObject schemas from T3.5 and T3.6.

Task: Implement `POST /api/v1/context/process`.

- Request: `{ intent: str, answers: Record<str, str | list[str]>,
              question: str | None }` (the full question is optional at this stage
  — if provided, it's used by the entity extractor for richer extraction).
- The service layer calls:
  1. AI T3.5's `parse_answers(domain_intent, raw_answers)` → ContextObject
  2. AI T3.6's `extract(context_object, question)` → EntitySet
- Response: `{ context_object: {...}, entity_set: {...}, session_id: str }`
  The session_id is a UUID generated here and stored server-side (cache in Upstash
  Redis with a 1-hour TTL, keyed by session_id) — the frontend sends it with
  subsequent `/api/v1/chat` requests to look up context without re-sending the
  full ContextObject every time.
- If either AI component isn't ready, stub both and mark clearly in status.md.

When done: update /backend/status.md with the confirmed contract and flip T2.5.2
to [x] in /process.md. Add a Cross-part note — frontend T2.1, AI T4.1, and
backend T3.1 all depend on the session_id pattern established here.
```

---

## Phase 3 — Chat / query API

### T3.1 — `/api/v1/chat` endpoint

**Prompt:**
```
Read /context.md §2 (hard constraints — this endpoint is where they get enforced
end-to-end) and /backend/coding_conventions.md first.

Task: Implement `POST /api/v1/chat`:
- Request: `{ question: str, domain_intent: str, session_id: str | None,
              jurisdiction: str, language: str, conversation_id: str | None }`.
  If session_id is provided, look up the ContextObject + EntitySet from Upstash
  Redis cache (set by T2.5.2) and pass them to the AI query pipeline. If cache
  miss, proceed without context (log a warning).
- The service layer calls into the `ai/` layer's query pipeline (check
  ai/status.md for the current function signature/interface — if it's not ready
  yet, build against a documented interface and mock it, and note the mock
  clearly).
- Persist the Message + Citations (including corpus_collection on each citation,
  per T1.1's Citation model) + Conversation (create one if conversation_id is
  null) per the models from T1.1.
- Response shape must match exactly what's documented for frontend in
  frontend/coding_conventions.md's Phase 2 section (answer, confidence,
  confidence_label, classification, citations[], requires_human_review).
- If the AI layer returns zero citations or below-threshold confidence, ensure
  requires_human_review is true — never let a low-confidence answer look
  confident on the wire.

Write tests covering the persistence side (mock the AI layer call).

When done: update /backend/status.md with the final, confirmed contract (mark it
CONFIRMED, not draft) and flip T3.1 to [x] in /process.md. Add a Cross-part note —
this unblocks frontend T2.3.
```

### T3.2 — Conversation history endpoints

**Prompt:**
```
Read /backend/coding_conventions.md first.

Task: Implement `GET /api/v1/chat/conversations` (list current user's
conversations) and `GET /api/v1/chat/conversations/{id}` (full message + citation
history for one conversation), both scoped to the authenticated user (users can
never see others' conversations except ADMIN).

When done: update /backend/status.md and flip T3.2 to [x] in /process.md.
```

### T3.3 — Feedback endpoint

**Prompt:**
```
Task: Implement `POST /api/v1/feedback` accepting message_id, rating, optional
comment, persisting to the Feedback model from T1.1.

When done: update /backend/status.md and flip T3.3 to [x] in /process.md.
```

---

## Phase 4 — Classification / IP / ABS / sources / expert

### T4.1 — `/api/v1/classification`

**Prompt:**
```
Read /context.md §2 rule 6 (classification must be deterministic/auditable) and
/backend/coding_conventions.md first.

Task: Implement `POST /api/v1/classification` accepting the wizard answers from
frontend T3.1 (product type, derived-from-authoritative-text, formulation novelty,
biological resources used). This endpoint calls a rules-engine function in the
`ai/` layer (see ai/prompts/phases.md Phase 3, T3.3) rather than embedding
classification logic in the backend itself — the backend's job is to persist the
Classification record (including `rules_fired` for auditability) and shape the
response. If the ai/ rules engine isn't ready, stub it behind a clearly-marked
interface matching the documented contract, and note it in status.md.

When done: update /backend/status.md with the finalized contract and flip T4.1 to
[x] in /process.md. Add a Cross-part note — this unblocks frontend T3.1/T3.2.
```

### T4.2 — `/api/v1/ip` and `/api/v1/abs`

**Prompt:**
```
Read /backend/coding_conventions.md first.

Task: Implement `POST /api/v1/ip` (returns per-IP-type relevance assessment for a
classified product, backing frontend's "IP protection map" in T3.2) and
`POST /api/v1/abs` (backing frontend's ABS wizard, T4.1). Both persist to
IPAssessment/ABSAssessment respectively and call into the AI layer for the actual
reasoning (see ai/prompts/phases.md Phase 3, T3.4 for ABS).

When done: update /backend/status.md with both contracts and flip T4.2 to [x] in
/process.md.
```

### T4.3 — `/api/v1/sources`

**Prompt:**
```
Task: If not already fully covered by T2.1's `/api/v1/documents` endpoint, add
whatever's missing to fully back the frontend Source Explorer (T4.2 in
frontend/prompts/phases.md) — e.g. full-text search across document titles/
sections and filtering by corpus_collection if not already present. Otherwise,
confirm in status.md that T2.1 already covers this and this task is a no-op.

When done: update /backend/status.md and flip T4.3 to [x] in /process.md.
```

### T4.4 — Expert escalation + audit log wiring

**Prompt:**
```
Read /context.md §2 (escalation is a hard requirement, not optional) and
/backend/coding_conventions.md first.

Task: Implement `POST /api/v1/expert` (creates an ExpertRequest, RBAC-open to any
authenticated USER; list/resolve endpoints RBAC-gated to IP_FACILITATOR/ADMIN).
Then do a pass across every endpoint built so far in Phases 1–4 and ensure each
one that reads or writes sensitive/substantive data (chat answers, classification
results, document access, expert requests) writes an AuditLog entry — this is a
DPDP-alignment requirement, not a nice-to-have. Write a short test asserting an
AuditLog row is created for at least the chat and classification flows.

When done: update /backend/status.md and flip T4.4 to [x] in /process.md.
```

---

## Phase 5 — Security, ops, deploy

### T5.1 — Rate limiting & input hardening

**Prompt:**
```
Read /backend/coding_conventions.md first.

Task: Add Upstash Redis-backed rate limiting (`REDIS_URL` env var) to all
public-facing endpoints (not just login), tuned per endpoint sensitivity
(chat/classification lower limits than read-only listing endpoints). Use redis-py
with the `REDIS_URL` — Upstash's `rediss://` URL works with redis-py's standard
connection. Review every Pydantic schema for missing length/format constraints on
free-text fields (question text, feedback comments). Add basic request size limits
at the ASGI/middleware level.

When done: update /backend/status.md and flip T5.1 to [x] in /process.md.
```

### T5.2 — Structured audit logging pass

**Prompt:**
```
Task: Review the AuditLog coverage from T4.4 for completeness against DPDP-style
principles: log who accessed what, when, and why (action type), without logging
sensitive payload contents unnecessarily (log that a chat query happened and its
citations, not duplicate raw PII). Document the audit log's retention/rotation plan
(even if just a README note for now — a full retention job is out of scope for MVP).

When done: update /backend/status.md and flip T5.2 to [x] in /process.md.
```

### T5.3 — Monitoring & health checks

**Manual prerequisite:** A free Sentry account + DSN.

**Prompt:**
```
Task: Integrate Sentry for error tracking (DSN from a SENTRY_DSN env var, never
hardcoded — add it to .env.example). Expand the `/health` endpoint from T0.2 to
check all three cloud services individually and return per-service status:
- Supabase DB: attempt a lightweight query (e.g. `SELECT 1`)
- Upstash Redis: ping via redis-py using REDIS_URL
- Supabase Storage: attempt a lightweight operation (e.g. list the bucket)
Return per-dependency status so ops can see exactly what's degraded.

When done: update /backend/status.md and flip T5.3 to [x] in /process.md.
```

### T5.4 — Deploy + CI

**Manual prerequisite:** A Render or Railway account connected to the repo.
Supabase and Upstash are already cloud-managed — no managed DB/Redis to provision
separately. Just set the env vars from your `.env` in the hosting dashboard.

**Prompt:**
```
Task: Add a GitHub Actions workflow running lint + tests on every push (tests run
against the real Supabase test DB — use TEST_DATABASE_URL from the secret in CI
settings, not a local container). Prepare deployment config for the chosen host
(Render/Railway):
- Backend API service: Dockerfile from T0.2, env vars from .env.example all set
  in the hosting dashboard.
- Celery worker service: same Docker image, different start command
  (`celery -A app.workers.celery_app worker --loglevel=info`).
- Migration step: a release/pre-deploy command running `alembic upgrade head`
  targeting the live Supabase DB before the new app instance starts.

All services connect to the same Supabase project and Upstash Redis — no
additional DB or Redis provisioning needed. Document required env vars in
README.md. Do a final smoke test against the deployed instance once the human has
set all env vars.

When done: update /backend/status.md, flip T5.4 to [x] in /process.md, and update
README.md §5 with the real deployed URL.
```
