import { describe, it, expect } from 'vitest'
import { fetchContextQuestions, processContextAnswers } from '../services/contextService'
import { sendChatQuery } from '../services/chatService'

describe('Frontend Services Suite (with Mock Fallback)', () => {
  describe('contextService', () => {
    it('returns tailored context questions for BUSINESS intent', async () => {
      const questions = await fetchContextQuestions({ intent: 'BUSINESS' })
      expect(questions.length).toBeGreaterThan(0)
      expect(questions[0]?.id).toBe('biz_product_type')
    })

    it('returns tailored context questions for PATENT intent', async () => {
      const questions = await fetchContextQuestions({ intent: 'PATENT' })
      expect(questions.length).toBeGreaterThan(0)
      expect(questions.some((q) => q.id === 'pat_novel')).toBe(true)
    })

    it('returns tailored context questions for EXPORT intent', async () => {
      const questions = await fetchContextQuestions({ intent: 'EXPORT' })
      expect(questions.length).toBeGreaterThan(0)
      expect(questions.some((q) => q.id === 'exp_nba')).toBe(true)
    })

    it('processes context answers and returns entity sets', async () => {
      const result = await processContextAnswers({
        intent: 'PATENT',
        answers: { pat_novel: 'Turmeric composition' },
      })
      expect(result).toHaveProperty('context_object')
      expect(result).toHaveProperty('entity_set')
    })
  })

  describe('chatService', () => {
    it('generates grounded response with citations and confidence metadata', async () => {
      const res = await sendChatQuery({
        question: 'How does Section 3(p) affect traditional formulations?',
        domain_intent: 'PATENT',
        context_object: null,
        jurisdiction: 'INDIA',
        language: 'en',
        conversation_id: null,
      })

      expect(res).toHaveProperty('answer')
      expect(res.answer).toContain('Section 3(p)')
      expect(res.confidence).toBeGreaterThan(0)
      expect(['HIGH', 'MEDIUM', 'LOW']).toContain(res.confidence_label)
      expect(Array.isArray(res.citations)).toBe(true)
      expect(res.citations.length).toBeGreaterThan(0)
      expect(res.citations[0]).toHaveProperty('document_title')
      expect(res.citations[0]).toHaveProperty('excerpt')
    })
  })
})
