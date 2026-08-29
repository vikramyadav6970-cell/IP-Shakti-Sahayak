import { apiClient } from './apiClient'
import type { ContextQuestion, DomainIntent } from '@/types'
import { logger } from '@/lib/logger'

/**
 * Backend answer_type mapping → frontend AnswerType.
 * Backend uses 'text' | 'single_choice' | 'multiple_choice' | 'FREE_TEXT' | 'SINGLE_SELECT' | 'MULTI_SELECT'
 * Frontend uses 'text' | 'select' | 'multi_select' | 'radio' | 'checkbox'
 */
const ANSWER_TYPE_MAP: Record<string, ContextQuestion['answer_type']> = {
  text: 'text',
  single_choice: 'select',
  multiple_choice: 'multi_select',
  FREE_TEXT: 'text',
  SINGLE_SELECT: 'select',
  MULTI_SELECT: 'multi_select',
}

function mapAnswerType(backendType: string): ContextQuestion['answer_type'] {
  return ANSWER_TYPE_MAP[backendType] ?? 'text'
}

/**
 * Mock context questions per intent — used until backend is available.
 */
const MOCK_QUESTIONS: Record<DomainIntent, ContextQuestion[]> = {
  BUSINESS: [
    {
      id: 'biz_product_type',
      question_text: 'What type of Ayurvedic product are you looking to protect?',
      answer_type: 'select',
      options: ['Classical medicine', 'Proprietary medicine', 'Cosmetic', 'Food supplement', 'Personal care', 'Other'],
      required: true,
    },
    {
      id: 'biz_brand',
      question_text: 'Do you have an existing brand name or logo?',
      answer_type: 'radio',
      options: ['Yes, registered', 'Yes, unregistered', 'No, need to create one'],
      required: true,
    },
    {
      id: 'biz_market',
      question_text: 'Which markets are you targeting?',
      answer_type: 'multi_select',
      options: ['India only', 'India + Export', 'International only'],
      required: true,
    },
  ],
  EXPORT: [
    {
      id: 'exp_herbs',
      question_text: 'Which key herbs or ingredients are in your product?',
      answer_type: 'text',
      required: true,
      placeholder: 'e.g., Ashwagandha, Turmeric, Neem...',
    },
    {
      id: 'exp_country',
      question_text: 'What is the destination country for export?',
      answer_type: 'select',
      options: ['USA', 'EU (any member state)', 'UK', 'Japan', 'Australia', 'Canada', 'UAE', 'Other'],
      required: true,
    },
    {
      id: 'exp_purpose',
      question_text: 'Is this for commercial sale or research purposes?',
      answer_type: 'radio',
      options: ['Commercial sale', 'Research / academic', 'Both'],
      required: true,
    },
    {
      id: 'exp_nba',
      question_text: 'Have you approached the National Biodiversity Authority (NBA)?',
      answer_type: 'radio',
      options: ['Yes, approval obtained', 'Yes, application pending', 'No', 'Not sure if needed'],
      required: true,
    },
  ],
  MEDICINAL: [
    {
      id: 'med_type',
      question_text: 'Is your product a classical or proprietary formulation?',
      answer_type: 'radio',
      options: ['Classical (from authoritative text)', 'Proprietary (new formulation)', 'New drug', 'Phytopharmaceutical', 'Not sure'],
      required: true,
    },
    {
      id: 'med_text',
      question_text: 'Is the formulation derived from an authoritative Ayurvedic text?',
      answer_type: 'radio',
      options: ['Yes (e.g., Charaka Samhita, Sushruta Samhita)', 'No', 'Partially based on classical text'],
      required: true,
    },
    {
      id: 'med_new_ingredients',
      question_text: 'Does it contain any new or non-traditional ingredients?',
      answer_type: 'radio',
      options: ['No, all traditional ingredients', 'Yes, includes modern additives', 'Yes, novel combination'],
      required: true,
    },
  ],
  PATENT: [
    {
      id: 'pat_novel',
      question_text: 'What is the novel aspect of your invention?',
      answer_type: 'text',
      required: true,
      placeholder: 'Describe what makes your formulation/process new...',
    },
    {
      id: 'pat_type',
      question_text: 'What type of innovation is this?',
      answer_type: 'radio',
      options: ['New formulation / composition', 'New extraction process', 'New use of known herb', 'New combination of known herbs', 'Device / apparatus'],
      required: true,
    },
    {
      id: 'pat_prior_art',
      question_text: 'Have you done a prior art search?',
      answer_type: 'radio',
      options: ['Yes, found no matches', 'Yes, found similar prior art', 'No, need assistance', 'Not sure what this means'],
      required: true,
    },
    {
      id: 'pat_tkdl',
      question_text: 'Is this formulation or its base found in traditional knowledge databases?',
      answer_type: 'radio',
      options: ['Yes', 'No', 'Not sure'],
      required: true,
    },
  ],
  RESEARCH: [
    {
      id: 'res_type',
      question_text: 'What type of research is this?',
      answer_type: 'radio',
      options: ['Clinical trial', 'Pharmacological study', 'IP landscape analysis', 'Ethnobotanical research', 'Other'],
      required: true,
    },
    {
      id: 'res_bio',
      question_text: 'Does your research involve biological resources from India?',
      answer_type: 'radio',
      options: ['Yes', 'No', 'Not sure'],
      required: true,
    },
    {
      id: 'res_international',
      question_text: 'Will results be published or used internationally?',
      answer_type: 'radio',
      options: ['Yes, international publication', 'Yes, international patent filing', 'No, India only', 'Both publication and patent'],
      required: true,
    },
  ],
  OTHER: [],
}

interface FetchQuestionsParams {
  intent: DomainIntent
}

interface ProcessContextParams {
  intent: DomainIntent
  answers: Record<string, string | string[]>
}

interface ProcessContextResult {
  session_id: string
  context_object: Record<string, unknown>
  entity_set: Record<string, unknown>
}

/**
 * Fetch context-gathering questions for a given intent.
 * Backend returns { intent, questions } — we extract .questions and map field names.
 */
export async function fetchContextQuestions({ intent }: FetchQuestionsParams): Promise<ContextQuestion[]> {
  try {
    const response = await apiClient.get<{ intent: string; questions: Array<{
      question_id: string
      question_text: string
      answer_type: string
      options?: string[]
      required: boolean
      placeholder?: string
      help_text?: string
    }> }>(
      `/api/v1/context/questions`,
      { params: { intent } }
    )
    // Map backend field names → frontend field names
    return response.data.questions.map((q) => ({
      id: q.question_id,
      question_text: q.question_text,
      answer_type: mapAnswerType(q.answer_type),
      options: q.options,
      required: q.required,
      placeholder: q.placeholder,
      help_text: q.help_text,
    }))
  } catch {
    logger.info('Backend not available, using mock context questions for intent:', intent)
    await new Promise((resolve) => setTimeout(resolve, 600))
    return MOCK_QUESTIONS[intent] ?? []
  }
}

/**
 * Process context answers — sends to backend for entity extraction.
 * Backend returns { session_id, context_object, entity_set }.
 */
export async function processContextAnswers({ intent, answers }: ProcessContextParams): Promise<ProcessContextResult> {
  try {
    const response = await apiClient.post<ProcessContextResult>('/api/v1/context/process', {
      intent,
      answers,
    })
    return response.data
  } catch {
    logger.info('Backend not available, using mock context processing')
    await new Promise((resolve) => setTimeout(resolve, 800))
    return {
      session_id: `mock-session-${Date.now()}`,
      context_object: { domain_intent: intent, answers },
      entity_set: {
        herbs: [],
        jurisdictions: ['INDIA'],
        ip_types: [],
        biological_resources: [],
        formulation_name: null,
        destination_country: null,
        regulatory_regime: null,
      },
    }
  }
}
