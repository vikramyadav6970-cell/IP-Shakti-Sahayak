import { useState, useCallback } from 'react'
import { motion, useReducedMotion, AnimatePresence, type Variants } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  Briefcase,
  Ship,
  Pill,
  FileSearch,
  FlaskConical,
  HelpCircle,
} from 'lucide-react'
import { useIntentStore } from '@/store'
import { JurisdictionToggle } from '@/components/JurisdictionToggle'
import { LanguageToggle } from '@/components/LanguageToggle'
import { DisclaimerBanner } from '@/components/ui/DisclaimerBanner'
import type { DomainIntent } from '@/types'

interface IntentCardData {
  intent: DomainIntent
  title: string
  description: string
  icon: React.ComponentType<{ size?: number; className?: string }>
  gradient: string
  glowColor: string
}

const INTENT_CARDS: IntentCardData[] = [
  {
    intent: 'BUSINESS',
    title: 'Business',
    description:
      'Trademark, GI, copyright & design protection for your Ayurvedic brand and products.',
    icon: Briefcase,
    gradient: 'linear-gradient(135deg, rgba(45, 212, 191, 0.12), rgba(45, 212, 191, 0.03))',
    glowColor: 'rgba(45, 212, 191, 0.25)',
  },
  {
    intent: 'EXPORT',
    title: 'Export',
    description:
      'Navigate NBA approvals, CITES, and destination-country regulations for herbal exports.',
    icon: Ship,
    gradient: 'linear-gradient(135deg, rgba(245, 158, 11, 0.12), rgba(245, 158, 11, 0.03))',
    glowColor: 'rgba(245, 158, 11, 0.25)',
  },
  {
    intent: 'MEDICINAL',
    title: 'Medicinal',
    description:
      'Drug & food regulatory classification — classical, proprietary, new drug, or Ayurveda-Aahara.',
    icon: Pill,
    gradient: 'linear-gradient(135deg, rgba(139, 92, 246, 0.12), rgba(139, 92, 246, 0.03))',
    glowColor: 'rgba(139, 92, 246, 0.25)',
  },
  {
    intent: 'PATENT',
    title: 'Patent',
    description:
      'Section 3(p) analysis, TKDL prior art, and patent strategy for novel formulations.',
    icon: FileSearch,
    gradient: 'linear-gradient(135deg, rgba(45, 212, 191, 0.12), rgba(139, 92, 246, 0.03))',
    glowColor: 'rgba(45, 212, 191, 0.25)',
  },
  {
    intent: 'RESEARCH',
    title: 'Research',
    description:
      'ABS compliance, biological resource access, and IP for clinical or academic research.',
    icon: FlaskConical,
    gradient: 'linear-gradient(135deg, rgba(245, 158, 11, 0.12), rgba(139, 92, 246, 0.03))',
    glowColor: 'rgba(245, 158, 11, 0.25)',
  },
  {
    intent: 'OTHER',
    title: 'Other',
    description:
      'Describe your query freely — the AI will determine the best guidance pathway.',
    icon: HelpCircle,
    gradient: 'linear-gradient(135deg, rgba(148, 163, 184, 0.12), rgba(148, 163, 184, 0.03))',
    glowColor: 'rgba(148, 163, 184, 0.25)',
  },
]

const cardVariants: Variants = {
  hidden: { opacity: 0, y: 40, scale: 0.95 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      delay: 0.1 + i * 0.08,
      duration: 0.5,
      ease: [0.21, 0.47, 0.32, 0.98] as [number, number, number, number],
    },
  }),
  exit: {
    opacity: 0,
    scale: 0.9,
    transition: { duration: 0.3 },
  },
}

const containerVariants = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.08,
    },
  },
}

export function IntentSelectionPage() {
  const navigate = useNavigate()
  const prefersReducedMotion = useReducedMotion()
  const { t } = useTranslation()
  const { setDomainIntent } = useIntentStore()

  const [showOtherInput, setShowOtherInput] = useState(false)
  const [otherDescription, setOtherDescription] = useState('')
  const [selectedCard, setSelectedCard] = useState<DomainIntent | null>(null)

  const handleIntentSelect = useCallback(
    (intent: DomainIntent) => {
      if (intent === 'OTHER') {
        setShowOtherInput(true)
        return
      }

      setSelectedCard(intent)
      setDomainIntent(intent)

      // Brief delay for selection animation, then navigate
      setTimeout(() => {
        navigate('/context')
      }, 400)
    },
    [navigate, setDomainIntent]
  )

  const handleOtherSubmit = useCallback(() => {
    if (!otherDescription.trim()) return
    setDomainIntent('OTHER')
    useIntentStore.setState({
      context_object: {
        domain_intent: 'OTHER',
        answers: {},
        free_description: otherDescription.trim(),
      },
    })
    navigate('/chat')
  }, [otherDescription, navigate, setDomainIntent])

  return (
    <div
      style={{
        position: 'relative',
        zIndex: 1,
        minHeight: '100dvh',
        display: 'flex',
        flexDirection: 'column',
        paddingBottom: '40px', // space for disclaimer
      }}
    >
      {/* Header */}
      <header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '20px 32px',
        }}
      >
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h1
            style={{
              fontFamily: 'var(--font-heading)',
              fontSize: 'clamp(1.1rem, 2vw, 1.4rem)',
              fontWeight: 600,
              color: 'var(--color-text)',
              letterSpacing: '-0.02em',
            }}
          >
            IP-SAKTI{' '}
            <span style={{ color: 'var(--color-teal)', fontWeight: 700 }}>
              Sahayak
            </span>
          </h1>
        </motion.div>
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          style={{ display: 'flex', alignItems: 'center', gap: '10px' }}
        >
          <LanguageToggle />
          <JurisdictionToggle />
        </motion.div>
      </header>

      {/* Main content */}
      <main
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '0 32px',
          maxWidth: '1200px',
          margin: '0 auto',
          width: '100%',
        }}
      >
        {/* Tagline */}
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.1 }}
          style={{ textAlign: 'center', marginBottom: '48px' }}
        >
          <h2
            style={{
              fontFamily: 'var(--font-heading)',
              fontSize: 'clamp(1.8rem, 4vw, 2.8rem)',
              fontWeight: 700,
              color: 'var(--color-text)',
              letterSpacing: '-0.03em',
              lineHeight: 1.15,
              marginBottom: '12px',
            }}
          >
            {t('landing.heading', 'What do you need help with?')}
          </h2>
          <p
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: 'clamp(0.9rem, 1.5vw, 1.1rem)',
              color: 'var(--color-muted)',
              maxWidth: '600px',
              margin: '0 auto',
            }}
          >
            {t(
              'landing.description',
              'Select a domain to get AI-powered, citation-grounded IP & regulatory guidance for Ayurvedic products.'
            )}
          </p>
        </motion.div>

        {/* Intent cards grid */}
        <motion.div
          variants={prefersReducedMotion ? {} : containerVariants}
          initial="hidden"
          animate="visible"
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '20px',
            width: '100%',
            maxWidth: '1000px',
          }}
        >
          {INTENT_CARDS.map((card, i) => (
            <IntentCard
              key={card.intent}
              data={card}
              index={i}
              isSelected={selectedCard === card.intent}
              onSelect={handleIntentSelect}
              prefersReducedMotion={!!prefersReducedMotion}
            />
          ))}
        </motion.div>

        {/* "Other" inline textarea */}
        <AnimatePresence>
          {showOtherInput && (
            <motion.div
              initial={{ opacity: 0, y: 20, height: 0 }}
              animate={{ opacity: 1, y: 0, height: 'auto' }}
              exit={{ opacity: 0, y: 20, height: 0 }}
              transition={{ duration: 0.3 }}
              style={{
                marginTop: '24px',
                width: '100%',
                maxWidth: '600px',
              }}
            >
              <div
                className="glass"
                style={{
                  padding: '24px',
                  borderRadius: 'var(--radius)',
                }}
              >
                <label
                  htmlFor="other-description"
                  style={{
                    display: 'block',
                    fontFamily: 'var(--font-heading)',
                    fontSize: '1rem',
                    fontWeight: 600,
                    color: 'var(--color-text)',
                    marginBottom: '12px',
                  }}
                >
                  Describe your query
                </label>
                <textarea
                  id="other-description"
                  value={otherDescription}
                  onChange={(e) => setOtherDescription(e.target.value)}
                  placeholder="e.g., I'm developing a turmeric-based skincare cream and want to know about trademark and export regulations..."
                  rows={4}
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    fontFamily: 'var(--font-body)',
                    fontSize: '0.9rem',
                    color: 'var(--color-text)',
                    backgroundColor: 'rgba(30, 41, 59, 0.5)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: '8px',
                    resize: 'vertical',
                    outline: 'none',
                    lineHeight: 1.6,
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = 'rgba(45, 212, 191, 0.3)'
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = 'rgba(255, 255, 255, 0.08)'
                  }}
                />
                <div
                  style={{
                    display: 'flex',
                    gap: '12px',
                    marginTop: '16px',
                    justifyContent: 'flex-end',
                  }}
                >
                  <button
                    onClick={() => setShowOtherInput(false)}
                    style={{
                      padding: '8px 20px',
                      fontFamily: 'var(--font-body)',
                      fontSize: '0.85rem',
                      fontWeight: 500,
                      color: 'var(--color-muted)',
                      backgroundColor: 'transparent',
                      border: '1px solid rgba(255, 255, 255, 0.08)',
                      borderRadius: '8px',
                      cursor: 'pointer',
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleOtherSubmit}
                    disabled={!otherDescription.trim()}
                    style={{
                      padding: '8px 24px',
                      fontFamily: 'var(--font-body)',
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      color: '#030712',
                      backgroundColor: otherDescription.trim()
                        ? 'var(--color-teal)'
                        : 'rgba(45, 212, 191, 0.3)',
                      border: 'none',
                      borderRadius: '8px',
                      cursor: otherDescription.trim()
                        ? 'pointer'
                        : 'not-allowed',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    Get guidance →
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <DisclaimerBanner />
    </div>
  )
}

/* ──────────────────────────────────────────────────────────────
   IntentCard component
   ────────────────────────────────────────────────────────────── */

interface IntentCardProps {
  data: IntentCardData
  index: number
  isSelected: boolean
  onSelect: (intent: DomainIntent) => void
  prefersReducedMotion: boolean
}

function IntentCard({
  data,
  index,
  isSelected,
  onSelect,
  prefersReducedMotion,
}: IntentCardProps) {
  const Icon = data.icon

  return (
    <motion.button
      custom={index}
      variants={prefersReducedMotion ? undefined : cardVariants}
      initial={prefersReducedMotion ? {} : 'hidden'}
      animate={isSelected ? { scale: 1.05, opacity: 0.7 } : 'visible'}
      whileHover={
        prefersReducedMotion
          ? {}
          : {
              scale: 1.03,
              transition: { type: 'spring', stiffness: 400, damping: 25 },
            }
      }
      whileTap={prefersReducedMotion ? {} : { scale: 0.98 }}
      onClick={() => onSelect(data.intent)}
      aria-label={`Select ${data.title} — ${data.description}`}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
        padding: '28px 24px',
        borderRadius: 'var(--radius)',
        cursor: 'pointer',
        textAlign: 'left',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        background: data.gradient,
        backdropFilter: 'blur(24px)',
        WebkitBackdropFilter: 'blur(24px)',
        boxShadow: isSelected
          ? `0 0 0 1px var(--color-teal), 0 0 30px ${data.glowColor}, 0 8px 32px rgba(0,0,0,0.4)`
          : '0 8px 32px rgba(0, 0, 0, 0.4)',
        transition: 'box-shadow 0.3s ease, border-color 0.3s ease',
        fontFamily: 'var(--font-body)',
        width: '100%',
      }}
      onMouseEnter={(e) => {
        const el = e.currentTarget
        el.style.borderColor = 'rgba(45, 212, 191, 0.3)'
        el.style.boxShadow = `0 0 0 1px var(--color-teal), 0 0 20px ${data.glowColor}, 0 8px 32px rgba(0,0,0,0.4)`
      }}
      onMouseLeave={(e) => {
        const el = e.currentTarget
        if (!isSelected) {
          el.style.borderColor = 'rgba(255, 255, 255, 0.08)'
          el.style.boxShadow = '0 8px 32px rgba(0, 0, 0, 0.4)'
        }
      }}
    >
      {/* Icon */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '44px',
          height: '44px',
          borderRadius: '12px',
          backgroundColor: 'rgba(255, 255, 255, 0.05)',
          border: '1px solid rgba(255, 255, 255, 0.06)',
          marginBottom: '16px',
        }}
      >
        <span style={{ color: 'var(--color-teal)', display: 'flex' }}>
          <Icon size={22} />
        </span>
      </div>

      {/* Title */}
      <h3
        style={{
          fontFamily: 'var(--font-heading)',
          fontSize: '1.15rem',
          fontWeight: 600,
          color: 'var(--color-text)',
          marginBottom: '8px',
          letterSpacing: '-0.01em',
        }}
      >
        {data.title}
      </h3>

      {/* Description */}
      <p
        style={{
          fontFamily: 'var(--font-body)',
          fontSize: '0.85rem',
          color: 'var(--color-muted)',
          lineHeight: 1.5,
        }}
      >
        {data.description}
      </p>
    </motion.button>
  )
}
