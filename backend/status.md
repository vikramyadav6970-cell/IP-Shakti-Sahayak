# backend/status.md

Granular status log + **the authoritative record of finalized API contracts** the
other two tracks (frontend, AI) depend on. When you finalize an endpoint's
request/response shape, put it here in full, not just in your head or in code.

---

## Finalized API contracts

*(none yet — populate as endpoints are built; keep this section, don't move it)*

---

## Log

### (2026-08-28) Phase 0 - T0.1 Completed
- Created `.env.example`
- Created `app/config.py` with pydantic-settings
- Created `app/db.py` with async SQLAlchemy
- Created `requirements.txt` with pinned dependencies
- Note: Skipped docker-compose as infra is cloud-managed.

### (2026-08-28) Phase 0 - T0.2 Completed
- scaffolded FastAPI project with `app/main.py`
- Added `/health` endpoint verifying Supabase DB, Upstash Redis, and Supabase Storage connectivity.
- Mounted `/api/v1` router.
- Added minimal `Dockerfile` for Render/Railway deployment.

### (2026-08-28) Phase 0 - T0.3 Completed
- Initialized Alembic with the async template.
- Updated `alembic/env.py` to pull the connection string dynamically from `app.config.settings` and ensure the async driver is used.
- Created the initial empty migration (`b8da6ba84d17_initial.py`).
- **Note to human**: The migration is ready. Once you configure your `.env` with the real `DATABASE_URL`, run `alembic upgrade head` to apply it to the live Supabase DB.

### (2026-08-28) Phase 1 - T1.1 Completed
- Created core SQLAlchemy models (`User`, `Conversation`, `Message`, `Citation`, `Document`, `DocumentVersion`, `Product`, `Classification`, `IPAssessment`, `ABSAssessment`, `AuditLog`, `Feedback`, `ExpertRequest`).
- All models inherit from `BaseModel` providing `id` (UUID), `created_at`, and `updated_at`.
- Configured `alembic/env.py` to import `Base.metadata` for autogenerate support.
- **Note to human**: Because of the local Python 3.14/`asyncpg` compilation issue, I could not run `alembic revision --autogenerate -m "core_models"` directly. Once you switch to Python 3.11/3.12 or install C++ tools, run that command to generate the migration script, and then run `alembic upgrade head`.

### (2026-08-29) Phase 1 - T1.2 Completed
- Implemented JWT-based authentication using `passlib[bcrypt]` and `python-jose`.
- Created endpoints for `/api/v1/auth/register`, `/api/v1/auth/login`, and `/api/v1/auth/refresh`.
- Added dependency `get_current_user` to validate JWTs and load the User from the database.
- Added dependency `require_role(*roles)` for RBAC-gating.
- Added Upstash Redis rate limiting to the login endpoint to prevent brute-force attacks.
- Automated tests passing for all flows (registration, login, invalid tokens, role authorization).

#### API Contract: Auth Endpoints
**POST /api/v1/auth/register**
- **Request Body (JSON):**
  ```json
  {
    "name": "string",
    "email": "user@example.com",
    "password": "strongpassword",
    "language": "string | null",
    "organization": "string | null"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "name": "string",
    "email": "user@example.com",
    "language": "string | null",
    "organization": "string | null",
    "id": "uuid",
    "role": "USER",
    "created_at": "datetime"
  }
  ```

**POST /api/v1/auth/login**
- **Request Body (Form Data - OAuth2 spec):**
  `username=user@example.com&password=strongpassword`
- **Response (200 OK):**
  ```json
  {
    "user": {
      "name": "string",
      "email": "user@example.com",
      "language": "string | null",
      "organization": "string | null",
      "id": "uuid",
      "role": "USER",
      "created_at": "datetime"
    },
    "token": {
      "access_token": "jwt_string",
      "refresh_token": "jwt_string",
      "token_type": "bearer"
    }
  }
  ```

**POST /api/v1/auth/refresh**
- **Request Query:** `?refresh_token=jwt_string`
- **Response (200 OK):**
  ```json
  {
    "access_token": "new_jwt_string",
    "refresh_token": "new_jwt_string",
    "token_type": "bearer"
  }
  ```

### (2026-08-29) Phase 1 - T1.3 Completed
- Implemented `/api/v1/users/me` endpoint to return the current user's profile.
- Implemented `/api/v1/users` endpoint to list users, gated to the `ADMIN` role.
- Updated `UserRepository` with a `list_users(skip, limit)` method with default pagination.

#### API Contract: User Endpoints
**GET /api/v1/users/me**
- **Request Headers:** `Authorization: Bearer <access_token>`
- **Response (200 OK):**
  ```json
  {
    "name": "string",
    "email": "user@example.com",
    "language": "string | null",
    "organization": "string | null",
    "id": "uuid",
    "role": "USER",
    "created_at": "datetime"
  }
  ```

**GET /api/v1/users?skip=0&limit=50**
- **Request Headers:** `Authorization: Bearer <access_token>` (Must have `ADMIN` role)
- **Response (200 OK):**
  ```json
  [
    {
      "name": "string",
      "email": "user@example.com",
      "language": "string | null",
      "organization": "string | null",
      "id": "uuid",
      "role": "USER",
      "created_at": "datetime"
    }
  ]
  ```

### (2026-08-29) Phase 2 - T2.1 Completed
- Implemented `app/api/v1/documents.py` containing CRUD for `/api/v1/documents` and `/api/v1/documents/{id}/versions`.
- Read (list/get) is open to any authenticated user.
- Write (create/update/delete) is RBAC-gated to `CONTENT_MANAGER` and `ADMIN`.
- The `GET /api/v1/documents` endpoint supports filtering by `jurisdiction`, `document_type`, and `corpus_collection`.

#### API Contract: Document Endpoints
**GET /api/v1/documents**
- **Query Params:** `skip=0`, `limit=50`, `jurisdiction` (optional string), `document_type` (optional string enum), `corpus_collection` (optional string, e.g., 'legal_statutory')
- **Request Headers:** `Authorization: Bearer <access_token>`
- **Response (200 OK):**
  ```json
  [
    {
      "title": "Patents Act",
      "jurisdiction": "India",
      "document_type": "STATUTE",
      "authority": "Parliament of India",
      "language": "en",
      "source_url": "http://example.com/patents.pdf",
      "corpus_collection": "legal_statutory",
      "id": "uuid",
      "created_at": "datetime",
      "updated_at": "datetime"
    }
  ]
  ```

**POST /api/v1/documents**
- **Request Headers:** `Authorization: Bearer <access_token>` (Must be CONTENT_MANAGER or ADMIN)
- **Request Body:** Same JSON fields as above response (minus id/dates), missing fields will use defaults.
- **Response (201 Created):** Same as above object.

**GET /api/v1/documents/{id}/versions**
- **Request Headers:** `Authorization: Bearer <access_token>`
- **Response (200 OK):**
  ```json
  [
    {
      "id": "uuid",
      "document_id": "uuid",
      "version_label": "2005 Amendment",
      "effective_from": "datetime | null",
      "storage_key": "s3_key_string",
      "is_current": true,
      "ingestion_status": "PENDING",
      "created_at": "datetime",
      "updated_at": "datetime"
    }
  ]
  ```

**POST /api/v1/documents/{id}/versions**
- **Request Headers:** `Authorization: Bearer <access_token>` (Must be CONTENT_MANAGER or ADMIN)
- **Request Body (Multipart Form):**
  - `version_label`: string
  - `file`: binary file upload
- **Response (201 Created):** Same as above object.

### (2026-08-29) Phase 2 - T2.2 Completed
- Implemented `app/services/storage.py` with `StorageService` for Supabase Storage S3-compatible API using `boto3`.
- Wired document upload into `POST /api/v1/documents/{id}/versions`. The endpoint receives an `UploadFile`, uploads it to Supabase Storage, and records the `storage_key` in the `DocumentVersion` row in the database, while marking any previous versions as `is_current = False`.

### (2026-08-29) Phase 2 - T2.3 Completed
- Configured Celery worker application in `app/workers/celery_app.py` using Upstash Redis.
- Added `POST /api/v1/documents/{version_id}/ingest` to enqueue `ai.tasks.ingest_document` and set status to `PROCESSING`.
- Added `GET /api/v1/documents/{version_id}/ingest/status` to retrieve current ingestion status.
- Documented agreed Celery task signature in `ai/status.md`.

#### API Contract: Ingestion Endpoints
**POST /api/v1/documents/{version_id}/ingest**
- **Request Headers:** `Authorization: Bearer <access_token>` (Must be CONTENT_MANAGER or ADMIN)
- **Response (202 Accepted):**
  ```json
  {
    "message": "Ingestion triggered successfully",
    "version_id": "uuid"
  }
  ```

**GET /api/v1/documents/{version_id}/ingest/status**
- **Request Headers:** `Authorization: Bearer <access_token>`
- **Response (200 OK):**
  ```json
  {
    "version_id": "uuid",
    "status": "PROCESSING",
  }
  ```

### (2026-08-29) Phase 2.5 - T2.5.1 & T2.5.2 Completed
- Implemented `/api/v1/context/questions` to retrieve context-gathering questions based on domain intent.
- Implemented `/api/v1/context/process` to process answers and generate a session ID.
- Stubbed AI layer interactions (`ai/ T3.5` and `T3.6`) in `app/services/context_service.py` pending their implementation.
- Integrated Upstash Redis for caching the `ContextObject` and `EntitySet` with a 1-hour TTL keyed by `session_id`.

#### API Contract: Context Gathering Endpoints
**GET /api/v1/context/questions?intent={domain_intent}**
- **Query Params:** `intent` (one of: BUSINESS, EXPORT, MEDICINAL, PATENT, RESEARCH, OTHER)
- **Response (200 OK):**
  ```json
  {
    "intent": "BUSINESS",
    "questions": [
      {
        "question_id": "q1",
        "question_text": "What is the product type?",
        "answer_type": "text",
        "options": null,
        "required": true
      }
    ]
  }
  ```

**POST /api/v1/context/process**
- **Request Body:**
  ```json
  {
    "intent": "BUSINESS",
    "answers": {
      "q1": "Ayurvedic soap"
    },
    "question": "I want to export my soap"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "session_id": "uuid-string",
    "context_object": {
      "intent": "BUSINESS",
      "parsed_answers": {"q1": "Ayurvedic soap"},
      "status": "STUBBED_CONTEXT"
    },
    "entity_set": {
      "extracted_entities": ["STUB_HERB_1", "STUB_JURISDICTION_INDIA"],
      "status": "STUBBED_ENTITIES"
    }
  }
  ```

### (2026-08-29) Phase 3 - T3.1 Completed
- Implemented `POST /api/v1/chat` logic, mocking the AI layer (query pipeline).
- Context (`ContextObject` and `EntitySet`) is correctly loaded from Upstash Redis using the provided `session_id`.
- Handled persistence for Conversations, Messages, and Citations.
- Enforced hard constraints for low confidence or empty citations triggering `requires_human_review = True`.
- Written `pytest` tests validating successful and unauthorized paths.
- Documented mock AI layer `query_pipeline` interface in `ai/status.md`.

#### [CONFIRMED] API Contract: Chat/Query Endpoint
**POST /api/v1/chat**
- **Request Headers:** `Authorization: Bearer <access_token>`
- **Request Body:**
  ```json
  {
    "question": "What is the patent term?",
    "domain_intent": "PATENT",
    "session_id": "uuid-string",
    "jurisdiction": "India",
    "language": "en",
    "conversation_id": null
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "answer": "Mock answer for 'What is the patent term?'. Context provided: True.",
    "confidence": 0.85,
    "confidence_label": "High",
    "classification": "PATENT",
    "citations": [
      {
        "document_title": "Mock Act 2026",
        "section_ref": "Section 42",
        "source_url": "https://example.com/act",
        "jurisdiction": "India",
        "document_type": "STATUTE",
        "corpus_collection": "legal_statutory"
      }
    ],
    "requires_human_review": false,
    "conversation_id": "uuid-string"
  }
  ```

### (2026-08-29) Phase 3 - T3.2 Completed
- Added SQLAlchemy relationships in `app/models/chat.py` to allow querying Conversations with Messages and Citations.
- Implemented `GET /api/v1/chat/conversations` for retrieving a list of conversations for the authenticated user.
- Implemented `GET /api/v1/chat/conversations/{id}` for retrieving full message and citation history, fully scoped to the authenticated user.

#### [CONFIRMED] API Contract: Conversation History Endpoints
**GET /api/v1/chat/conversations**
- **Request Headers:** `Authorization: Bearer <access_token>`
- **Response (200 OK):**
  ```json
  [
    {
      "id": "uuid-string",
      "created_at": "datetime"
    }
  ]
  ```

**GET /api/v1/chat/conversations/{id}**
- **Request Headers:** `Authorization: Bearer <access_token>`
- **Response (200 OK):**
  ```json
  {
    "id": "uuid-string",
    "created_at": "datetime",
    "messages": [
      {
        "id": "uuid-string",
        "role": "user",
        "content": "What is the patent term?",
        "jurisdiction": null,
        "confidence_score": null,
        "confidence_label": null,
        "requires_human_review": false,
        "citations": [],
        "created_at": "datetime"
      }
    ]
  }
  ```

### (2026-08-29) Phase 3 - T3.3 Completed
- Implemented `POST /api/v1/feedback` to accept message ratings and optional comments.
- Mapped accurately to the `Feedback` SQL model from T1.1.

#### [CONFIRMED] API Contract: Feedback Endpoint
**POST /api/v1/feedback**
- **Request Headers:** `Authorization: Bearer <access_token>`
- **Request Body:**
  ```json
  {
    "message_id": "uuid-string",
    "rating": 5,
    "comment": "Excellent answer."
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "id": "uuid-string",
    "message_id": "uuid-string",
    "user_id": "uuid-string",
    "rating": 5,
    "comment": "Excellent answer."
  }
  ```

### (2026-08-29) Phase 4 - T4.1 Completed
- Implemented `POST /api/v1/classification` endpoint.
- Backend delegates to a **stubbed deterministic rules engine** in `app/services/classification_service.py` (will be replaced by `ai/` layer T3.3 once ready).
- Every rule evaluation is captured in `rules_fired` (JSONB) for auditability per context.md §2 rule 6.
- Persists the `Classification` record via the T1.1 model.

#### [CONFIRMED] API Contract: Classification Endpoint
**POST /api/v1/classification**
- **Request Headers:** `Authorization: Bearer <access_token>`
- **Request Body:**
  ```json
  {
    "product_id": "uuid-string",
    "product_type": "herbal medicine",
    "derived_from_authoritative_text": true,
    "formulation_novelty": "traditional",
    "biological_resources_used": ["Ashwagandha", "Tulsi"]
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "id": "uuid-string",
    "product_id": "uuid-string",
    "category": "Classical Medicine",
    "regulatory_pathway": "Schedule E1 — Classical Ayurvedic Medicine",
    "rules_fired": [
      {
        "rule": "AUTHORITATIVE_TEXT_CHECK",
        "input": "derived_from_authoritative_text=True",
        "result": "Classified as Classical Medicine"
      },
      {
        "rule": "FORMULATION_NOVELTY_OVERRIDE",
        "input": "formulation_novelty=traditional",
        "result": "No override applied"
      },
      {
        "rule": "PRODUCT_TYPE_REFINEMENT",
        "input": "product_type=herbal medicine",
        "result": "No product-type reclassification"
      },
      {
        "rule": "BIOLOGICAL_RESOURCES_FLAG",
        "input": "biological_resources_used=['Ashwagandha', 'Tulsi']",
        "result": "ABS assessment recommended"
      }
    ]
  }
  ```

### (2026-08-29) Phase 4 - T4.2 Completed
- Implemented `POST /api/v1/ip` for per-IP-type relevance assessment, persisting to `IPAssessment`.
- Implemented `POST /api/v1/abs` for ABS obligation assessment, persisting to `ABSAssessment`.
- Both delegate to stubbed AI layer functions in `app/services/assessment_service.py` (pending AI layer T3.4).

#### [CONFIRMED] API Contract: IP Assessment Endpoint
**POST /api/v1/ip**
- **Request Headers:** `Authorization: Bearer <access_token>`
- **Request Body:**
  ```json
  {
    "product_id": "uuid-string",
    "ip_type": "Patent"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "id": "uuid-string",
    "product_id": "uuid-string",
    "ip_type": "Patent",
    "relevance_label": "High",
    "reasoning": "Ayurvedic formulations with novel processes or compositions may qualify for patent protection under the Patents Act, 1970. However, traditional knowledge documented in classical texts is excluded from patentability.",
    "legal_provisions": [
      {
        "provision": "Patents Act 1970, Section 3(p)",
        "description": "Excludes traditional knowledge from patentability",
        "jurisdiction": "India"
      },
      {
        "provision": "TRIPS Agreement, Article 27",
        "description": "Patentable subject matter requirements",
        "jurisdiction": "International"
      }
    ]
  }
  ```

#### [CONFIRMED] API Contract: ABS Assessment Endpoint
**POST /api/v1/abs**
- **Request Headers:** `Authorization: Bearer <access_token>`
- **Request Body:**
  ```json
  {
    "product_id": "uuid-string",
    "biological_resources": [
      {"name": "Ashwagandha", "type": "plant"}
    ],
    "origin": "India",
    "purpose": "commercial"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "id": "uuid-string",
    "product_id": "uuid-string",
    "biological_resources": [
      {"name": "Ashwagandha", "type": "plant"}
    ],
    "origin": "India",
    "purpose": "commercial",
    "relevance_label": "Applicable",
    "next_steps": [
      {
        "step": "NBA Approval",
        "description": "Apply to the National Biodiversity Authority for approval before commercializing products using biological resources.",
        "authority": "National Biodiversity Authority (NBA)"
      },
      {
        "step": "SBB Intimation",
        "description": "Intimate the State Biodiversity Board about use of biological resources for commercial purposes.",
        "authority": "State Biodiversity Board (SBB)"
      },
      {
        "step": "Benefit Sharing Agreement",
        "description": "Negotiate and execute a benefit-sharing agreement as per the Biological Diversity Act, 2002.",
        "authority": "NBA / Local Biodiversity Management Committee"
      }
    ]
  }
  ```

### (2026-08-29) Phase 4 - T4.3 Completed
- T2.1's `GET /api/v1/documents` already covered `jurisdiction`, `document_type`, and `corpus_collection` filters.
- **Added:** `search` query parameter for case-insensitive text search across document titles (using SQL `ILIKE`), which was the only missing piece for the frontend Source Explorer (frontend T4.2).
- Updated contract: `GET /api/v1/documents?search=patents&jurisdiction=India&document_type=STATUTE&corpus_collection=legal_statutory&skip=0&limit=50`

### (2026-08-29) Phase 4 - T4.4 Completed
- Implemented `POST /api/v1/expert` (any authenticated user), `GET /api/v1/expert` and `PATCH /api/v1/expert/{id}` (IP_FACILITATOR/ADMIN only).
- Created `app/services/audit.py` with a reusable `write_audit_log()` utility.
- Wired audit logging into: **chat** (CHAT_QUERY), **classification** (CLASSIFICATION_CREATE), **IP assessment** (IP_ASSESSMENT_CREATE), **ABS assessment** (ABS_ASSESSMENT_CREATE), **expert request** (EXPERT_REQUEST_CREATE, EXPERT_REQUEST_RESOLVE).
- All audit entries are append-only per the AuditLog model from T1.1.

#### [CONFIRMED] API Contract: Expert Escalation Endpoints
**POST /api/v1/expert**
- **Request Headers:** `Authorization: Bearer <access_token>`
- **Request Body:**
  ```json
  {
    "message_id": "uuid-string-or-null",
    "context": "The answer about patent eligibility seems incorrect for novel formulations."
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "id": "uuid-string",
    "user_id": "uuid-string",
    "message_id": "uuid-string",
    "status": "OPEN",
    "context": "The answer about patent eligibility seems incorrect for novel formulations.",
    "created_at": "datetime"
  }
  ```

**GET /api/v1/expert?status=OPEN&skip=0&limit=50**
- **Request Headers:** `Authorization: Bearer <access_token>` (IP_FACILITATOR or ADMIN)
- **Response (200 OK):** Array of ExpertRequestResponse objects.

**PATCH /api/v1/expert/{id}**
- **Request Headers:** `Authorization: Bearer <access_token>` (IP_FACILITATOR or ADMIN)
- **Request Body:**
  ```json
  {
    "status": "RESOLVED"
  }
  ```
- **Response (200 OK):** Updated ExpertRequestResponse object.

#### Audit Log Coverage
| Endpoint | Action | Resource Type |
|---|---|---|
| POST /api/v1/chat | CHAT_QUERY | Conversation |
| POST /api/v1/classification | CLASSIFICATION_CREATE | Classification |
| POST /api/v1/ip | IP_ASSESSMENT_CREATE | IPAssessment |
| POST /api/v1/abs | ABS_ASSESSMENT_CREATE | ABSAssessment |
| POST /api/v1/expert | EXPERT_REQUEST_CREATE | ExpertRequest |
| PATCH /api/v1/expert/{id} | EXPERT_REQUEST_RESOLVE | ExpertRequest |

### (2026-08-29) Phase 5 - T5.1 Completed
- Built a generic `RateLimiter` FastAPI dependency in `app/security/rate_limit.py` using `redis-py` (connected via Upstash `REDIS_URL`).
- Applied `RateLimiter` to all public-facing endpoints with tuned limits:
  - `auth`: `/register` (5 req / 5 min), `/refresh` (10 req / 1 min)
  - `chat`: `/chat` (10 req / 1 min), `/chat/conversations` (60 req / 1 min)
  - `classification`, `ip`, `abs`: POST endpoints (20 req / 1 min)
  - `expert`: POST (10 req / 1 min), GET/PATCH (60 req / 1 min)
  - `feedback`: POST (20 req / 1 min)
  - `context`: `/questions` (60 req / 1 min), `/process` (20 req / 1 min)
  - `documents`: GET endpoints (60 req / 1 min), POST (20 req / 1 min)
- Hardened Pydantic schemas in `chat.py`, `feedback.py`, `expert.py`, and `user.py` by adding `Field(..., max_length=X)` constraints on free-text fields.
- Added ASGI/middleware in `app/main.py` (`limit_request_size`) to drop any request with a body larger than 5MB.

### (2026-08-29) Phase 5 - T5.2 Completed
- Reviewed AuditLog coverage for DPDP compliance.
- Updated `CHAT_QUERY` audit log in `chat_service.py` to remove the raw `question` text. It now logs `domain_intent` and `confidence`.
- Updated `EXPERT_REQUEST_CREATE` audit log in `expert.py` to remove the raw `context` snippet. It now logs `message_id`.
- Created `backend/README.md` to document the Audit Log Retention & Rotation Plan (90-day hot storage, 2-year cold storage deletion).

### (2026-08-29) Phase 5 - T5.3 Completed
- Integrated `sentry_sdk` in `app/main.py`. It initializes automatically if `SENTRY_DSN` is provided in the environment.
- Added `SENTRY_DSN` to `app/config.py` and `.env.example`.
- Verified the `/health` endpoint from Phase 0 already checks Supabase DB, Upstash Redis, and Supabase Storage independently and reports per-dependency status.
