# backend/coding_conventions.md

Read `/context.md` and `/process.md` before this file. This file governs how code
is written inside `backend/` specifically.

## Stack (authoritative)

- **Python 3.11+**, **FastAPI**, **Pydantic v2** for schemas/validation.
- **SQLAlchemy 2.0** (async) + **Alembic** for migrations.
- **Database: Supabase** (managed PostgreSQL). Connect via Supabase's
  **transaction-mode pooler URL** for the async SQLAlchemy engine
  (`DATABASE_URL` env var — get it from Supabase dashboard → Project Settings →
  Database → Connection string → Transaction mode). Do not introduce a local
  Postgres container; the whole team shares the same Supabase project in dev.
  pgvector extension is pre-enabled on Supabase — no `CREATE EXTENSION` migration
  needed (but document in status.md that it was verified).
- **Cache / rate limiting / Celery broker: Upstash Redis** (serverless). Use the
  `REDIS_URL` env var (Upstash provides a `rediss://` URL — copy it from the
  Upstash console → REST API tab). `redis-py` and Celery both accept this URL
  directly with no code changes. Do NOT spin up a local Redis container.
- **Object storage: Supabase Storage** (S3-compatible). Use boto3 with the
  Supabase S3 endpoint (`SUPABASE_STORAGE_URL`, `SUPABASE_STORAGE_KEY`,
  `SUPABASE_STORAGE_SECRET`, `SUPABASE_STORAGE_BUCKET` env vars — get the S3
  credentials from Supabase dashboard → Storage → S3 access). The storage
  abstraction in `app/services/storage.py` must stay interface-based so swapping
  to Cloudflare R2 or AWS S3 later is a config change, not a code change.
- **Celery** for background jobs (document ingestion, embedding generation).
  Broker = Upstash Redis (`REDIS_URL`). Workers run locally in dev; deploy as a
  separate worker process on Render/Railway in prod.
- **JWT** (via `python-jose` or `PyJWT`) for auth; RBAC roles: `USER`, `ADMIN`,
  `IP_FACILITATOR`, `CONTENT_MANAGER`, `RESEARCHER`.
- There is **no Docker Compose dev infra** for this project. All stateful services
  (DB, Redis, Storage) are cloud-managed. Document required env vars in
  `.env.example`; never commit real credentials.

## Hard rules

1. **Layered architecture, always:** `api/` (route handlers — thin, no business
   logic) → `services/` (business logic) → `repositories/` (DB access). A route
   handler should read like: validate input (Pydantic does this), call a service,
   return the service's result. If you find yourself writing SQLAlchemy queries
   directly inside a route handler, stop and move it to a repository.
2. **Never hardcode secrets.** Every credential (LLM API key, `DATABASE_URL`,
   `REDIS_URL`, Supabase Storage keys, JWT secret, Qdrant keys) comes from
   environment variables via a single `Settings` object (pydantic-settings).
   `.env.example` must list every var with a comment on where to obtain it, and
   must never contain a real secret.
3. **Every schema change ships with an Alembic migration** in the same task/commit
   — never let models.py drift from the actual DB schema.
4. **No raw string-concatenated SQL, ever.** Use SQLAlchemy's query builder/ORM or
   parameterized `text()` calls only.
5. **Structured, not print-based, logging.** Use Python's `logging` module with a
   JSON formatter in production; every request that touches an AI answer must log
   enough to reconstruct what evidence/citations were used (this feeds the audit
   log requirement in context.md).
6. **Production-grade only:** every endpoint has explicit error handling (don't
   let an unhandled exception 500 silently — return a structured error body), input
   validation via Pydantic (reject, don't sanitize-and-hope), and a docstring
   explaining what it does. No endpoint should be left half-implemented and
   presented as done — mark it `[~]` in status.md instead.
7. **No unnecessary dependencies.** Before adding a library, check if the Stack
   list above already covers the need. If you genuinely need something new,
   name it explicitly in your task summary and in status.md with a one-line
   justification.
8. **Don't build your own auth, crypto, or password hashing.** Use established
   libraries (`passlib`/`bcrypt`, `python-jose`) — this is exactly the kind of
   "don't reinvent a library" case that matters most for security.
9. **API versioning:** all routes under `/api/v1/...` as already specified in
   `context.md`'s architecture notes. Don't introduce a differently-versioned or
   unversioned route.
10. **Tests required for every service function with real logic** (not simple
    passthroughs) — pytest, with a test DB. Use SQLite in-memory for pure
    relational unit tests; for anything requiring pgvector-specific behavior, use
    the real Supabase test/staging DB (document the test DB URL in `.env.example`
    as `TEST_DATABASE_URL`).

## Folder structure

```
backend/
├── coding_conventions.md
├── status.md
├── prompts/
│   └── phases.md
├── .env.example               # All cloud service env vars documented here
├── requirements.txt / pyproject.toml
├── alembic/
├── app/
│   ├── main.py
│   ├── config.py             # Settings object (pydantic-settings, reads .env)
│   ├── api/                  # route handlers, one router module per resource
│   ├── schemas/               # Pydantic request/response models
│   ├── models/                # SQLAlchemy ORM models
│   ├── repositories/
│   ├── services/
│   │   └── storage.py        # Supabase Storage interface (boto3 under the hood)
│   ├── security/               # auth, RBAC, rate limiting (Upstash Redis)
│   └── workers/                # Celery task definitions
└── tests/
```

## API contract discipline

Whenever you finalize or change a request/response schema for an endpoint the
frontend or AI layer depends on, **immediately update `backend/status.md` with the
exact JSON shape** and add a line under `process.md` → Cross-part notes. Don't make
the other tracks reverse-engineer your Pydantic models from source.

## Definition of done for any backend task

- `alembic upgrade head` runs clean from a fresh Supabase DB (run against the
  real Supabase connection, not a local container).
- New/changed endpoints documented (FastAPI's auto-generated OpenAPI docs count,
  but also update `status.md` with the shape for cross-team visibility).
- Relevant tests pass (`pytest`).
- No secrets committed, `.env.example` updated if new vars were introduced.
- `status.md` and `process.md` updated.
