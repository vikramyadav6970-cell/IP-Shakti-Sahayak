import { useTranslation } from 'react-i18next'

/**
 * Non-dismissible disclaimer banner.
 * Hard requirement from context.md §2 rule 4:
 * "Information, not legal advice" shown with every substantive answer.
 */
export function DisclaimerBanner() {
  const { t } = useTranslation()

  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 50,
        height: '40px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '0 16px',
        textAlign: 'center',
        backgroundColor: 'rgba(45, 212, 191, 0.08)',
        borderTop: '1px solid rgba(45, 212, 191, 0.15)',
        fontFamily: 'var(--font-body)',
        fontSize: '0.75rem',
        color: 'var(--color-teal)',
        letterSpacing: '0.02em',
        userSelect: 'none',
      }}
    >
      <svg
        width="14"
        height="14"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        style={{ marginRight: '6px', opacity: 0.7, flexShrink: 0 }}
        aria-hidden="true"
      >
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="16" x2="12" y2="12" />
        <line x1="12" y1="8" x2="12.01" y2="8" />
      </svg>
      {t(
        'app.disclaimer',
        'Information provided is for educational and guidance purposes only and does not constitute formal legal advice.'
      )}
    </div>
  )
}
