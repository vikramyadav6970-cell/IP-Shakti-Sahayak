/**
 * Types for chat/answer API responses.
 * See context.md §2 for hard constraints on citations and confidence.
 *
 * Aligned with backend/app/schemas/chat.py as of 2026-08-29.
 */

/** One citation referencing a source document */
export interface Citation {
  id: string
  document_title: string
  section_reference: string | null
  collection: QdrantCollection | string
  jurisdiction: string
  source_authority?: string
  source_url?: string
  relevance_score?: number | null
  excerpt?: string | null
  document_type?: string | null
}

/** The 5 Qdrant collections — see context.md §3a */
export type QdrantCollection =
  | 'legal_statutory'
  | 'standards_formulations'
  | 'case_law_prior_art'
  | 'procedural_forms'
  | 'international_export'

/** Confidence level — always shown as text, not just color (accessibility rule) */
export type ConfidenceLabel = 'HIGH' | 'MEDIUM' | 'LOW' | 'ABSTAIN'

/** Chat request payload — matches backend ChatRequest schema */
export interface ChatRequest {
  question: string
  domain_intent: string
  session_id: string | null
  jurisdiction: string
  language: string
  conversation_id: string | null
}

/** Chat response from the backend — matches backend ChatResponse schema */
export interface ChatResponse {
  answer: string
  confidence: number
  confidence_label: ConfidenceLabel
  classification: string | null
  abs_assessment?: Record<string, unknown> | null
  citations: Citation[]
  requires_human_review: boolean
  conversation_id: string | null
  sub_tasks_run: string[]
  sources_by_collection: Record<string, number>
}

/** A single message in the conversation */
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  citations?: Citation[]
  confidence?: number
  confidence_label?: ConfidenceLabel
  requires_human_review?: boolean
  sub_tasks_run?: string[]
  sources_by_collection?: Record<string, number>
}
