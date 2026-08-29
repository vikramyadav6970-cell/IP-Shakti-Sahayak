import { useEffect, useState, useCallback } from 'react'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Loader2 } from 'lucide-react'
import { useIntentStore } from '@/store'
import { fetchContextQuestions, processContextAnswers } from '@/services/contextService'
import type { ContextQuestion } from '@/types'

/**
 * Context Gathering page — progressive reveal of AI-generated follow-up questions.
 * See context.md §1 pipeline stage 2.
 */
export function ContextPage() {
  const navigate = useNavigate()
  const prefersReducedMotion = useReducedMotion()
  const {
    domain_intent,
    context_answers,
    setContextQuestions,
    setContextAnswer,
    setContextObject,
    setEntitySet,
    setSessionId,
  } = useIntentStore()

  const [questions, setQuestions] = useState<ContextQuestion[]>([])
  const [visibleCount, setVisibleCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Redirect to home if no intent selected
  useEffect(() => {
    if (!domain_intent) {
      navigate('/')
    }
  }, [domain_intent, navigate])

  // Fetch questions on mount
  useEffect(() => {
    if (!domain_intent) return
    let cancelled = false

    async function load() {
      try {
        setLoading(true)
        setError(null)
        const qs = await fetchContextQuestions({ intent: domain_intent! })
        if (!cancelled) {
          setQuestions(qs)
          setContextQuestions(qs)
          setVisibleCount(qs.length > 0 ? 1 : 0)
          setLoading(false)
        }
      } catch {
        if (!cancelled) {
          setError('Failed to load questions. Please try again.')
          setLoading(false)
        }
      }
    }

    void load()
    return () => { cancelled = true }
  }, [domain_intent, setContextQuestions])

  // Show next question when current one is answered
  const handleAnswer = useCallback(
    (questionId: string, value: string | string[]) => {
      setContextAnswer(questionId, value)
      // Show next question if it exists
      const currentIdx = questions.findIndex((q) => q.id === questionId)
      if (currentIdx >= 0 && currentIdx + 1 < questions.length && visibleCount <= currentIdx + 1) {
        setVisibleCount(currentIdx + 2)
      }
    },
    [questions, visibleCount, setContextAnswer]
  )

  // Check if all required questions are answered
  const allAnswered = questions
    .filter((q) => q.required)
    .every((q) => {
      const ans = context_answers[q.id]
      if (Array.isArray(ans)) return ans.length > 0
      return !!ans
    })

  const handleSubmit = useCallback(async () => {
    if (!domain_intent || submitting) return
    setSubmitting(true)
    try {
      const result = await processContextAnswers({
        intent: domain_intent,
        answers: context_answers,
      })
      // Store session_id from backend — needed for chat API calls
      if (result.session_id) {
        setSessionId(result.session_id)
      }
      setContextObject({
        domain_intent,
        answers: context_answers,
      })
      const es = result.entity_set as Record<string, unknown>
      setEntitySet({
        herbs: (es.herbs as string[]) ?? [],
        jurisdictions: (es.jurisdictions as string[]) ?? [],
        ip_types: (es.ip_types as string[]) ?? [],
        biological_resources: (es.biological_resources as string[]) ?? [],
        formulation_name: (es.formulation_name as string | null) ?? null,
        destination_country: (es.destination_country as string | null) ?? null,
        regulatory_regime: (es.regulatory_regime as string | null) ?? null,
      })
      navigate('/chat')
    } catch {
      setError('Failed to process context. Please try again.')
      setSubmitting(false)
    }
  }, [domain_intent, context_answers, submitting, navigate, setContextObject, setEntitySet, setSessionId])

  // Progress
  const answeredCount = questions.filter((q) => {
    const ans = context_answers[q.id]
    if (Array.isArray(ans)) return ans.length > 0
    return !!ans
  }).length
  const progress = questions.length > 0 ? (answeredCount / questions.length) * 100 : 0

  if (!domain_intent) return null

  return (
    <div
      style={{
        maxWidth: '680px',
        margin: '0 auto',
        padding: '20px 0',
      }}
    >
      {/* Intent header */}
      <motion.div
        initial={prefersReducedMotion ? {} : { opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ marginBottom: '24px' }}
      >
        <p style={{ fontSize: '0.8rem', color: 'var(--color-muted)', fontFamily: 'var(--font-body)', marginBottom: '4px' }}>
          Gathering context for
        </p>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.5rem', fontWeight: 700, color: 'var(--color-text)' }}>
          {domain_intent} Guidance
        </h2>
      </motion.div>

      {/* Progress bar */}
      <motion.div
        initial={prefersReducedMotion ? {} : { opacity: 0 }}
        animate={{ opacity: 1 }}
        style={{
          height: '4px',
          borderRadius: '2px',
          backgroundColor: 'rgba(255, 255, 255, 0.06)',
          marginBottom: '32px',
          overflow: 'hidden',
        }}
      >
        <motion.div
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
          style={{
            height: '100%',
            borderRadius: '2px',
            backgroundColor: 'var(--color-teal)',
          }}
        />
      </motion.div>

      {/* Loading state */}
      {loading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="glass"
          style={{
            padding: '48px',
            borderRadius: 'var(--radius)',
            textAlign: 'center',
          }}
        >
          <Loader2
            size={28}
            style={{ color: 'var(--color-teal)', margin: '0 auto 12px', animation: 'spin 1s linear infinite' }}
          />
          <p style={{ color: 'var(--color-muted)', fontSize: '0.9rem', fontFamily: 'var(--font-body)' }}>
            Generating targeted questions...
          </p>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </motion.div>
      )}

      {/* Error state */}
      {error && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="glass"
          style={{
            padding: '32px',
            borderRadius: 'var(--radius)',
            textAlign: 'center',
            border: '1px solid rgba(239, 68, 68, 0.2)',
          }}
        >
          <p style={{ color: '#ef4444', fontSize: '0.9rem', fontFamily: 'var(--font-body)', marginBottom: '16px' }}>
            {error}
          </p>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: '8px 20px',
              fontSize: '0.85rem',
              fontFamily: 'var(--font-body)',
              fontWeight: 500,
              color: 'var(--color-text)',
              backgroundColor: 'rgba(255, 255, 255, 0.06)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '8px',
              cursor: 'pointer',
            }}
          >
            Try again
          </button>
        </motion.div>
      )}

      {/* Question cards — progressive reveal */}
      <AnimatePresence mode="sync">
        {questions.slice(0, visibleCount).map((q, i) => (
          <motion.div
            key={q.id}
            initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: prefersReducedMotion ? 0 : 0.12, duration: 0.4 }}
            className="glass"
            style={{
              padding: '24px',
              borderRadius: 'var(--radius)',
              marginBottom: '16px',
            }}
          >
            <label
              htmlFor={q.id}
              style={{
                display: 'block',
                fontFamily: 'var(--font-body)',
                fontSize: '0.95rem',
                fontWeight: 500,
                color: 'var(--color-text)',
                marginBottom: '14px',
              }}
            >
              <span style={{ color: 'var(--color-teal)', marginRight: '8px', fontSize: '0.8rem' }}>
                {i + 1}/{questions.length}
              </span>
              {q.question_text}
            </label>

            <QuestionInput
              question={q}
              value={context_answers[q.id]}
              onChange={(val) => handleAnswer(q.id, val)}
            />
          </motion.div>
        ))}
      </AnimatePresence>

      {/* Continue button */}
      {!loading && !error && questions.length > 0 && (
        <AnimatePresence>
          {allAnswered && (
            <motion.div
              initial={prefersReducedMotion ? {} : { opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              style={{ marginTop: '24px', display: 'flex', justifyContent: 'flex-end' }}
            >
              <button
                onClick={() => void handleSubmit()}
                disabled={submitting}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '12px 28px',
                  fontSize: '0.9rem',
                  fontFamily: 'var(--font-body)',
                  fontWeight: 600,
                  color: '#030712',
                  backgroundColor: submitting ? 'rgba(45, 212, 191, 0.5)' : 'var(--color-teal)',
                  border: 'none',
                  borderRadius: '10px',
                  cursor: submitting ? 'wait' : 'pointer',
                  transition: 'all 0.2s ease',
                }}
              >
                {submitting ? (
                  <>
                    <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
                    Processing...
                  </>
                ) : (
                  <>
                    Continue
                    <ArrowRight size={16} />
                  </>
                )}
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      )}
    </div>
  )
}

/* ──────────────────────────────────────────────────────────────
   QuestionInput — renders the correct input based on answer_type
   ────────────────────────────────────────────────────────────── */

interface QuestionInputProps {
  question: ContextQuestion
  value: string | string[] | undefined
  onChange: (value: string | string[]) => void
}

function QuestionInput({ question, value, onChange }: QuestionInputProps) {
  const inputStyle = {
    width: '100%',
    padding: '10px 14px',
    fontSize: '0.88rem',
    fontFamily: 'var(--font-body)',
    color: 'var(--color-text)',
    backgroundColor: 'rgba(30, 41, 59, 0.5)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '8px',
    outline: 'none',
    transition: 'border-color 0.2s ease',
  } as const

  switch (question.answer_type) {
    case 'text':
      return (
        <input
          id={question.id}
          type="text"
          value={(value as string) ?? ''}
          onChange={(e) => onChange(e.target.value)}
          placeholder={question.placeholder ?? 'Type your answer...'}
          style={inputStyle}
          onFocus={(e) => { e.target.style.borderColor = 'rgba(45, 212, 191, 0.3)' }}
          onBlur={(e) => { e.target.style.borderColor = 'rgba(255, 255, 255, 0.08)' }}
        />
      )

    case 'select':
      return (
        <select
          id={question.id}
          value={(value as string) ?? ''}
          onChange={(e) => onChange(e.target.value)}
          style={{ ...inputStyle, cursor: 'pointer' }}
        >
          <option value="">Select an option...</option>
          {question.options?.map((opt) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      )

    case 'radio':
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }} role="radiogroup" aria-labelledby={question.id}>
          {question.options?.map((opt) => (
            <label
              key={opt}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '10px 14px',
                borderRadius: '8px',
                cursor: 'pointer',
                backgroundColor: value === opt ? 'rgba(45, 212, 191, 0.08)' : 'rgba(30, 41, 59, 0.3)',
                border: value === opt ? '1px solid rgba(45, 212, 191, 0.2)' : '1px solid rgba(255, 255, 255, 0.06)',
                transition: 'all 0.2s ease',
                fontSize: '0.85rem',
                fontFamily: 'var(--font-body)',
                color: value === opt ? 'var(--color-text)' : 'var(--color-muted)',
              }}
            >
              <input
                type="radio"
                name={question.id}
                value={opt}
                checked={value === opt}
                onChange={() => onChange(opt)}
                style={{ accentColor: 'var(--color-teal)' }}
              />
              {opt}
            </label>
          ))}
        </div>
      )

    case 'multi_select':
    case 'checkbox': {
      const selected = Array.isArray(value) ? value : []
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {question.options?.map((opt) => {
            const isChecked = selected.includes(opt)
            return (
              <label
                key={opt}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '10px 14px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  backgroundColor: isChecked ? 'rgba(45, 212, 191, 0.08)' : 'rgba(30, 41, 59, 0.3)',
                  border: isChecked ? '1px solid rgba(45, 212, 191, 0.2)' : '1px solid rgba(255, 255, 255, 0.06)',
                  transition: 'all 0.2s ease',
                  fontSize: '0.85rem',
                  fontFamily: 'var(--font-body)',
                  color: isChecked ? 'var(--color-text)' : 'var(--color-muted)',
                }}
              >
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={() => {
                    const next = isChecked
                      ? selected.filter((s) => s !== opt)
                      : [...selected, opt]
                    onChange(next)
                  }}
                  style={{ accentColor: 'var(--color-teal)' }}
                />
                {opt}
              </label>
            )
          })}
        </div>
      )
    }

    default:
      return null
  }
}
