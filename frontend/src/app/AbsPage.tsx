import { useState, useCallback } from 'react'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { ArrowLeft, ArrowRight, Loader2, Shield } from 'lucide-react'
import { logger } from '@/lib/logger'

interface AbsStep {
  id: string
  title: string
  question: string
  options: string[]
  type: 'radio' | 'multi_select'
}

const ABS_STEPS: AbsStep[] = [
  {
    id: 'bio_resources',
    title: 'Biological Resources',
    question: 'Does your product or research involve biological resources?',
    options: ['Yes, plant-based', 'Yes, animal-derived', 'Yes, microorganism', 'No biological resources', 'Not sure'],
    type: 'radio',
  },
  {
    id: 'which_resources',
    title: 'Resource Details',
    question: 'Which biological resources are involved?',
    options: ['Medicinal plants/herbs', 'Essential oils', 'Extracts/concentrates', 'Seeds/genetic material', 'Traditional fermentation cultures', 'Marine organisms'],
    type: 'multi_select',
  },
  {
    id: 'origin',
    title: 'Origin',
    question: 'Where do these biological resources originate?',
    options: ['India (wild-collected)', 'India (cultivated)', 'Imported', 'Multiple origins', 'Unknown origin'],
    type: 'radio',
  },
  {
    id: 'purpose',
    title: 'Purpose',
    question: 'What is the purpose of accessing these resources?',
    options: ['Commercial product development', 'Academic/basic research', 'Bio-survey / bio-utilization', 'Transfer to third party', 'Publication of research results'],
    type: 'radio',
  },
]

interface AbsResult {
  relevance: 'HIGH' | 'MEDIUM' | 'LOW' | 'NOT_APPLICABLE'
  summary: string
  next_steps: string[]
}

export function AbsPage() {
  const prefersReducedMotion = useReducedMotion()
  const [currentStep, setCurrentStep] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string | string[]>>({})
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<AbsResult | null>(null)
  const [direction, setDirection] = useState(1)

  const step = ABS_STEPS[currentStep]
  const isLastStep = currentStep === ABS_STEPS.length - 1
  const currentAnswer = step ? answers[step.id] : undefined
  const hasAnswer = Array.isArray(currentAnswer) ? currentAnswer.length > 0 : !!currentAnswer

  const handleSubmit = useCallback(async () => {
    setSubmitting(true)
    try {
      logger.info('ABS assessment submitted:', answers)
      await new Promise((r) => setTimeout(r, 1000))
      setResult(generateAbsResult(answers))
    } finally {
      setSubmitting(false)
    }
  }, [answers])

  if (result) {
    const relevanceColors = {
      HIGH:           { bg: 'rgba(239, 68, 68, 0.1)',  text: '#ef4444', border: 'rgba(239, 68, 68, 0.2)' },
      MEDIUM:         { bg: 'rgba(245, 158, 11, 0.1)', text: '#f59e0b', border: 'rgba(245, 158, 11, 0.2)' },
      LOW:            { bg: 'rgba(45, 212, 191, 0.1)',  text: '#2dd4bf', border: 'rgba(45, 212, 191, 0.2)' },
      NOT_APPLICABLE: { bg: 'rgba(148, 163, 184, 0.1)', text: '#94a3b8', border: 'rgba(148, 163, 184, 0.2)' },
    }
    const style = relevanceColors[result.relevance]

    return (
      <div style={{ maxWidth: '640px', margin: '0 auto', padding: '20px 0' }}>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass" style={{ padding: '32px', borderRadius: 'var(--radius)', marginBottom: '24px', textAlign: 'center' }}>
          <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.2, type: 'spring' }}>
            <Shield size={36} style={{ color: style.text, margin: '0 auto 12px' }} />
          </motion.div>
          <span style={{ display: 'inline-flex', padding: '4px 16px', borderRadius: '999px', backgroundColor: style.bg, border: `1px solid ${style.border}`, fontSize: '0.85rem', fontWeight: 600, fontFamily: 'var(--font-body)', color: style.text, marginBottom: '12px' }}>
            {result.relevance} ABS Relevance
          </span>
          <p style={{ fontSize: '0.9rem', color: 'var(--color-muted)', fontFamily: 'var(--font-body)', marginTop: '8px' }}>{result.summary}</p>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="glass" style={{ padding: '24px', borderRadius: 'var(--radius)', marginBottom: '24px' }}>
          <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1rem', fontWeight: 600, color: 'var(--color-text)', marginBottom: '14px' }}>Required Steps</h3>
          <ol style={{ paddingLeft: '20px' }}>
            {result.next_steps.map((s, i) => (
              <li key={i} style={{ fontSize: '0.85rem', fontFamily: 'var(--font-body)', color: 'var(--color-muted)', marginBottom: '8px', lineHeight: 1.5 }}>{s}</li>
            ))}
          </ol>
        </motion.div>

        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <button onClick={() => { setResult(null); setCurrentStep(0); setAnswers({}) }} style={{ padding: '10px 20px', fontSize: '0.85rem', fontFamily: 'var(--font-body)', color: 'var(--color-muted)', backgroundColor: 'transparent', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '8px', cursor: 'pointer' }}>
            Run another assessment
          </button>
        </div>
      </div>
    )
  }

  if (!step) return null

  return (
    <div style={{ maxWidth: '640px', margin: '0 auto', padding: '20px 0' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '32px' }}>
        {ABS_STEPS.map((s, i) => (
          <div key={s.id} style={{ flex: 1 }}>
            <div style={{ height: '3px', borderRadius: '2px', backgroundColor: i <= currentStep ? 'var(--color-gold)' : 'rgba(255,255,255,0.06)', transition: 'background-color 0.3s' }} />
            <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-body)', color: i === currentStep ? 'var(--color-gold)' : 'var(--color-muted)', marginTop: '4px', display: 'block' }}>{s.title}</span>
          </div>
        ))}
      </div>

      <AnimatePresence mode="wait" custom={direction}>
        <motion.div key={step.id} custom={direction} initial={prefersReducedMotion ? {} : { opacity: 0, x: direction * 40 }} animate={{ opacity: 1, x: 0 }} exit={prefersReducedMotion ? {} : { opacity: 0, x: direction * -40 }} transition={{ duration: 0.3 }} className="glass" style={{ padding: '32px', borderRadius: 'var(--radius)' }}>
          <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.3rem', fontWeight: 600, color: 'var(--color-text)', marginBottom: '24px' }}>{step.question}</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {step.options.map((opt) => {
              const isRadio = step.type === 'radio'
              const isSelected = isRadio ? currentAnswer === opt : (Array.isArray(currentAnswer) && currentAnswer.includes(opt))
              return (
                <button key={opt} onClick={() => {
                  if (isRadio) setAnswers((a) => ({ ...a, [step.id]: opt }))
                  else {
                    const prev = Array.isArray(currentAnswer) ? currentAnswer : []
                    setAnswers((a) => ({ ...a, [step.id]: prev.includes(opt) ? prev.filter((x) => x !== opt) : [...prev, opt] }))
                  }
                }} style={{
                  display: 'flex', alignItems: 'center', gap: '12px', padding: '14px 18px', borderRadius: '10px',
                  textAlign: 'left', cursor: 'pointer', fontFamily: 'var(--font-body)', fontSize: '0.88rem',
                  backgroundColor: isSelected ? 'rgba(245, 158, 11, 0.1)' : 'rgba(30, 41, 59, 0.3)',
                  border: isSelected ? '1px solid rgba(245, 158, 11, 0.25)' : '1px solid rgba(255,255,255,0.06)',
                  color: isSelected ? 'var(--color-text)' : 'var(--color-muted)', transition: 'all 0.2s ease',
                }}>
                  <span style={{ width: '18px', height: '18px', borderRadius: isRadio ? '50%' : '4px', border: isSelected ? '2px solid var(--color-gold)' : '2px solid rgba(255,255,255,0.15)', backgroundColor: isSelected ? 'var(--color-gold)' : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    {isSelected && <span style={{ width: '8px', height: '8px', borderRadius: isRadio ? '50%' : '2px', backgroundColor: '#030712' }} />}
                  </span>
                  {opt}
                </button>
              )
            })}
          </div>
        </motion.div>
      </AnimatePresence>

      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '24px' }}>
        <button onClick={() => { setDirection(-1); setCurrentStep((s) => Math.max(0, s - 1)) }} disabled={currentStep === 0} style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '10px 20px', fontSize: '0.85rem', fontFamily: 'var(--font-body)', color: currentStep === 0 ? 'rgba(148,163,184,0.3)' : 'var(--color-muted)', backgroundColor: 'transparent', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '8px', cursor: currentStep === 0 ? 'not-allowed' : 'pointer' }}>
          <ArrowLeft size={15} /> Back
        </button>
        <button onClick={() => { if (isLastStep) void handleSubmit(); else { setDirection(1); setCurrentStep((s) => s + 1) } }} disabled={!hasAnswer || submitting} style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '10px 24px', fontSize: '0.85rem', fontFamily: 'var(--font-body)', fontWeight: 600, color: hasAnswer ? '#030712' : 'var(--color-muted)', backgroundColor: hasAnswer ? 'var(--color-gold)' : 'rgba(245,158,11,0.2)', border: 'none', borderRadius: '8px', cursor: hasAnswer && !submitting ? 'pointer' : 'not-allowed' }}>
          {submitting ? <><Loader2 size={15} style={{ animation: 'spin 1s linear infinite' }} /> Assessing...</>
            : isLastStep ? <>Assess ABS</>
            : <>Next <ArrowRight size={15} /></>
          }
        </button>
      </div>
    </div>
  )
}

function generateAbsResult(answers: Record<string, string | string[]>): AbsResult {
  const bioResources = answers.bio_resources as string
  if (bioResources === 'No biological resources') {
    return { relevance: 'NOT_APPLICABLE', summary: 'Your product does not appear to involve biological resources. ABS regulations may not apply.', next_steps: ['Confirm your product does not contain any biological material derived from Indian biodiversity', 'If ingredients change, re-run this assessment'] }
  }
  const origin = answers.origin as string
  const isIndian = origin?.includes('India')
  return {
    relevance: isIndian ? 'HIGH' : 'MEDIUM',
    summary: isIndian
      ? 'Your product uses biological resources from India. Compliance with the Biological Diversity Act 2002 (as amended 2023) is mandatory.'
      : 'Your product may involve international ABS obligations under the Nagoya Protocol / CBD.',
    next_steps: [
      'Apply for prior approval from the National Biodiversity Authority (NBA) via Form I',
      'Prepare a benefit-sharing agreement per Section 21 of the Biological Diversity Act',
      'Maintain chain-of-custody documentation for all biological materials',
      'If exporting, verify destination country ABS requirements (Nagoya Protocol compliance)',
      'Consult the State Biodiversity Board for local body requirements',
    ],
  }
}
