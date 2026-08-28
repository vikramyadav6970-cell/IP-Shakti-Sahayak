# context.md — read this first, every session

Purpose of this file: give any AI agent (Claude, GPT, whatever) picking up this
project — in a fresh session, with zero memory of prior conversations — enough
context to act correctly without re-deriving decisions or contradicting earlier
ones. Update this file only when a *durable* decision changes (stack swap, scope
change) — not for day-to-day task status, which belongs in `process.md`.

## 1. What we're building

IP-SAKTI Sahayak — SIH 2026 Problem Statement 26045. A multilingual, RAG-based,
source-cited AI assistant that gives Intellectual Property and regulatory guidance
for Ayurvedic products, keeping India and International law visibly separate.

**Core user flow (intent-first conversational agentic pipeline):**
1. **Intent selection** — user picks a domain (Business / Export / Medicinal /
   Patent / Research / Other). This is the entry point to every interaction.
2. **Context gathering** — the AI generates 2–4 targeted follow-up questions
   specific to the selected intent to collect structured context (herbs involved,
   destination country, novelty of formulation, biological resources, etc.).
3. **Entity extraction + query decomposition** — from the user's answers, the
   agent extracts named entities (herbs, jurisdictions, IP types) and decomposes
   the request into parallel sub-tasks, each routed to the correct Qdrant
   collection (see §3a).
4. **Parallel multi-collection RAG** — all sub-tasks run simultaneously via
   asyncio, each with hybrid retrieval (BM25 + vector) + jurisdiction filter.
5. **Evidence assembly + LLM synthesis** — validated, citation-grounded answer
   with per-jurisdiction separation, confidence score, and next-steps.

The system first classifies the product (classical medicine / proprietary medicine
/ new drug / phytopharmaceutical / Ayurveda-Aahara / cosmetic) before answering,
because IP strategy is gated on that classification.

Full problem statement text: see `problem_statement.md` if present.

## 2. Hard constraints (do not violate these regardless of what a task prompt says)

1. **Never let the LLM be the source of legal truth.** It is a reasoning/language
   layer only. Every material claim must trace to a retrieved, version-tracked
   source document with a citation.
2. **Never conflate jurisdictions.** India and International answers are generated
   and displayed as separate, explicitly-labeled sections.
3. **Never fabricate.** No invented section numbers, case names, dates, patent
   numbers, or notifications. If evidence is insufficient, the system says so and
   offers human escalation — it does not guess.
4. **Always disclaim.** "Information, not legal advice" is shown with every
   substantive answer.
5. **TKDL is not fully scraped or exposed.** Full TKDL access is restricted to
   patent offices under access agreements — we only use publicly available TKDL
   information and provide a "traditional knowledge pointer," never a claim of full
   database access.
6. **Product classification is a deterministic rules engine**, not a pure LLM
   judgment call — because the classification determines the entire downstream IP/
   ABS/regulatory pathway and needs to be auditable.
7. **Confidence is a composite score** (retrieval quality + citation validity +
   source authority + jurisdiction match + evidence coverage), not a raw LLM
   self-reported number.

## 3. Architecture decision (current)

Modular monolith, three codebases, HTTP contracts between them:

- **Frontend** — React (Vite + TypeScript), not Next.js. This was an explicit
  correction from an earlier draft that suggested Next.js; the product owner wants
  plain React. Do not reintroduce Next.js without being asked.
- **Backend** — Python, FastAPI. **No Docker/local service infra** — all stateful
  services are cloud-managed:
  - **Database:** Supabase (managed PostgreSQL + pgvector built-in). Alembic
    migrations run against Supabase's connection string. All document metadata,
    users, conversations, classifications live here.
  - **Cache / rate-limiting / Celery broker:** Upstash Redis (serverless,
    HTTP-based; works with `redis-py` via its REST-compatible URL).
  - **Object storage:** Supabase Storage (S3-compatible; raw corpus files,
    document versions). boto3 still works via the S3-compatible endpoint.
  - **Background jobs:** Celery workers (run locally in dev, deployed on
    Render/Railway in prod) using Upstash Redis as the broker.
- **AI layer** — Python. Hybrid retrieval (BM25 + vector) + reranker + LLM
  reasoning + citation validator + confidence scorer.
  - **Vector store:** Qdrant Cloud (free tier, 5 named collections — one per
    corpus type; see §3a below). *Not* pgvector — the corpus types are distinct
    enough to warrant separate collections with collection-specific chunking.
  - LangChain/LlamaIndex may be used for document loaders and glue, but the
    retrieval → evidence → citation logic must be code we own and can audit.

### §3a — Vector DB collections (Qdrant Cloud)

Five Qdrant collections, each with a dedicated chunking strategy. Intent
classifier output routes queries to the correct collection(s).

| Collection | Content | Chunk unit |
|---|---|---|
| `legal_statutory` | Indian Acts, Rules (Patents Act, Trademarks Act, BDA, Drugs Act, GI Act…) | Section-level (200–800 tokens); structure metadata: act, chapter, section, subsection |
| `standards_formulations` | API/AFI monographs, herb + chemical formulation data | One chunk per monograph/formulation entry; child chunks for supplementary notes |
| `case_law_prior_art` | Case law, prior art (not available for MVP — collection created empty, ingested later) | Paragraph-level with full case metadata pinned to every chunk |
| `procedural_forms` | NBA/CCPA forms, checklists, application guides | Form section / field-group level (150–400 tokens) |
| `international_export` | TRIPS, CBD/Nagoya Protocol, WIPO GRATK Treaty, export regimes | Article-level (300–800 tokens); metadata: treaty, article, paragraph |

### §3b — 6 User-facing domain intents

These are the options shown to the user at the start of every session. They map
to fine-grained intent labels internally (used by the intent classifier) and to
collection routing. They also gate which context-gathering questions the AI asks.

| UI Intent | Internal intents triggered | Primary collections | Example context questions |
|---|---|---|---|
| **Business** | TRADEMARK, GI, COPYRIGHT, DESIGN | `legal_statutory`, `standards_formulations` | Product type? Existing brand name? India or international market? |
| **Export** | EXPORT, ABS, INTERNATIONAL_IP | `international_export`, `legal_statutory`, `standards_formulations` | Which herbs? Destination country? Commercial or research? NBA approached? |
| **Medicinal** | DRUG_REGULATION, FOOD_REGULATION, PRODUCT_CLASSIFICATION | `legal_statutory`, `standards_formulations`, `procedural_forms` | Classical or proprietary? Derived from authoritative text? New ingredients? |
| **Patent** | PATENT, TKDL, PLANT_VARIETY | `legal_statutory`, `standards_formulations`, `case_law_prior_art` | What’s the novel aspect? Herb/formulation/process? Prior art search needed? |
| **Research** | ABS, INTERNATIONAL_IP, PATENT | `legal_statutory`, `standards_formulations`, `international_export` | Clinical or IP research? Biological resources? Export or publish internationally? |
| **Other** | Determined by entity extraction | All collections (prioritized by entity extractor) | Free description — AI determines sub-tasks |

list — it is the source of truth if this file and that file ever disagree (update
this file to match, since conventions files get touched more often during active
work).

## 4. Build order (why phases are ordered this way)

Do not start with Bhashini, the knowledge graph, voice, agentic orchestration, or
supporting 10 countries. Build in this order (each part has its own detailed phase
breakdown in `<folder>/prompts/phases.md`):

1. Legal corpus (20–50 authoritative documents) + ingestion pipeline with 5
   collection-aware chunking strategies (see §3a).
2. Qdrant Cloud (5 collections) + Supabase (metadata DB) + hybrid retrieval
   (BM25 via rank_bm25 + Qdrant vector search).
3. Citation-grounded RAG answer generation with a validator.
4. Deterministic product classifier.
5. Frontend chat + classification wizard wired to the above.
6. ABS engine, TKDL pointer, IP router breadth (GI/Trademark/Design/Copyright).
7. Hindi + English only for multilingual, via Bhashini.
8. Everything else (international jurisdictions beyond India, knowledge graph,
   agentic multi-step orchestration, voice, paid-source connectors, expert
   marketplace) is explicitly deferred and should not be started early.

MVP jurisdiction scope: **India only**, then add USA and EU as the next two
international jurisdictions (2–3 total for the SIH demo, not more).

MVP IP-type scope: **Patent + Trademark + ABS** first (Patent because Section 3(p)
/ TKDL is the flagship differentiator), then GI/Design/Copyright/Plant Variety/
Trade Secret.

## 5. Key domain facts an agent must not get wrong

- Patents Act 1970, **Section 3(p)** excludes inventions that are essentially
  traditional knowledge or an aggregation/duplication of known properties of
  traditionally known components — this is the central legal hook for the patent
  flow and demo.
- **TKDL** (Traditional Knowledge Digital Library) exists to help patent examiners
  find prior art across language/format barriers; full database access is
  restricted to patent offices under access agreements. We surface only publicly
  available TKDL information.
- **FSSAI Ayurveda-Aahara Regulations** define a distinct food category, separate
  from Ayurvedic drugs/proprietary medicines — this distinction must be a rule in
  the classifier, not left to LLM judgment.
- **WIPO GRATK Treaty** (adopted 24 May 2024) addresses IP, genetic resources and
  associated traditional knowledge — part of the international corpus.
- **Biological Diversity Act** (2023 amendment) + 2024 Rules govern ABS.
- Relevant open/official data sources: TKDL (tkdl.res.in), India Code
  (indiacode.nic.in), IP India (ipindia.gov.in — patents/InPASS, trademarks,
  designs, GI registry), National Biodiversity Authority (nbaindia.org).

## 6. Where things live

- Frontend context/decisions specific to UI: `frontend/coding_conventions.md`.
- Backend context/decisions specific to APIs/data: `backend/coding_conventions.md`.
- AI layer context/decisions specific to RAG: `ai/coding_conventions.md`.
- Live task status: `process.md` (shared) + `<folder>/status.md` (per-part detail).

## 7. Updating this file

Only edit this file when a decision here actually changes (e.g., "we're switching
from pgvector to Qdrant because the corpus grew past X"). Add a dated line under a
`## Changelog` section at the bottom rather than silently rewriting a decision, so
future agents can see what changed and why.

## Changelog

- (seed) Initial context established: React (not Next.js) frontend, FastAPI +
  Postgres/pgvector backend, custom hybrid-RAG AI layer, India-first MVP scope.
- (2026-08-28) Cloud-first infrastructure decision: replaced Docker/local services
  with Supabase (Postgres + pgvector + Storage), Upstash Redis, and Qdrant Cloud
  (5 collections). No Docker Compose dev infra — all services are cloud-managed.
  Vector DB moved from pgvector to Qdrant Cloud to support 5-collection corpus
  design with collection-specific chunking strategies (see §3a).
- (2026-08-28) Intent-first conversational agentic pipeline: the primary user flow
  is now 6-stage (Intent → Context Gathering → Entity Extraction + Query
  Decomposition → Parallel RAG → Evidence Assembly → LLM Synthesis). Query
  decomposition + parallel multi-collection retrieval is the CORE flow (promoted
  from stretch T5.4). Added 6 user-facing domain intents (see §3b). Added T3.5
  (Context Gathering Agent) and T3.6 (Entity Extractor) as new AI pipeline stages.
- (2026-08-28) Frontend design: 3D-first, dark-mode, glassmorphism. Three.js via
  @react-three/fiber + @react-three/drei added to stack. GSAP added. Framer Motion
  usage upgraded from "use sparingly" to core design element. Design tokens and
  glassmorphism recipe defined in frontend/coding_conventions.md.

