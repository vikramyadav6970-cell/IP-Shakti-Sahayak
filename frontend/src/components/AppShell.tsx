import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import {
  MessageSquare,
  Layers,
  TreePalm,
  BookOpen,
  Shield,
  RotateCcw,
  LogIn,
  LogOut,
  User as UserIcon,
} from 'lucide-react'
import { useIntentStore } from '@/store'
import { useAuthStore } from '@/store/useAuthStore'
import { JurisdictionToggle } from '@/components/JurisdictionToggle'
import { LanguageToggle } from '@/components/LanguageToggle'
import { DisclaimerBanner } from '@/components/ui/DisclaimerBanner'

/**
 * Persistent app shell for all routes except the landing page.
 * Glassmorphism header, nav, disclaimer banner.
 */
export function AppShell() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const reset = useIntentStore((s) => s.reset)
  const { user, logout } = useAuthStore()

  const NAV_LINKS = [
    { to: '/chat', label: t('nav.chat', 'Chat'), icon: MessageSquare },
    { to: '/classify', label: t('nav.classify', 'Classify'), icon: Layers },
    { to: '/abs', label: t('nav.abs', 'ABS'), icon: TreePalm },
    { to: '/sources', label: t('nav.sources', 'Sources'), icon: BookOpen },
    { to: '/admin', label: t('nav.admin', 'Admin'), icon: Shield },
  ] as const

  const handleNewSession = () => {
    reset()
    navigate('/')
  }

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
      {/* Glassmorphism header */}
      <motion.header
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="glass"
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 40,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '12px 24px',
          borderTop: 'none',
          borderLeft: 'none',
          borderRight: 'none',
          borderRadius: 0,
        }}
      >
        {/* Left: logo + nav */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
          <button
            onClick={() => navigate('/')}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontFamily: 'var(--font-heading)',
              fontSize: '1.15rem',
              fontWeight: 600,
              color: 'var(--color-text)',
              letterSpacing: '-0.02em',
              padding: 0,
            }}
            aria-label="Go to home page"
          >
            IP-SAKTI{' '}
            <span style={{ color: 'var(--color-teal)', fontWeight: 700 }}>
              Sahayak
            </span>
          </button>

          <nav
            style={{ display: 'flex', alignItems: 'center', gap: '4px' }}
            aria-label="Main navigation"
          >
            {NAV_LINKS.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                style={({ isActive }) => ({
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 14px',
                  borderRadius: '8px',
                  fontSize: '0.82rem',
                  fontFamily: 'var(--font-body)',
                  fontWeight: 500,
                  textDecoration: 'none',
                  transition: 'all 0.2s ease',
                  color: isActive ? 'var(--color-teal)' : 'var(--color-muted)',
                  backgroundColor: isActive
                    ? 'rgba(45, 212, 191, 0.1)'
                    : 'transparent',
                })}
              >
                <Icon size={15} aria-hidden="true" />
                {label}
              </NavLink>
            ))}
          </nav>
        </div>

        {/* Right: language + jurisdiction + auth + new session */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <LanguageToggle />
          <JurisdictionToggle />

          {user ? (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '4px 10px',
                borderRadius: '8px',
                backgroundColor: 'rgba(255, 255, 255, 0.04)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
              }}
            >
              <UserIcon size={13} style={{ color: 'var(--color-teal)' }} />
              <span style={{ fontSize: '0.76rem', color: 'var(--color-text)', fontFamily: 'var(--font-body)' }}>
                {user.name || user.email}
              </span>
              <button
                onClick={() => logout()}
                title="Logout"
                style={{
                  background: 'none',
                  border: 'none',
                  padding: '2px',
                  cursor: 'pointer',
                  color: 'var(--color-muted)',
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                <LogOut size={12} />
              </button>
            </div>
          ) : (
            <button
              onClick={() => navigate('/login')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                padding: '6px 12px',
                fontSize: '0.78rem',
                fontFamily: 'var(--font-body)',
                fontWeight: 500,
                color: 'var(--color-text)',
                backgroundColor: 'rgba(255, 255, 255, 0.04)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '8px',
                cursor: 'pointer',
              }}
            >
              <LogIn size={13} style={{ color: 'var(--color-teal)' }} />
              {t('nav.login', 'Login')}
            </button>
          )}

          <button
            onClick={handleNewSession}
            aria-label="Start a new session"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              padding: '6px 14px',
              fontSize: '0.8rem',
              fontFamily: 'var(--font-body)',
              fontWeight: 500,
              color: 'var(--color-muted)',
              backgroundColor: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '8px',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = 'var(--color-text)'
              e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.15)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = 'var(--color-muted)'
              e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)'
            }}
          >
            <RotateCcw size={13} aria-hidden="true" />
            {t('nav.new_session', 'New Session')}
          </button>
        </div>
      </motion.header>

      {/* Page content */}
      <main
        style={{
          flex: 1,
          padding: '24px 32px',
          maxWidth: '1400px',
          margin: '0 auto',
          width: '100%',
        }}
      >
        <Outlet />
      </main>

      <DisclaimerBanner />
    </div>
  )
}
