import { useState, useCallback } from 'react'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Loader2, CheckCircle2 } from 'lucide-react'
import { apiClient } from '@/services/apiClient'
import { logger } from '@/lib/logger'

interface WizardStep {
  id: string
  title: string
  question: string
  options: string[]
  type: 'radio' | 'multi_select'
}

const WIZARD_STEPS: WizardStep[] = [
  {
    id: 'product_type',
    title: 'Product Type',
    question: 'What is your product?',
    options: ['Ayurvedic medicine', 'Food / Nutraceutical', 'Cosmetic', 'Plant-based extract', 'Research formulation', 'Not sure'],
    type: 'radio',
  },
  {
    id: 'authoritative_text',
    title: 'Classical Origin',
    question: 'Is the formulation derived from an authoritative Ayurvedic text?',
    options: ['Yes (e.g., Charaka Samhita, Sushruta Samhita, Ashtanga Hridaya)', 'No', 'Not sure'],
    type: 'radio',
  },
  {
    id: 'formulation_novelty',
    title: 'Formulation Novelty',
    question: 'Is it a new formulation?',
    options: ['Existing classical formulation', 'Modified classical formulation', 'Completely new formulation', 'Not sure'],
    type: 'radio',
  },
  {
    id: 'biological_resources',
    title: 'Biological Resources',
    question: 'Does it use biological resources?',
    options: ['Plant-based herbs', 'Animal-derived ingredients', 'Microorganism-based', 'Marine resources', 'Mineral-based', 'No biological resources'],
    type: 'multi_select',
  },
]

interface ClassificationResult {
  classification: string
  regulatory_pathway: string
  ip_scores: Record<string, number>
  next_steps: string[]
}

/**
 * Product Classification Wizard — multi-step with glassmorphism cards.
 * See context.md §2 rule 6: classification is deterministic rules engine.
 */
export function ClassifyPage() {
  const navigate = useNavigate()
  const prefersReducedMotion = useReducedMotion()
  const [currentStep, setCurrentStep] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string | string[]>>({})
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<ClassificationResult | null>(null)
  const [direction, setDirection] = useState(1) // 1 = forward, -1 = back

  const step = WIZARD_STEPS[currentStep]
  const isLastStep = currentStep === WIZARD_STEPS.length - 1
  const currentAnswer = step ? answers[step.id] : undefined
  const hasAnswer = Array.isArray(currentAnswer) ? currentAnswer.length > 0 : !!currentAnswer

  const handleNext = useCallback(() => {
    if (isLastStep) {
      void handleSubmit()
    } else {
      setDirection(1)
      setCurrentStep((s) => s + 1)
    }
  }, [isLastStep, currentStep])

  const handleBack = useCallback(() => {
    setDirection(-1)
    setCurrentStep((s) => Math.max(0, s - 1))
  }, [])

  const handleSubmit = useCallback(async () => {
    setSubmitting(true)
    try {
      const response = await apiClient.post('/api/v1/classification', { answers })
      setResult(response.data as ClassificationResult)
    } catch {
      logger.info('Backend not available, using mock classification result')
      await new Promise((r) => setTimeout(r, 1200))
      setResult(generateMockResult(answers))
    }
    setSubmitting(false)
  }, [answers])

  // Show result view
  if (result) {
    return <ClassificationResultView result={result} onNavigateChat={() => navigate('/chat')} onReset={() => { setResult(null); setCurrentStep(0); setAnswers({}) }} />
  }

  if (!step) return null

  return (
    <div style={{ maxWidth: '640px', margin: '0 auto', padding: '20px 0' }}>
      {/* Step progress bar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '32px' }}>
        {WIZARD_STEPS.map((s, i) => (
          <div key={s.id} style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div style={{ height: '3px', borderRadius: '2px', backgroundColor: i <= currentStep ? 'var(--color-teal)' : 'rgba(255,255,255,0.06)', transition: 'background-color 0.3s ease' }} />
            <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-body)', color: i === currentStep ? 'var(--color-teal)' : 'var(--color-muted)' }}>
              {s.title}
            </span>
          </div>
        ))}
      </div>

      {/* Wizard card */}
      <AnimatePresence mode="wait" custom={direction}>
        <motion.div
          key={step.id}
          custom={direction}
          initial={prefersReducedMotion ? {} : { opacity: 0, x: direction * 40 }}
          animate={{ opacity: 1, x: 0 }}
          exit={prefersReducedMotion ? {} : { opacity: 0, x: direction * -40 }}
          transition={{ duration: 0.3 }}
          className="glass"
          style={{ padding: '32px', borderRadius: 'var(--radius)' }}
        >
          <p style={{ fontSize: '0.75rem', color: 'var(--color-teal)', fontFamily: 'var(--font-body)', marginBottom: '8px' }}>
            Step {currentStep + 1} of {WIZARD_STEPS.length}
          </p>
          <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.3rem', fontWeight: 600, color: 'var(--color-text)', marginBottom: '24px' }}>
            {step.question}
          </h3>

          {/* Options */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {step.options.map((opt) => {
              const isRadio = step.type === 'radio'
              const isSelected = isRadio ? currentAnswer === opt : (Array.isArray(currentAnswer) && currentAnswer.includes(opt))
              return (
                <button
                  key={opt}
                  onClick={() => {
                    if (isRadio) {
                      setAnswers((a) => ({ ...a, [step.id]: opt }))
                    } else {
                      const prev = Array.isArray(currentAnswer) ? currentAnswer : []
                      const next = prev.includes(opt) ? prev.filter((x) => x !== opt) : [...prev, opt]
                      setAnswers((a) => ({ ...a, [step.id]: next }))
                    }
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '14px 18px',
                    borderRadius: '10px',
                    textAlign: 'left',
                    cursor: 'pointer',
                    fontFamily: 'var(--font-body)',
                    fontSize: '0.88rem',
                    transition: 'all 0.2s ease',
                    backgroundColor: isSelected ? 'rgba(45, 212, 191, 0.1)' : 'rgba(30, 41, 59, 0.3)',
                    border: isSelected ? '1px solid rgba(45, 212, 191, 0.25)' : '1px solid rgba(255,255,255,0.06)',
                    color: isSelected ? 'var(--color-text)' : 'var(--color-muted)',
                  }}
                >
                  <span style={{
                    width: '18px', height: '18px', borderRadius: isRadio ? '50%' : '4px',
                    border: isSelected ? '2px solid var(--color-teal)' : '2px solid rgba(255,255,255,0.15)',
                    backgroundColor: isSelected ? 'var(--color-teal)' : 'transparent',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                  }}>
                    {isSelected && <span style={{ width: '8px', height: '8px', borderRadius: isRadio ? '50%' : '2px', backgroundColor: '#030712' }} />}
                  </span>
                  {opt}
                </button>
              )
            })}
          </div>
        </motion.div>
      </AnimatePresence>

      {/* Navigation */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '24px' }}>
        <button
          onClick={handleBack}
          disabled={currentStep === 0}
          style={{
            display: 'flex', alignItems: 'center', gap: '6px', padding: '10px 20px',
            fontSize: '0.85rem', fontFamily: 'var(--font-body)', fontWeight: 500,
            color: currentStep === 0 ? 'rgba(148,163,184,0.3)' : 'var(--color-muted)',
            backgroundColor: 'transparent', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '8px',
            cursor: currentStep === 0 ? 'not-allowed' : 'pointer',
          }}
        >
          <ArrowLeft size={15} /> Back
        </button>
        <button
          onClick={handleNext}
          disabled={!hasAnswer || submitting}
          style={{
            display: 'flex', alignItems: 'center', gap: '6px', padding: '10px 24px',
            fontSize: '0.85rem', fontFamily: 'var(--font-body)', fontWeight: 600,
            color: hasAnswer ? '#030712' : 'var(--color-muted)',
            backgroundColor: hasAnswer ? 'var(--color-teal)' : 'rgba(45,212,191,0.2)',
            border: 'none', borderRadius: '8px',
            cursor: hasAnswer && !submitting ? 'pointer' : 'not-allowed',
            transition: 'all 0.2s ease',
          }}
        >
          {submitting ? <><Loader2 size={15} style={{ animation: 'spin 1s linear infinite' }} /> Classifying...</>
            : isLastStep ? <><CheckCircle2 size={15} /> Classify</>
            : <>Next <ArrowRight size={15} /></>
          }
        </button>
      </div>
    </div>
  )
}

/* ──────────────────────────────────────────────────────────────
   Classification Result View (T3.2)
   ────────────────────────────────────────────────────────────── */

const IP_TYPES = ['Patent', 'Trademark', 'GI', 'Design', 'Copyright', 'Trade Secret', 'Plant Variety'] as const

interface ClassificationResultViewProps {
  result: ClassificationResult
  onNavigateChat: () => void
  onReset: () => void
}

function ClassificationResultView({ result, onNavigateChat, onReset }: ClassificationResultViewProps) {
  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px 0' }}>
      {/* Hero card */}
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ type: 'spring', stiffness: 200, damping: 20 }}
        className="glass"
        style={{ padding: '36px', borderRadius: 'var(--radius)', textAlign: 'center', marginBottom: '24px' }}
      >
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: 'spring', stiffness: 300 }}
          style={{
            display: 'inline-flex', padding: '8px 24px', borderRadius: '999px',
            backgroundColor: 'rgba(45, 212, 191, 0.12)', border: '1px solid rgba(45, 212, 191, 0.2)',
            marginBottom: '16px',
          }}
        >
          <span style={{ fontSize: '0.9rem', fontFamily: 'var(--font-heading)', fontWeight: 600, color: 'var(--color-teal)' }}>
            {result.classification}
          </span>
        </motion.div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.4rem', fontWeight: 700, color: 'var(--color-text)', marginBottom: '8px' }}>
          Product Classification
        </h2>
        <p style={{ fontSize: '0.9rem', fontFamily: 'var(--font-body)', color: 'var(--color-muted)' }}>
          Regulatory pathway: <strong style={{ color: 'var(--color-text)' }}>{result.regulatory_pathway}</strong>
        </p>
      </motion.div>

      {/* IP Protection Map — Radar-style grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="glass"
        style={{ padding: '28px', borderRadius: 'var(--radius)', marginBottom: '24px' }}
      >
        <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1rem', fontWeight: 600, color: 'var(--color-text)', marginBottom: '20px' }}>
          IP Protection Relevance Map
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px' }}>
          {IP_TYPES.map((ipType) => {
            const score = result.ip_scores[ipType.toUpperCase().replace(' ', '_')] ?? result.ip_scores[ipType.toLowerCase()] ?? 0
            const pct = Math.round(score * 100)
            return (
              <button
                key={ipType}
                onClick={onNavigateChat}
                style={{
                  padding: '16px', borderRadius: '10px', textAlign: 'center', cursor: 'pointer',
                  backgroundColor: score > 0.5 ? 'rgba(45, 212, 191, 0.08)' : 'rgba(30, 41, 59, 0.3)',
                  border: score > 0.5 ? '1px solid rgba(45, 212, 191, 0.15)' : '1px solid rgba(255,255,255,0.06)',
                  transition: 'all 0.2s ease',
                }}
              >
                {/* Score bar */}
                <div style={{ height: '4px', borderRadius: '2px', backgroundColor: 'rgba(255,255,255,0.06)', marginBottom: '10px', overflow: 'hidden' }}>
                  <div style={{
                    height: '100%', borderRadius: '2px', width: `${pct}%`,
                    backgroundColor: score > 0.7 ? 'var(--color-teal)' : score > 0.4 ? 'var(--color-gold)' : 'var(--color-muted)',
                    transition: 'width 0.5s ease',
                  }} />
                </div>
                <p style={{ fontFamily: 'var(--font-body)', fontSize: '0.78rem', fontWeight: 600, color: 'var(--color-text)', marginBottom: '2px' }}>
                  {ipType}
                </p>
                <p style={{ fontFamily: 'var(--font-body)', fontSize: '0.7rem', color: 'var(--color-muted)' }}>
                  {pct}% relevance
                </p>
              </button>
            )
          })}
        </div>
        <p style={{ fontSize: '0.7rem', color: 'var(--color-muted)', fontFamily: 'var(--font-body)', marginTop: '12px', fontStyle: 'italic' }}>
          Scores indicate potential applicability, not probability of legal success. Click any type to explore further.
        </p>
      </motion.div>

      {/* Next steps */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="glass"
        style={{ padding: '24px', borderRadius: 'var(--radius)', marginBottom: '24px' }}
      >
        <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1rem', fontWeight: 600, color: 'var(--color-text)', marginBottom: '14px' }}>
          Recommended Next Steps
        </h3>
        <ol style={{ paddingLeft: '20px' }}>
          {result.next_steps.map((step, i) => (
            <li key={i} style={{ fontSize: '0.85rem', fontFamily: 'var(--font-body)', color: 'var(--color-muted)', marginBottom: '8px', lineHeight: 1.5 }}>
              {step}
            </li>
          ))}
        </ol>
      </motion.div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
        <button onClick={onReset} style={{ padding: '10px 20px', fontSize: '0.85rem', fontFamily: 'var(--font-body)', color: 'var(--color-muted)', backgroundColor: 'transparent', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '8px', cursor: 'pointer' }}>
          Classify another product
        </button>
        <button onClick={onNavigateChat} style={{ padding: '10px 24px', fontSize: '0.85rem', fontFamily: 'var(--font-body)', fontWeight: 600, color: '#030712', backgroundColor: 'var(--color-teal)', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>
          Ask detailed questions →
        </button>
      </div>
    </div>
  )
}

/* ──────────────────────────────────────────────────────────────
   Mock result generator
   ────────────────────────────────────────────────────────────── */

function generateMockResult(answers: Record<string, string | string[]>): ClassificationResult {
  const productType = (answers.product_type as string) ?? 'Ayurvedic medicine'
  const isClassical = (answers.authoritative_text as string)?.includes('Yes')

  return {
    classification: isClassical ? 'Classical Ayurvedic Medicine (ASU)' : 'Proprietary Ayurvedic Medicine',
    regulatory_pathway: isClassical
      ? 'Schedule E — Classical medicines listed in authoritative texts. License under Drugs & Cosmetics Act Rule 158-B.'
      : 'Proprietary Medicine — requires license under Drugs & Cosmetics Act with Form 24 or 25-D.',
    ip_scores: {
      PATENT: isClassical ? 0.2 : 0.75,
      TRADEMARK: 0.85,
      GI: isClassical ? 0.6 : 0.15,
      DESIGN: 0.3,
      COPYRIGHT: 0.2,
      TRADE_SECRET: 0.65,
      PLANT_VARIETY: productType.includes('Plant') ? 0.5 : 0.1,
    },
    next_steps: [
      'File trademark application for your brand name and logo with the Trademark Registry',
      isClassical
        ? 'Verify your formulation against the Ayurvedic Pharmacopoeia (API/AFI) for compliance'
        : 'Prepare patent application focusing on the novel composition or process',
      'Complete ABS compliance check if using biological resources from India',
      'Consult a qualified IP attorney for formal filing strategy',
      'Review TKDL database for prior art (via IP India portal)',
    ],
  }
}
