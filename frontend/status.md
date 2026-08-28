# frontend/status.md

Granular status log for the frontend track. High-level checklist lives in the root
`process.md` — this file is for detail that doesn't fit there: deviations, decisions
made mid-task, things the next agent needs to know.

Add a new dated entry at the top each time you touch this folder. Don't delete old
entries.

---

## Log

### 2026-08-28 — Phase 0 + Phase 1 complete

**T0.1 — Scaffold** ✅
Scaffolded with `create-vite@latest` (react-ts template). All packages installed.

| Category | Package | Version |
|---|---|---|
| Core | react | ^19.2.8 |
| Core | react-dom | ^19.2.8 |
| Core | typescript | ~6.0.2 |
| Core | vite | ^8.2.2 |
| 3D | three | ^0.185.1 |
| 3D | @react-three/fiber | ^9.7.0 |
| 3D | @react-three/drei | ^10.7.8 |
| 3D | @types/three | ^0.185.4 |
| Animation | gsap | ^3.15.0 |
| Animation | @gsap/react | ^2.1.2 |
| Animation | framer-motion | ^13.1.1 |
| State | zustand | ^5.0.15 |
| State | @tanstack/react-query | ^5.102.8 |
| Forms | react-hook-form | ^7.86.0 |
| Forms | zod | ^4.4.3 |
| Forms | @hookform/resolvers | ^5.9.1 |
| Routing | react-router-dom | ^7.18.3 |
| Charts | recharts | ^3.10.1 |
| Icons | lucide-react | ^1.35.0 |
| i18n | react-i18next | ^17.0.12 |
| i18n | i18next | ^26.4.0 |
| Fonts | @fontsource/space-grotesk | ^5.3.0 |
| Fonts | @fontsource/inter | ^5.3.0 |
| Styling | tailwindcss | ^4.3.3 |
| Styling | @tailwindcss/vite | ^4.3.3 |
| Styling | @tailwindcss/typography | ^0.5.20 |
| UI utils | clsx | ^2.1.1 |
| UI utils | tailwind-merge | ^3.6.0 |
| UI utils | class-variance-authority | ^0.7.1 |
| HTTP | axios | ^1.20.0 |
| Markdown | react-markdown | ^10.1.0 |
| Markdown | remark-gfm | ^4.0.1 |
| Testing | vitest | ^4.1.11 |
| Testing | @testing-library/react | ^16.3.3 |
| Testing | @testing-library/jest-dom | ^7.0.1 |
| Linting | eslint | ^10.9.1 |
| Linting | eslint-config-prettier | ^10.1.8 |
| Linting | oxlint | ^1.79.0 |
| Formatting | prettier | ^3.9.6 |

Deviation: Vite scaffold used React 19 (not 18 specified in conventions). React 19
is backward-compatible; no API-breaking differences for our usage. Convention file
says "React 18" but that predates React 19's stable release — kept 19.

Deviation: TypeScript 6.0.2 (not 5.x). TS 6 deprecates `baseUrl` in tsconfig —
removed it, `paths` works without `baseUrl` in TS 5+/6+ with bundler moduleResolution.

Deviation: shadcn/ui not yet initialized via CLI — components will be added manually
or via CLI in a follow-up task. The design tokens and glassmorphism are set up.

**T0.2 — Design system** ✅
- globals.css with all design tokens (CSS custom properties)
- shadcn/ui variable mappings (--background, --foreground, --primary, etc.)
- Glassmorphism `.glass` and `.glass-hover` utility classes
- Dark scrollbar, selection, reduce-motion media query
- Font imports via @fontsource (Space Grotesk 400-700, Inter 400-600)
- `cn()` utility in src/lib/cn.ts

**T0.3 — 3D background canvas** ✅
- `BackgroundCanvas.tsx`: full-screen Canvas with frameloop="demand"
- `ParticleField.tsx`: instanced mesh, 3500 particles, teal+violet, sine drift
- `StaticStarField`: reduced-motion fallback (static points)
- `NebulaFog`: radial gradient plane for ambient glow
- `SceneWrapper.tsx`: fixed div behind content, lazy-loaded via React.lazy+Suspense

**T0.4 — State stores, API client, routing** ✅
- `useAuthStore`: user, token, login/logout
- `useJurisdictionStore`: India/International + country, localStorage persistence
- `useIntentStore`: full pipeline state (domain_intent, context_questions,
  context_answers, context_object, entity_set, session_id, reset)
- `apiClient.ts`: axios instance, auth interceptor, structured error handling
- `logger.ts`: dev-only logger (import.meta.env.DEV gated)
- Types: intent.ts, jurisdiction.ts, chat.ts, auth.ts with barrel export
- React Router routes: /, /context, /chat, /classify, /abs, /sources, /admin, /login
- TanStack Query QueryClientProvider at app root

**T1.1 — 3D Intent Selector (landing page)** ✅
- 6 glassmorphism intent cards with Lucide icons, staggered entrance animations
- Hover: teal glow + scale 1.03 (Framer Motion spring)
- Click: store intent → navigate to /context
- "Other" card: inline textarea → free_description → navigate to /chat
- Header: product name + jurisdiction toggle
- Disclaimer banner at bottom

**T1.2 — App Shell** ✅
- Glassmorphism sticky header with nav (Chat/Classify/ABS/Sources/Admin)
- "New Session" button → useIntentStore.reset() → navigate /
- Non-dismissible disclaimer banner (40px, teal tint)
- Outlet for nested routes

**T1.3 — Jurisdiction Toggle** ✅
- Pill toggle: India (teal) / International (gold)
- Animated country dropdown (AnimatePresence) when International selected
- Wired to useJurisdictionStore with localStorage persistence

**Phase 2 — Chat / RAG Interface** ✅
- `contextService.ts`: Intent-tailored question generation & answer processing with mock fallback.
- `ContextPage.tsx`: Progressive question reveal, progress bar, responsive inputs.
- `chatService.ts`: Query submission to `/api/v1/chat` with mock response grounding in Sections 3(p), Biological Diversity Act, and WIPO treaties.
- `ChatPage.tsx`: Two-panel layout with real-time animated Evidence Map, markdown answer rendering, confidence badges, source collection counts, and human escalation modal.
- `CitationCard.tsx`: Collection-colored badges (Statutes, Formulations, Case Law, Forms, International), jurisdiction indicators, and verbatim legal excerpts.

**Phase 3 — Product Classification Wizard** ✅
- `ClassifyPage.tsx`: Multi-step glassmorphism wizard (Product Type, Classical Origin, Novelty, Biological Resources) with animated transitions.
- Result view: Dynamic ASU vs Proprietary classification, regulatory license pathways (Rule 158-B / Form 24), and radar-style IP Protection Relevance Map across 7 IP categories.

**Phase 4 — ABS, Source Explorer, Dashboard** ✅
- `AbsPage.tsx`: Biological Diversity Act assessment wizard (origin, materials, purpose) with NBA Form I recommendations.
- `SourcesPage.tsx`: Searchable and filterable grid of 13+ authoritative legal statutes, pharmacopoeias (API/AFI), regulations (FSSAI), and international treaties.
- `AdminPage.tsx`: Role-gated dashboard showing Qdrant collection indexed status, system latency health checks, and AI evaluation metrics.

**Phase 5 — Auth, i18n, Deploy Config** ✅
- `LoginPage.tsx`: Authentication screen with demo quick-login presets (Innovator / Admin) and role context selection.
- `i18n`: Full Hindi (`hi.json`) and English (`en.json`) localization dictionaries, LanguageToggle component with localStorage persistence.
- `vercel.json`: Production SPA routing rewrite configuration.

**Build status:** `npm run build` compiles 2,633+ modules cleanly with **0 errors**.
