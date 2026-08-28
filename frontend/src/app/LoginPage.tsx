import { useState } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { LogIn, Lock, Mail, Shield, User as UserIcon, ArrowRight } from 'lucide-react'
import { useAuthStore } from '@/store/useAuthStore'
import type { UserRole } from '@/types/auth'

export function LoginPage() {
  const navigate = useNavigate()
  const prefersReducedMotion = useReducedMotion()
  const { login } = useAuthStore()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [selectedRole, setSelectedRole] = useState<UserRole>('USER')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim() || !password.trim()) {
      setError('Please enter both email and password.')
      return
    }

    setIsLoading(true)
    setError(null)

    // Simulate login & hydrate user store
    setTimeout(() => {
      login(
        {
          id: `usr_${Date.now()}`,
          email: email.trim(),
          role: selectedRole,
          name: email.split('@')[0] || 'User',
        },
        'mock-jwt-token-xyz-123'
      )
      setIsLoading(false)
      navigate('/')
    }, 600)
  }

  const handleQuickDemo = (role: UserRole) => {
    login(
      {
        id: `demo_${role.toLowerCase()}`,
        email: `${role.toLowerCase()}@ipsakti.gov.in`,
        role: role,
        name: `Demo ${role.replace('_', ' ')}`,
      },
      'demo-jwt-token-456'
    )
    navigate(role === 'ADMIN' ? '/admin' : '/')
  }

  return (
    <div
      style={{
        position: 'relative',
        zIndex: 1,
        minHeight: '100dvh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px 16px',
      }}
    >
      <motion.div
        initial={prefersReducedMotion ? {} : { opacity: 0, y: 20, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="glass"
        style={{
          padding: '36px 32px',
          borderRadius: 'var(--radius)',
          maxWidth: '440px',
          width: '100%',
          boxShadow: '0 12px 40px rgba(0, 0, 0, 0.4)',
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, rgba(45, 212, 191, 0.2), rgba(139, 92, 246, 0.2))',
              border: '1px solid rgba(45, 212, 191, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 12px',
            }}
          >
            <LogIn size={22} style={{ color: 'var(--color-teal)' }} />
          </div>
          <h2
            style={{
              fontFamily: 'var(--font-heading)',
              fontSize: '1.45rem',
              fontWeight: 700,
              color: 'var(--color-text)',
              letterSpacing: '-0.02em',
              marginBottom: '6px',
            }}
          >
            Sign in to IP-SAKTI
          </h2>
          <p
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: '0.84rem',
              color: 'var(--color-muted)',
            }}
          >
            Access personalized patent analysis, ABS compliance, and session history.
          </p>
        </div>

        {error && (
          <div
            style={{
              padding: '10px 14px',
              backgroundColor: 'rgba(239, 68, 68, 0.12)',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              borderRadius: '8px',
              color: '#ef4444',
              fontSize: '0.8rem',
              fontFamily: 'var(--font-body)',
              marginBottom: '18px',
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label
              htmlFor="login-email"
              style={{
                display: 'block',
                fontFamily: 'var(--font-body)',
                fontSize: '0.8rem',
                fontWeight: 500,
                color: 'var(--color-muted)',
                marginBottom: '6px',
              }}
            >
              Email Address
            </label>
            <div style={{ position: 'relative' }}>
              <Mail
                size={16}
                style={{
                  position: 'absolute',
                  left: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--color-muted)',
                }}
              />
              <input
                id="login-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@organization.com"
                style={{
                  width: '100%',
                  padding: '10px 14px 10px 36px',
                  fontFamily: 'var(--font-body)',
                  fontSize: '0.88rem',
                  color: 'var(--color-text)',
                  backgroundColor: 'rgba(30, 41, 59, 0.6)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: '8px',
                  outline: 'none',
                }}
              />
            </div>
          </div>

          <div>
            <label
              htmlFor="login-password"
              style={{
                display: 'block',
                fontFamily: 'var(--font-body)',
                fontSize: '0.8rem',
                fontWeight: 500,
                color: 'var(--color-muted)',
                marginBottom: '6px',
              }}
            >
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <Lock
                size={16}
                style={{
                  position: 'absolute',
                  left: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--color-muted)',
                }}
              />
              <input
                id="login-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                style={{
                  width: '100%',
                  padding: '10px 14px 10px 36px',
                  fontFamily: 'var(--font-body)',
                  fontSize: '0.88rem',
                  color: 'var(--color-text)',
                  backgroundColor: 'rgba(30, 41, 59, 0.6)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: '8px',
                  outline: 'none',
                }}
              />
            </div>
          </div>

          <div>
            <label
              htmlFor="login-role"
              style={{
                display: 'block',
                fontFamily: 'var(--font-body)',
                fontSize: '0.8rem',
                fontWeight: 500,
                color: 'var(--color-muted)',
                marginBottom: '6px',
              }}
            >
              Demo Role Context
            </label>
            <select
              id="login-role"
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value as UserRole)}
              style={{
                width: '100%',
                padding: '10px 12px',
                fontFamily: 'var(--font-body)',
                fontSize: '0.85rem',
                color: 'var(--color-text)',
                backgroundColor: 'rgba(30, 41, 59, 0.6)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '8px',
                outline: 'none',
                cursor: 'pointer',
              }}
            >
              <option value="USER">Public User / Innovator</option>
              <option value="RESEARCHER">Ayurvedic Researcher / Academic</option>
              <option value="IP_FACILITATOR">IP Facilitator / Legal Expert</option>
              <option value="CONTENT_MANAGER">Corpus Content Manager</option>
              <option value="ADMIN">System Administrator</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            style={{
              marginTop: '8px',
              padding: '11px',
              fontFamily: 'var(--font-body)',
              fontSize: '0.9rem',
              fontWeight: 600,
              color: '#030712',
              backgroundColor: 'var(--color-teal)',
              border: 'none',
              borderRadius: '8px',
              cursor: isLoading ? 'wait' : 'pointer',
              transition: 'all 0.2s ease',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
            }}
          >
            {isLoading ? 'Signing in...' : 'Sign In'}
            <ArrowRight size={16} />
          </button>
        </form>

        <div style={{ margin: '24px 0', borderTop: '1px solid rgba(255, 255, 255, 0.06)' }} />

        {/* Quick demo presets */}
        <div>
          <p
            style={{
              fontSize: '0.74rem',
              color: 'var(--color-muted)',
              fontFamily: 'var(--font-body)',
              textAlign: 'center',
              marginBottom: '10px',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            1-Click Demo Login
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
            <button
              onClick={() => handleQuickDemo('USER')}
              style={{
                padding: '8px 10px',
                borderRadius: '6px',
                backgroundColor: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                color: 'var(--color-text)',
                fontSize: '0.76rem',
                fontFamily: 'var(--font-body)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                justifyContent: 'center',
              }}
            >
              <UserIcon size={13} style={{ color: 'var(--color-teal)' }} />
              Innovator
            </button>
            <button
              onClick={() => handleQuickDemo('ADMIN')}
              style={{
                padding: '8px 10px',
                borderRadius: '6px',
                backgroundColor: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                color: 'var(--color-text)',
                fontSize: '0.76rem',
                fontFamily: 'var(--font-body)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                justifyContent: 'center',
              }}
            >
              <Shield size={13} style={{ color: 'var(--color-gold)' }} />
              Admin
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
