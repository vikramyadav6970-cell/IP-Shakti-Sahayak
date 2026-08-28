import type { QdrantCollection, ConfidenceLabel, Citation } from '@/types'
import { motion } from 'framer-motion'

/* ──────────────────────────────────────────────────────────────
   CitationCard — renders one citation with collection + jurisdiction badges
   See context.md §2 rules 1, 3: every claim must trace to a source.
   ────────────────────────────────────────────────────────────── */

const COLLECTION_COLORS: Record<QdrantCollection, { bg: string; text: string; label: string }> = {
  legal_statutory:       { bg: 'rgba(45, 212, 191, 0.12)', text: '#2dd4bf', label: 'Statutes' },
  standards_formulations: { bg: 'rgba(245, 158, 11, 0.12)', text: '#f59e0b', label: 'Formulations' },
  case_law_prior_art:    { bg: 'rgba(251, 191, 36, 0.12)', text: '#fbbf24', label: 'Case Law' },
  procedural_forms:      { bg: 'rgba(139, 92, 246, 0.12)',  text: '#8b5cf6', label: 'Forms' },
  international_export:  { bg: 'rgba(96, 165, 250, 0.12)',  text: '#60a5fa', label: 'International' },
}

interface CitationCardProps {
  citation: Citation
  index: number
}

export function CitationCard({ citation, index }: CitationCardProps) {
  const collectionStyle = COLLECTION_COLORS[citation.collection]

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
      style={{
        padding: '16px',
        borderRadius: '10px',
        backgroundColor: 'rgba(15, 23, 42, 0.5)',
        border: '1px solid rgba(255, 255, 255, 0.06)',
        marginBottom: '8px',
      }}
    >
      {/* Badges row */}
      <div style={{ display: 'flex', gap: '6px', marginBottom: '10px', flexWrap: 'wrap' }}>
        {/* Collection badge */}
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            padding: '2px 8px',
            fontSize: '0.7rem',
            fontFamily: 'var(--font-body)',
            fontWeight: 600,
            borderRadius: '4px',
            backgroundColor: collectionStyle.bg,
            color: collectionStyle.text,
          }}
        >
          {collectionStyle.label}
        </span>
        {/* Jurisdiction badge */}
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            padding: '2px 8px',
            fontSize: '0.7rem',
            fontFamily: 'var(--font-body)',
            fontWeight: 500,
            borderRadius: '4px',
            backgroundColor: 'rgba(255, 255, 255, 0.06)',
            color: 'var(--color-muted)',
          }}
        >
          {citation.jurisdiction}
        </span>
      </div>

      {/* Title + section */}
      <h4
        style={{
          fontFamily: 'var(--font-heading)',
          fontSize: '0.85rem',
          fontWeight: 600,
          color: 'var(--color-text)',
          marginBottom: '4px',
        }}
      >
        {citation.document_title}
      </h4>
      <p
        style={{
          fontSize: '0.75rem',
          color: 'var(--color-teal)',
          fontFamily: 'var(--font-body)',
          fontWeight: 500,
          marginBottom: '8px',
        }}
      >
        {citation.section_reference}
      </p>

      {/* Excerpt */}
      <p
        style={{
          fontSize: '0.78rem',
          color: 'var(--color-muted)',
          fontFamily: 'var(--font-body)',
          lineHeight: 1.5,
          fontStyle: 'italic',
          borderLeft: `2px solid ${collectionStyle.text}`,
          paddingLeft: '10px',
          marginBottom: '10px',
        }}
      >
        "{citation.excerpt}"
      </p>

      {/* Footer */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '0.7rem', color: 'var(--color-muted)', fontFamily: 'var(--font-body)' }}>
          {citation.source_authority}
        </span>
        {citation.source_url && (
          <a
            href={citation.source_url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontSize: '0.7rem',
              color: 'var(--color-teal)',
              fontFamily: 'var(--font-body)',
              textDecoration: 'none',
            }}
          >
            Open source →
          </a>
        )}
      </div>
    </motion.div>
  )
}

/** Shown when answer has zero citations */
export function NoCitationsCard() {
  return (
    <div
      style={{
        padding: '20px',
        borderRadius: '10px',
        backgroundColor: 'rgba(245, 158, 11, 0.08)',
        border: '1px solid rgba(245, 158, 11, 0.15)',
        textAlign: 'center',
      }}
    >
      <p style={{ fontSize: '0.85rem', color: 'var(--color-gold)', fontFamily: 'var(--font-body)', fontWeight: 500 }}>
        No authoritative source found
      </p>
      <p style={{ fontSize: '0.75rem', color: 'var(--color-muted)', fontFamily: 'var(--font-body)', marginTop: '4px' }}>
        This answer could not be grounded in a specific source document. Consider consulting an IP professional.
      </p>
    </div>
  )
}

/* ──────────────────────────────────────────────────────────────
   ConfidenceBadge — color-coded chip + text label
   Never rely on color alone — text label always visible (rule 7).
   ────────────────────────────────────────────────────────────── */

const CONFIDENCE_STYLES: Record<ConfidenceLabel, { bg: string; text: string; border: string }> = {
  HIGH:   { bg: 'rgba(45, 212, 191, 0.12)', text: '#2dd4bf', border: 'rgba(45, 212, 191, 0.2)' },
  MEDIUM: { bg: 'rgba(245, 158, 11, 0.12)', text: '#f59e0b', border: 'rgba(245, 158, 11, 0.2)' },
  LOW:    { bg: 'rgba(239, 68, 68, 0.12)',  text: '#ef4444', border: 'rgba(239, 68, 68, 0.2)' },
}

interface ConfidenceBadgeProps {
  confidence: number
  label: ConfidenceLabel
  requiresHumanReview: boolean
  onEscalate?: () => void
}

export function ConfidenceBadge({ confidence, label, requiresHumanReview, onEscalate }: ConfidenceBadgeProps) {
  const style = CONFIDENCE_STYLES[label]
  const pct = Math.round(confidence * 100)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 12px',
            fontSize: '0.75rem',
            fontFamily: 'var(--font-body)',
            fontWeight: 600,
            borderRadius: '6px',
            backgroundColor: style.bg,
            color: style.text,
            border: `1px solid ${style.border}`,
          }}
        >
          <span
            style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              backgroundColor: style.text,
            }}
            aria-hidden="true"
          />
          {label} Confidence
        </span>
        <span style={{ fontSize: '0.7rem', color: 'var(--color-muted)', fontFamily: 'var(--font-body)' }}>
          {pct}%
        </span>
      </div>

      {(label === 'LOW' || requiresHumanReview) && (
        <button
          onClick={onEscalate}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 16px',
            fontSize: '0.78rem',
            fontFamily: 'var(--font-body)',
            fontWeight: 500,
            color: 'var(--color-gold)',
            backgroundColor: 'rgba(245, 158, 11, 0.08)',
            border: '1px solid rgba(245, 158, 11, 0.15)',
            borderRadius: '8px',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            width: 'fit-content',
          }}
        >
          ⚠ Human IP facilitator review recommended
        </button>
      )}
    </div>
  )
}
