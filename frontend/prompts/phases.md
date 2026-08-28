# frontend/prompts/phases.md

Each task below is a **ready-to-paste prompt** for an AI coding agent. Give the
agent repo access, paste the task's prompt block verbatim. Do tasks in order
within a phase; phases may overlap slightly with backend/AI phases of the same
number.

Manual/human steps are called out explicitly.

**Design mandate (read before every task):**
This product must be visually stunning. The design is dark-first, 3D, animated,
and premium. See `frontend/coding_conventions.md` for the exact design tokens,
glassmorphism recipe, and library stack. Every screen must use:
- 3D animated background (Three.js via @react-three/fiber)
- Glassmorphism panels for content areas
- Framer Motion for all UI transitions
- Space Grotesk (headings) + Inter (body) fonts
- The fixed colour palette from coding_conventions.md

**Pipeline reminder (read before every task):**
The user flow is: Intent Selection → Context Gathering → Answer. The frontend
drives the first two stages and displays the third. See `context.md §1` and `§3b`.
The `useIntentStore` (Zustand) holds the full session state.

---

## Phase 0 — Project setup

### T0.1 — Scaffold the project

**Manual prerequisite:** Node.js 20+ installed.

**Prompt:**
```
Read /context.md, /process.md, and /frontend/coding_conventions.md in full before
doing anything.

Task: Scaffold a new Vite + React + TypeScript project inside the existing
`frontend/` folder (do not create a nested duplicate folder). Requirements:

- Vite + React 18 + TypeScript, strict mode enabled in tsconfig.
- ESLint + Prettier configured for React/TS with no rule disables without a comment.
- Folder structure exactly as documented in frontend/coding_conventions.md,
  including the `src/components/three/` directory.
- Install ALL libraries from the Stack section of frontend/coding_conventions.md:
  - @react-three/fiber, @react-three/drei, three, @types/three
  - gsap, @gsap/react
  - framer-motion
  - zustand
  - @tanstack/react-query
  - react-hook-form, zod, @hookform/resolvers
  - react-router-dom
  - recharts
  - lucide-react
  - react-i18next, i18next
  - @fontsource/space-grotesk, @fontsource/inter
  - tailwindcss, @tailwindcss/typography, shadcn/ui (via CLI init)
  - axios (justify in status.md: preferred over fetch for interceptor support)

- package.json scripts: dev, build, preview, lint, test.

- `src/styles/globals.css` with the design token CSS variables from
  coding_conventions.md (--color-void, --color-surface, --color-surface-up,
  --color-border, --color-teal, --color-gold, --color-violet, --color-text,
  --color-muted) and the font-face declarations for Space Grotesk + Inter.

- A `.env.example` with:
  VITE_API_BASE_URL=http://localhost:8000  # backend dev server URL — all cloud keys live in backend

- A basic `App.tsx` that renders a full-screen dark canvas with "IP-SAKTI Sahayak"
  centered in Space Grotesk to confirm the dev server and fonts work.

When done: update /frontend/status.md with every package installed and its version,
and flip T0.1 to [x] in /process.md.
```

### T0.2 — shadcn/ui theme + design system

**Prompt:**
```
Read /context.md and /frontend/coding_conventions.md first.

Task: Configure shadcn/ui with a custom theme matching the coding_conventions.md
design tokens. Do not use the default zinc/slate look.

- Run shadcn/ui init and configure it to use the CSS variable approach.
- Map the design tokens to shadcn's expected CSS variables (--background,
  --foreground, --primary, --secondary, --muted, --accent, --border, --ring, etc.)
  using the palette from coding_conventions.md: void as background, teal as primary
  accent, gold as secondary.
- Install these shadcn components: button, input, form, card, dialog, tabs, badge,
  separator, dropdown-menu, sonner (toast), skeleton, progress, textarea, select,
  radio-group, checkbox.
- Create `src/lib/cn.ts` (the className merger utility from shadcn).
- Verify one Button and one Card render with correct dark glassmorphism styling
  on App.tsx.

When done: update /frontend/status.md and flip T0.2 to [x] in /process.md.
```

### T0.3 — 3D background canvas + core layout

**Prompt:**
```
Read /context.md and /frontend/coding_conventions.md (especially rule 9 — 3D
performance, and rule 7 — accessibility/reduce-motion) first.

Task: Build the persistent 3D background that lives behind every page.

1. Create `src/components/three/BackgroundCanvas.tsx`:
   - A full-screen `<Canvas>` with frameloop="demand" (render-on-demand).
   - A particle field (3000–4000 particles max) using instanced mesh for
     performance. Particles should slowly drift with a gentle sine wave motion.
     Color: mix of --color-teal and --color-violet at low opacity (0.3–0.5).
   - A soft nebula/fog effect using a large transparent plane with a radial
     gradient texture.
   - Wrap the Canvas in React.lazy + Suspense so it doesn't block the initial
     paint. The Suspense fallback is a plain `background: var(--color-void)` div.
   - useReducedMotion() check: if the user prefers reduced motion, render a static
     star field instead of animated particles.

2. Create `src/components/three/SceneWrapper.tsx`: a div that positions the Canvas
   fixed behind all content (z-index: 0) with `pointer-events: none` so it doesn't
   block UI interaction.

3. Wire SceneWrapper into App.tsx so it underlies all routes.

When done: update /frontend/status.md and flip T0.3 to [x] in /process.md.
```

### T0.4 — State stores, API client, routing skeleton

**Prompt:**
```
Read /context.md §1 and §3b, /process.md, and /frontend/coding_conventions.md first.

Task:
1. Create four Zustand stores in `src/store/`:
   - `useAuthStore`: user, token, login/logout actions.
   - `useJurisdictionStore`: selected jurisdiction (INDIA default), secondary
     country for International, persisted to localStorage.
   - `useIntentStore` (NEW — core of the pipeline): {
       domain_intent: DomainIntent | null,
       context_questions: ContextQuestion[],
       context_answers: Record<string, string | string[]>,
       context_object: ContextObject | null,   // typed result from T3.5
       entity_set: EntitySet | null,           // typed result from T3.6
       session_id: string | null,
       reset: () => void
     }
     DomainIntent = "BUSINESS" | "EXPORT" | "MEDICINAL" | "PATENT" | "RESEARCH" | "OTHER"
     Add a Comment: // TODO(contract): confirm ContextQuestion, ContextObject,
     EntitySet schemas against ai/status.md once T3.5 is done.

2. `src/services/apiClient.ts`: axios instance reading VITE_API_BASE_URL, attaching
   auth headers, structured error throwing on non-2xx.

3. React Router with route skeleton for: `/` (intent selector), `/context` (context
   gathering), `/chat` (answer screen), `/classify`, `/abs`, `/sources`, `/admin`,
   `/login`. Placeholder pages for each.

4. TanStack Query QueryClientProvider at app root.

When done: update /frontend/status.md and flip T0.4 to [x] in /process.md.
```

---

## Phase 1 — Intent selection & core shell

### T1.1 — 3D Intent selector (landing page)

**Prompt:**
```
Read /context.md §1 and §3b (the 6 domain intents and their descriptions), and
/frontend/coding_conventions.md (design system, Three.js rules) first.

Task: Build the landing page at `/` — the entry point to every user session. This
is the most important screen; it must be visually spectacular AND functional.

Layout: full-screen, no scrolling. The 3D background canvas from T0.3 is visible.
Content: six intent cards arranged in a curved 3D arc or a 2x3 grid floating over
the canvas.

Each IntentCard component:
- Glassmorphism panel (use the recipe from coding_conventions.md).
- An icon: use a custom SVG or a relevant Lucide icon. Make each card feel distinct.
- Title (Space Grotesk, bold, --color-text): Business / Export / Medicinal / Patent
  / Research / Other.
- One-line description (Inter, --color-muted): e.g. Export → "Navigate NBA approvals,
  CITES, and destination-country regulations for herbal exports."
- Hover state: teal glow border (box-shadow: 0 0 0 1px var(--color-teal), 0 0 20px
  rgba(45,212,191,0.2)), scale 1.03 (Framer Motion spring).
- Click: selection pulse animation (GSAP), then Framer Motion page exit to /context.
  Store the selected domain_intent in useIntentStore.

Header: Product name "IP-SAKTI Sahayak" in Space Grotesk, top-left, subtle.
Jurisdiction toggle (from T1.3) in the top-right corner.

"Other" card opens an inline textarea instead of navigating — the user types a
description, which becomes the context_object.free_description, then navigates to
/chat directly (skipping /context for "Other" intent).

Disclaimer banner (non-dismissible, slim): "Information, not legal advice." at the
bottom of every screen — this is a hard requirement from context.md §2 rule 4.

Reduce-motion: if the user prefers reduced motion, render the cards in a static
grid without entrance animations.

When done: update /frontend/status.md and flip T1.1 to [x] in /process.md.
```

### T1.2 — App shell, navigation, disclaimer

**Prompt:**
```
Read /context.md §2 hard constraints and /frontend/coding_conventions.md first.

Task: Build the persistent app shell (for routes /chat, /classify, /abs, /sources,
/admin — NOT the landing page which is full-screen 3D):

- Header (glassmorphism, sticky): product name/logo left, nav links right (Chat /
  Classify / ABS / Sources / Admin — admin only if role check permits), and a
  "New Session" button that calls useIntentStore.reset() and navigates to `/`.
- Jurisdiction toggle (builds in T1.3) — place in header.
- Non-dismissible disclaimer banner: "This tool provides information, not legal
  advice." Slim (40px), --color-teal/10 background, --color-teal text, always
  visible. Hard requirement from context.md §2 rule 4.
- Footer: minimal, --color-muted links.
- Responsive down to 375px.

When done: update /frontend/status.md and flip T1.2 to [x] in /process.md.
```

### T1.3 — Jurisdiction toggle

**Prompt:**
```
Read /context.md §2 rule 2 and /frontend/coding_conventions.md first.

Task: Build the Jurisdiction toggle wired to useJurisdictionStore.
- Two-state: India (default) / International. Persisted to localStorage.
- International: secondary select for country (USA, EU, UK, Japan, Australia,
  Canada, UAE, WHO/International, WIPO). For MVP, only USA and EU route anywhere
  real — note others in status.md.
- Expose via useJurisdiction() hook.
- Design: pill toggle, India = --color-teal active, International = --color-gold
  active. Small, prominent in header.

When done: update /frontend/status.md and flip T1.3 to [x] in /process.md.
```

---

## Phase 2 — Context gathering & answer flow

**Before starting this phase**, check `ai/status.md` for the finalized
ContextQuestion, ContextObject schemas from T3.5 — the context gathering UI must
match these exactly. If not yet available, use the schemas documented in
`ai/prompts/phases.md T3.5` and flag with TODO(contract).

### T2.1 — Context gathering UI (/context)

**Prompt:**
```
Read /context.md §1 (pipeline stage 2), ai/prompts/phases.md T3.5 (ContextObject
schemas per intent), and /frontend/coding_conventions.md first.

Task: Build the context-gathering screen at `/context`.

This screen receives the selected domain_intent from useIntentStore and presents
2–4 AI-generated follow-up questions before retrieval begins.

Design: conversational card-stack layout. Questions appear as floating glassmorphism
cards, staggered in from the bottom with Framer Motion (0.12s delay between each).
Each card contains: the question text (Inter, --color-text) and an answer input
(text field, select, checkbox list, or radio group — based on the ContextQuestion
answer_type).

Implementation:
1. On mount, call `GET /api/v1/context/questions?intent={domain_intent}` to fetch
   the questions from the backend (which calls ai/ T3.5). If not ready, use a mock
   from the schema in ai/prompts/phases.md T3.5.
2. Render questions one-by-one as the user answers (progressive reveal — question N+1
   appears after question N is answered, not all at once). Use Framer Motion AnimatePresence.
3. A progress bar (shadcn Progress component, --color-teal fill) shows how many
   questions remain.
4. "Continue" button appears when all required questions are answered. On click:
   - Store answers in useIntentStore.context_answers
   - POST answers to `/api/v1/context/process` (backend calls T3.6 entity extractor)
   - Store returned ContextObject + EntitySet in useIntentStore
   - Navigate to /chat

Service: `src/services/contextService.ts` — all API calls here, not inline.

Error states: if the question fetch fails, show a friendly error with a "Try again"
button. If the backend isn't ready, use the mock data.

When done: update /frontend/status.md with the mock ContextQuestion schema used
and flip T2.1 to [x] in /process.md. Add a Cross-part note for backend and AI.
```

### T2.2 — Chat / answer screen (/chat)

**Prompt:**
```
Read /context.md (especially §2 hard constraints), /process.md (check chat API
contract in backend/status.md), and /frontend/coding_conventions.md first.

Expected contract (confirm against backend/status.md before final wiring):
Request: { question: str, domain_intent: str, context_object: obj,
           jurisdiction: str, language: str, conversation_id: str | null }
Response: { answer: str (markdown), confidence: float, confidence_label: str,
            classification: str | null, citations: [...], requires_human_review: bool,
            sub_tasks_run: list[str], sources_by_collection: dict }

Task: Build the answer screen at `/chat`.

Layout (two-panel on desktop, single-column on mobile):

LEFT PANEL — Evidence Map (25% width):
- A visual indicator of which Qdrant collections were used for this answer.
  Use a set of small labeled nodes (one per collection) — active collections
  (present in sources_by_collection) glow with --color-teal, inactive are muted.
  Animate active nodes with a soft pulse (Framer Motion) when the answer arrives.
  Label each: "Statutes", "Formulations", "Case Law", "Forms", "International".
- Below the nodes, list the sub_tasks_run as small badges (shadcn Badge,
  --color-surface-up background).
- This panel collapses to a drawer trigger on mobile.

RIGHT PANEL — Conversation (75% width):
- Message list (user + assistant turns). User intent + context summary shown as
  the first "user" turn (reconstructed from useIntentStore, not a raw free-text
  message).
- Assistant answer rendered as markdown (use react-markdown with
  @tailwindcss/typography prose styles, dark mode).
- Input box with send button (for follow-up questions after the first answer —
  subsequent turns skip the context-gathering phase and go straight to retrieval).
- Loading: while the answer is streaming/loading, show a pulsing skeleton in the
  assistant panel and animate the evidence-map nodes with a "searching" shimmer.
- Use TanStack Query mutation for the send call via src/services/chatService.ts.

If navigating from /context, auto-submit on mount (the intent + context_object is
already in useIntentStore — submit the query immediately without the user having
to type anything).

When done: update /frontend/status.md and flip T2.2 to [x] in /process.md.
```

### T2.3 — Citation cards + confidence badge

**Prompt:**
```
Read /context.md §2 rules 1, 3, 7 and /frontend/coding_conventions.md first.

Task: Build two reusable components:

1. `<CitationCard>`: renders one citation with document title, section reference,
   collection badge (which of the 5 Qdrant collections it's from, color-coded:
   legal_statutory=teal, standards_formulations=gold, procedural_forms=violet,
   international_export=blue, case_law_prior_art=amber), jurisdiction badge,
   source authority, and an "Open source" link. If answer has zero citations, show
   an explicit "No authoritative source found" state (NOT a blank or omission).

2. `<ConfidenceBadge>`: color-coded chip + text label HIGH/MEDIUM/LOW. When LOW,
   render a "Human IP facilitator review recommended" CTA with a gold accent
   (escalation entry point wired fully in Phase 4). Never rely on color alone —
   the text label is always visible (accessibility rule).

Wire both into the chat screen from T2.2.

When done: update /frontend/status.md and flip T2.3 to [x] in /process.md.
```

### T2.4 — Finalize chat API wiring

**Prompt:**
```
Read /process.md Cross-part notes and /backend/status.md for the current, real
`/api/v1/chat` contract — stop and report blocked if not finalized.

Task: Replace the mock chatService.ts with real backend calls. Handle all error
shapes distinctly (validation errors, 5xx, auth, timeout). Add integration tests
(Vitest + RTL + MSW) covering: successful answer render with evidence map,
low-confidence escalation prompt, and error state.

When done: update /frontend/status.md and flip T2.4 to [x] in /process.md.
```

---

## Phase 3 — Product classification wizard

### T3.1 — Wizard shell

**Prompt:**
```
Read /context.md §2 rule 6 and /frontend/coding_conventions.md first.

Task: Build a multi-step wizard at `/classify` using React Hook Form + Zod.

Design: each wizard step is a full-panel card (glassmorphism) with a smooth
slide/fade transition between steps (Framer Motion AnimatePresence with
slide-left/right). Progress indicator: a horizontal step bar with teal active state.
The 3D background is visible throughout.

Steps:
1. "What is your product?" — Ayurvedic medicine / Food / Nutraceutical / Cosmetic /
   Plant-based extract / Research formulation / Not sure.
2. "Is the formulation derived from an authoritative Ayurvedic text?" — Yes / No /
   Not sure.
3. "Is it a new formulation?" — Existing classical / Modified / Completely new /
   Not sure.
4. "Does it use biological resources?" — multi-select checklist + yes/no for
   microorganism/animal-derived.

Final step submits to `/api/v1/classification` and navigates to result view (T3.2).

When done: update /frontend/status.md and flip T3.1 to [x] in /process.md.
```

### T3.2 — Classification result view

**Prompt:**
```
Read /context.md and /frontend/coding_conventions.md first.

Task: Build the classification result screen shown after wizard submission.

- Product classification label and regulatory pathway — in a prominent glassmorphism
  hero card with an animated badge (Framer Motion spring entrance).
- "IP protection map": an interactive 3D radar chart (use @react-three/drei's
  `<Html>` to overlay a Recharts RadarChart on a 3D scene, OR use a flat Recharts
  RadarChart styled with the design tokens — choose whichever looks better and
  document the choice). Label axes as PATENT / TRADEMARK / GI / DESIGN / COPYRIGHT
  / TRADE_SECRET / PLANT_VARIETY. Label scores as "relevance" or "potential
  applicability" — NEVER as probability of legal success.
- Each axis label is clickable: routes to /chat pre-seeded with a relevant question.
- Disclaimer visible.

When done: update /frontend/status.md and flip T3.2 to [x] in /process.md.
```

---

## Phase 4 — ABS wizard, Source Explorer, Escalation, Dashboard

### T4.1 — ABS compliance wizard

**Prompt:**
```
Read /context.md §5 and /frontend/coding_conventions.md first.

Task: Build `/abs`. Same wizard pattern as T3.1 (glassmorphism cards, step
progress, slide transitions). Steps: biological resources? → which ones (reuse
ingredient checklist from T3.1 step 4 as a shared component) → origin → purpose
→ research/access already involved? Result panel: ABS relevance label (HIGH/MEDIUM/
LOW/NOT_APPLICABLE — text always, not just color), numbered next-steps list.

When done: update /frontend/status.md and flip T4.1 to [x] in /process.md.
```

### T4.2 — Source Explorer

**Prompt:**
```
Read /context.md §2 rule 3 and /frontend/coding_conventions.md first.

Task: Build `/sources`. A searchable, filterable grid of corpus documents.

Design: card grid with glassmorphism cards. Each source card: title, collection
badge (color-coded per the 5 collections — same color scheme as CitationCard),
jurisdiction badge, document type, issuing authority, version/amendment date, and
"View source" link. Collection badge makes it immediately clear which of the 5
Qdrant collections this document belongs to.

Filters (top bar): jurisdiction select + document type select + collection select.
Search: text search across document titles. All filters via URL params (shareable).

When done: update /frontend/status.md and flip T4.2 to [x] in /process.md.
```

### T4.3 — Human expert escalation

**Prompt:**
```
Read /context.md and /frontend/coding_conventions.md first.

Task: Replace the placeholder escalation from T2.3 with a real flow: a dialog (
shadcn Dialog) showing why escalation is suggested (low confidence reason from the
response), a textarea for additional context, and a submit button that POSTs to
`/api/v1/expert`. Confirmation state: "Your query has been flagged — reference
#..." with a copy button for the reference ID.

Animate the dialog entrance with Framer Motion.

When done: update /frontend/status.md and flip T4.3 to [x] in /process.md.
```

### T4.4 — Admin / IP dashboard

**Prompt:**
```
Read /frontend/coding_conventions.md first.

Task: Build `/admin` (role-gated — show clear "not authorized" if role doesn't
permit, not a silent 404). Dashboard panels (glassmorphism cards):
- Corpus health: document count by collection (5 bars, collection-color-coded),
  indexed vs. pending, last-updated date.
- AI metrics: retrieval accuracy, citation accuracy, abstention rate, sub-task
  decomposition accuracy. Use Recharts for trend lines.
- System status: Supabase DB, Upstash Redis, Qdrant Cloud health (calls the
  backend /health endpoint).

Handle missing data (AI metrics not available until Phase 5 evaluation runs) with
normal empty states — not crashes.

When done: update /frontend/status.md and flip T4.4 to [x] in /process.md.
```

---

## Phase 5 — Auth, i18n, polish, deploy

### T5.1 — Auth UI

**Manual prerequisite:** Backend Phase 1 JWT implementation must be live.

**Prompt:**
```
Read /backend/status.md for auth endpoint shapes, then /frontend/coding_conventions.md.

Task: Build `/login` (and register if backend supports it) using React Hook Form +
Zod. Wire to real auth endpoints. Store token via useAuthStore (httpOnly cookie
preferred if backend supports; document choice). Route-guard all protected routes.

Design: centered glassmorphism card over the 3D background. Animated form entrance
(Framer Motion). Teal submit button.

When done: update /frontend/status.md and flip T5.1 to [x] in /process.md.
```

### T5.2 — Hindi/English i18n

**Manual prerequisite:** Bhashini API key if needed for content translation.

**Prompt:**
```
Read /frontend/coding_conventions.md first.

Task: Wire react-i18next with English and Hindi locale files for all static UI
strings (nav, buttons, form labels, disclaimer, wizard questions, intent card
descriptions). Add a language switcher in the app shell. Keep locale files
organized by feature (common.json, chat.json, classify.json, abs.json, intent.json).
UI chrome only — AI-generated answer translation is handled by the AI layer.

When done: update /frontend/status.md and flip T5.2 to [x] in /process.md.
```

### T5.3 — Accessibility + responsive + performance pass

**Prompt:**
```
Read /frontend/coding_conventions.md rules 7 and 9 first.

Task: Full audit:
- Keyboard navigation across all routes including intent selector and context
  gathering.
- aria-labels on icon-only controls.
- aria-live region on assistant message arrival in chat.
- Color contrast on all badges/chips.
- Reduce-motion: confirm all GSAP, Framer Motion, and Three.js animations respect
  useReducedMotion() — static fallbacks must exist.
- 3D performance: confirm Canvas frameloop="demand", particle count ≤5000, no
  Three.js memory leaks (dispose geometries/materials on unmount).
- Responsive down to 375px on all screens.
- Fix what you find; list unresolved items in status.md with reasons.

When done: update /frontend/status.md and flip T5.3 to [x] in /process.md.
```

### T5.4 — Deploy

**Manual prerequisite:** Vercel account (or equivalent) connected to the repo, and
the real backend URL to set as `VITE_API_BASE_URL`.

**Prompt:**
```
Task: Prepare for deployment: verify `npm run build` produces a clean production
bundle with zero TypeScript errors. Add a `vercel.json` with correct SPA rewrite
rules for React Router. Document required production env vars in README.md
(VITE_API_BASE_URL pointing at the deployed backend — all cloud service keys live
in the backend, not the frontend). Final smoke test against the deployed backend URL.

When done: update /frontend/status.md, flip T5.4 to [x] in /process.md, and update
README.md §5 with the real deployed URL.
```
