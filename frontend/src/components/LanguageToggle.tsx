import { useTranslation } from 'react-i18next'
import { Globe } from 'lucide-react'

export function LanguageToggle() {
  const { i18n } = useTranslation()
  const currentLang = i18n.language || 'en'

  const toggleLanguage = () => {
    const nextLang = currentLang.startsWith('hi') ? 'en' : 'hi'
    void i18n.changeLanguage(nextLang)
    localStorage.setItem('ipsakti_language', nextLang)
  }

  return (
    <button
      onClick={toggleLanguage}
      aria-label="Toggle language between English and Hindi"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        padding: '6px 12px',
        fontSize: '0.78rem',
        fontFamily: 'var(--font-body)',
        fontWeight: 600,
        color: 'var(--color-text)',
        backgroundColor: 'rgba(255, 255, 255, 0.04)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '8px',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = 'rgba(45, 212, 191, 0.3)'
        e.currentTarget.style.backgroundColor = 'rgba(45, 212, 191, 0.08)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)'
        e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.04)'
      }}
    >
      <Globe size={13} style={{ color: 'var(--color-teal)' }} />
      <span>{currentLang.startsWith('hi') ? 'हिन्दी' : 'English'}</span>
    </button>
  )
}
