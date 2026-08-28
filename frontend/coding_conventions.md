# frontend/coding_conventions.md

Read `/context.md` and `/process.md` before this file. This file governs how code
is written inside `frontend/` specifically. If any instruction here conflicts with
a task prompt, **these conventions win** — a task prompt describes *what*, this
file governs *how*.

## Stack (authoritative — do not substitute without updating this file)

- **React 18** + **Vite** + **TypeScript** (strict mode). Not Next.js — this was an
  explicit product decision, do not reintroduce it.
- **Tailwind CSS** + **shadcn/ui** for form components, dialogs, badges, and any
  standard UI primitives. shadcn/ui is the baseline — 3D/animated elements layer
  *on top of* it, not instead of it.
- **Three.js via `@react-three/fiber` + `@react-three/drei`** for 3D backgrounds,
  particle systems, and interactive 3D elements (intent selector sphere, evidence
  graph visualization). Never import Three.js directly in a React component — always
  go through `@react-three/fiber`. Use `@react-three/drei` helpers (OrbitControls,
  Float, Stars, etc.) before writing raw Three.js from scratch.
- **GSAP** (`gsap` + `@gsap/react`) for entrance animations, scroll-based effects,
  staggered card reveals, and timeline-based sequences. Use for anything requiring
  precise timing or sequencing that Framer Motion doesn't express cleanly.
- **Framer Motion** for component-level transitions (panel slides, card reveals,
  layout animations, exit animations). For this project, use Framer Motion freely
  — this is a premium, visually-driven product and motion is a core design element,
  not decoration. The "use sparingly" guidance from earlier drafts is superseded.
- **Zustand** for client/UI state (intent selection, context answers, session).
  **TanStack Query** for all server state — never hand-roll a `useEffect` + `fetch`
  + `useState` data-fetching pattern.
- **React Hook Form** + **Zod** for all forms and their validation schemas.
- **React Router** for routing.
- **Recharts** for charts and evaluation dashboards.
- **Lucide** for icons (supplement with custom SVG for 3D-adjacent decorative icons
  where Lucide doesn't have what's needed — document any custom icons).
- **react-i18next** for i18n (English/Hindi from Phase 5).
- **Google Fonts**: Space Grotesk (headings, large display text) + Inter (body,
  labels, smaller text). Load via `@fontsource/space-grotesk` and
  `@fontsource/inter` — don't use a `<link>` tag for fonts in a Vite project.
- Testing: **Vitest** + **React Testing Library** for components with real logic
  (forms, wizards, citation rendering). Pure presentational and 3D components
  don't require unit tests — but do require a visual smoke-test note in status.md.

## Design system

This is a **dark-first** design. The colour palette is fixed across the project:

```
--color-void:        #030712   /* page background — near-black */
--color-surface:     #0f172a   /* card/panel base */
--color-surface-up:  #1e293b   /* elevated surfaces, glass panels */
--color-border:      rgba(255,255,255,0.08)
--color-teal:        #2dd4bf   /* primary accent — retrieval/legal */
--color-gold:        #f59e0b   /* secondary accent — citations/authority */
--color-violet:      #8b5cf6   /* tertiary — classification/AI */
--color-text:        #f1f5f9   /* primary text */
--color-muted:       #94a3b8   /* secondary text, placeholders */
```

Glassmorphism recipe (use consistently for all floating panels):
```css
background: rgba(15, 23, 42, 0.6);
backdrop-filter: blur(24px);
border: 1px solid rgba(255,255,255,0.08);
box-shadow: 0 8px 32px rgba(0,0,0,0.4);
```

## Hard rules

1. **Never build a custom version of something a chosen library already does.** No
   hand-rolled modal/dropdown/toast/date-picker — use shadcn/ui. No hand-rolled
   fetch/cache/retry logic — use TanStack Query. No hand-rolled form validation —
   use Zod schemas. If shadcn/ui doesn't have a primitive you need, compose it from
   Radix (shadcn/ui's base) rather than writing raw DOM/ARIA handling yourself.
2. **No `any`.** Type every API response against a shared `types/` definition that
   matches the backend's Pydantic schema. If the backend contract isn't final yet,
   define the type from the documented contract in `backend/status.md` /
   `process.md` and flag it with a `// TODO(contract): confirm against backend`
   comment — this is the one allowed TODO category, and it must name what it's
   waiting on.
3. **No other TODOs, stubs, or "// implement later" placeholders** left in code
   that is presented as done. If a task is genuinely partial, mark it `[~]` in
   `process.md`/`status.md` with what's left — don't hide it in a code comment.
4. **No console.log left in committed code.** Use a small logger utility if you
   need dev-time diagnostics, gated behind `import.meta.env.DEV`.
5. **Production-grade only:** every screen that fetches data needs a loading
   state, an empty state, and an error state — not just the happy path. Every form
   needs client-side validation feedback. Every async action that can fail (chat
   query, classification submit) needs visible failure handling, not a silent swallow.
6. **Component structure:** one component per file, colocated with its own
   `ComponentName.test.tsx` if it has logic worth testing. Shared types in
   `src/types/`, API calls only inside `src/services/`, never inline `fetch`/
   `axios` calls inside components. 3D scene components live in
   `src/components/three/`.
7. **Accessibility is not optional — even in 3D UIs.** Every interactive element
   must be keyboard-reachable. Icon-only buttons must have `aria-label`. Color is
   never the only signal (e.g. confidence badges need text, not just a color chip).
   3D-only content must have a non-3D fallback for screen readers. Reduce-motion
   media query must be respected: wrap all GSAP/Framer/Three.js animations in
   `useReducedMotion()` checks and provide static fallbacks.
8. **Jurisdiction and disclaimer rules are UI law, not style choices:** any screen
   rendering a substantive answer must (a) visually separate India vs.
   International content if both are present, and (b) show the "information, not
   legal advice" disclaimer. Check `context.md §2` before shipping any
   answer-rendering surface.
9. **3D performance rules:** always lazy-load Three.js scenes via React.lazy +
   Suspense. Use `<Canvas>` with `frameloop="demand"` (render-on-demand, not
   continuous) for static or near-static scenes to avoid burning GPU on idle
   screens. Limit particle counts to ≤5000 on landing. Test on a mid-range device.
10. **Intent state is a first-class store.** The `useIntentStore` (Zustand) holds:
    selected_intent, context_answers[], entity_extraction_result, decomposed_tasks[].
    This store is the single source of truth for the full pipeline state and is
    cleared on session reset. Never pass intent through component props — read from
    the store.

## Folder structure

```
frontend/
├── coding_conventions.md
├── status.md
├── prompts/
│   └── phases.md
└── src/
    ├── app/            # routes/pages
    ├── components/
    │   ├── three/      # R3F canvas + scene components (particles, intent sphere, etc.)
    │   ├── chat/       # context-gathering + answer UI
    │   ├── citations/
    │   ├── classification/
    │   └── ui/         # shadcn/ui wrappers + custom primitives
    ├── hooks/
    ├── services/       # API clients — the ONLY place fetch/axios is used
    ├── store/          # Zustand stores (useAuthStore, useIntentStore, useJurisdictionStore)
    ├── types/          # shared TS types, mirrors backend schemas
    ├── lib/            # utilities (i18n setup, formatters, gsap helpers, etc.)
    └── styles/
```

## API contract discipline

The frontend must never guess a backend response shape. Before wiring a real
endpoint:
1. Check `backend/status.md` / `process.md` for the finalized contract.
2. If not finalized, build against a documented mock in
   `src/services/__mocks__/` and note the mock's shape in your own `status.md` so
   backend can match it (or tell you it's changing).

## Definition of done for any frontend task

- Builds with `npm run build` with zero TypeScript errors.
- Zero ESLint errors (config lives at project root once Phase 0 is done).
- Loading/empty/error states present for anything async.
- No console.log, no `any`, no unauthorized TODOs (see rule 2/3 above).
- Reduce-motion respected for all animations (rule 7).
- 3D scenes load without blocking the main thread (rule 9).
- `status.md` and `process.md` updated.
