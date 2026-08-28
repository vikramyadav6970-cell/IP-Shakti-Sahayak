/**
 * Types for chat/answer API responses.
 * See context.md §2 for hard constraints on citations and confidence.
 *
 * // TODO(contract): confirm against backend/status.md once T3.1 is done.
 */

/** One citation referencing a source document */
export interface Citation {
  id: string
  document_title: string
  section_reference: string
  collection: QdrantCollection
  jurisdiction: string
  source_authority: string
  source_url?: string
  relevance_score: number
  excerpt: string
}

/** The 5 Qdrant collections — see context.md §3a */
export type QdrantCollection =
  | 'legal_statutory'
  | 'standards_formulations'
  | 'case_law_prior_art'
  | 'procedural_forms'
  | 'international_export'

/** Confidence level — always shown as text, not just color (accessibility rule) */
export type ConfidenceLabel = 'HIGH' | 'MEDIUM' | 'LOW'

import type { ContextObject } from './intent'

/** Chat request payload */
export interface ChatRequest {
  question: string
  domain_intent: string
  context_object: ContextObject | Record<string, unknown> | null
  jurisdiction: string
  language: string
  conversation_id: string | null
}

/** Chat response from the backend */
export interface ChatResponse {
  answer: string
  confidence: number
  confidence_label: ConfidenceLabel
  classification: string | null
  citations: Citation[]
  requires_human_review: boolean
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
