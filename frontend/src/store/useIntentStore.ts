import { create } from 'zustand'
import type {
  ContextObject,
  ContextQuestion,
  DomainIntent,
  EntitySet,
} from '@/types'

/**
 * The core pipeline store — single source of truth for the full
 * Intent → Context → Answer session state.
 *
 * See coding_conventions.md rule 10: never pass intent through
 * component props — read from this store.
 *
 * // TODO(contract): confirm ContextQuestion, ContextObject,
 * EntitySet schemas against ai/status.md once T3.5 is done.
 */
interface IntentState {
  /** Selected domain intent (landing page) */
  domain_intent: DomainIntent | null

  /** AI-generated context-gathering questions */
  context_questions: ContextQuestion[]

  /** User's answers to context questions */
  context_answers: Record<string, string | string[]>

  /** Structured context object assembled from answers */
  context_object: ContextObject | null

  /** Entities extracted from context (T3.6) */
  entity_set: EntitySet | null

  /** Current session ID */
  session_id: string | null

  /* Actions */
  setDomainIntent: (intent: DomainIntent) => void
  setContextQuestions: (questions: ContextQuestion[]) => void
  setContextAnswer: (questionId: string, answer: string | string[]) => void
  setContextObject: (obj: ContextObject) => void
  setEntitySet: (entities: EntitySet) => void
  setSessionId: (id: string) => void
  reset: () => void
}

const initialState = {
  domain_intent: null,
  context_questions: [],
  context_answers: {},
  context_object: null,
  entity_set: null,
  session_id: null,
}

export const useIntentStore = create<IntentState>((set) => ({
  ...initialState,

  setDomainIntent: (intent) =>
    set({ domain_intent: intent }),

  setContextQuestions: (questions) =>
    set({ context_questions: questions }),

  setContextAnswer: (questionId, answer) =>
    set((state) => ({
      context_answers: { ...state.context_answers, [questionId]: answer },
    })),

  setContextObject: (obj) =>
    set({ context_object: obj }),

  setEntitySet: (entities) =>
    set({ entity_set: entities }),

  setSessionId: (id) =>
    set({ session_id: id }),

  reset: () => set(initialState),
}))
