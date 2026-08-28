import { motion, AnimatePresence } from 'framer-motion'
import { Globe, MapPin } from 'lucide-react'
import { useJurisdictionStore } from '@/store'
import type { InternationalCountry } from '@/types'

const INTERNATIONAL_COUNTRIES: { value: InternationalCountry; label: string }[] = [
  { value: 'USA', label: 'United States' },
  { value: 'EU', label: 'European Union' },
  { value: 'UK', label: 'United Kingdom' },
  { value: 'JAPAN', label: 'Japan' },
  { value: 'AUSTRALIA', label: 'Australia' },
  { value: 'CANADA', label: 'Canada' },
  { value: 'UAE', label: 'UAE' },
  { value: 'WHO', label: 'WHO/International' },
  { value: 'WIPO', label: 'WIPO' },
]

/**
 * Pill-style jurisdiction toggle: India (teal) / International (gold).
 * Wired to useJurisdictionStore with localStorage persistence.
 */
export function JurisdictionToggle() {
  const { mode, internationalCountry, setMode, setInternationalCountry } =
    useJurisdictionStore()

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      {/* Pill toggle */}
      <div
        style={{
          display: 'flex',
          borderRadius: '999px',
          overflow: 'hidden',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          backgroundColor: 'rgba(15, 23, 42, 0.6)',
          backdropFilter: 'blur(12px)',
        }}
      >
        <button
          onClick={() => setMode('INDIA')}
          aria-pressed={mode === 'INDIA'}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            padding: '6px 14px',
            fontSize: '0.8rem',
            fontFamily: 'var(--font-body)',
            fontWeight: 500,
            border: 'none',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            backgroundColor:
              mode === 'INDIA' ? 'rgba(45, 212, 191, 0.15)' : 'transparent',
            color: mode === 'INDIA' ? '#2dd4bf' : 'var(--color-muted)',
          }}
        >
          <MapPin size={14} aria-hidden="true" />
          India
        </button>
        <button
          onClick={() => setMode('INTERNATIONAL')}
          aria-pressed={mode === 'INTERNATIONAL'}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            padding: '6px 14px',
            fontSize: '0.8rem',
            fontFamily: 'var(--font-body)',
            fontWeight: 500,
            border: 'none',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            backgroundColor:
              mode === 'INTERNATIONAL'
                ? 'rgba(245, 158, 11, 0.15)'
                : 'transparent',
            color:
              mode === 'INTERNATIONAL' ? '#f59e0b' : 'var(--color-muted)',
          }}
        >
          <Globe size={14} aria-hidden="true" />
          International
        </button>
      </div>

      {/* Country selector — only visible when International is active */}
      <AnimatePresence>
        {mode === 'INTERNATIONAL' && (
          <motion.select
            initial={{ opacity: 0, width: 0 }}
            animate={{ opacity: 1, width: 'auto' }}
            exit={{ opacity: 0, width: 0 }}
            transition={{ duration: 0.2 }}
            value={internationalCountry}
            onChange={(e) =>
              setInternationalCountry(e.target.value as InternationalCountry)
            }
            aria-label="Select international jurisdiction"
            style={{
              padding: '6px 10px',
              fontSize: '0.75rem',
              fontFamily: 'var(--font-body)',
              backgroundColor: 'rgba(15, 23, 42, 0.6)',
              backdropFilter: 'blur(12px)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '8px',
              color: 'var(--color-gold)',
              cursor: 'pointer',
              outline: 'none',
            }}
          >
            {INTERNATIONAL_COUNTRIES.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </motion.select>
        )}
      </AnimatePresence>
    </div>
  )
}
