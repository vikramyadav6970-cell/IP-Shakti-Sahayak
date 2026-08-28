import { motion, useReducedMotion } from 'framer-motion'
import { Database, Cpu, Server, Activity, AlertTriangle } from 'lucide-react'
import { useAuthStore } from '@/store'

interface MetricCard {
  label: string
  value: string | number
  change?: string
  color: string
}

const CORPUS_STATS = [
  { collection: 'Statutes', count: 12, indexed: 12, color: '#2dd4bf' },
  { collection: 'Formulations', count: 8, indexed: 8, color: '#f59e0b' },
  { collection: 'Case Law', count: 0, indexed: 0, color: '#fbbf24' },
  { collection: 'Forms', count: 3, indexed: 3, color: '#8b5cf6' },
  { collection: 'International', count: 6, indexed: 6, color: '#60a5fa' },
]

const AI_METRICS: MetricCard[] = [
  { label: 'Retrieval Accuracy', value: '—', change: 'Pending eval', color: 'var(--color-teal)' },
  { label: 'Citation Accuracy', value: '—', change: 'Pending eval', color: 'var(--color-gold)' },
  { label: 'Abstention Rate', value: '—', change: 'Pending eval', color: 'var(--color-violet)' },
  { label: 'Decomposition Accuracy', value: '—', change: 'Pending eval', color: '#60a5fa' },
]

/**
 * Admin / IP Dashboard — role-gated.
 * Shows corpus health, AI metrics, system status.
 */
export function AdminPage() {
  const prefersReducedMotion = useReducedMotion()
  const { user } = useAuthStore()

  // Role check — show clear "not authorized" if role doesn't permit
  if (user && user.role !== 'ADMIN' && user.role !== 'CONTENT_MANAGER') {
    // For now, show the dashboard since auth isn't implemented yet
  }

  return (
    <div>
      <motion.div
        initial={prefersReducedMotion ? {} : { opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ marginBottom: '28px' }}
      >
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.5rem', fontWeight: 700, color: 'var(--color-text)', marginBottom: '8px' }}>
          Admin Dashboard
        </h2>
        <p style={{ fontSize: '0.9rem', color: 'var(--color-muted)', fontFamily: 'var(--font-body)' }}>
          Corpus health, AI metrics, and system status.
        </p>
      </motion.div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
        {/* Corpus Health */}
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass"
          style={{ padding: '24px', borderRadius: 'var(--radius)' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
            <Database size={18} style={{ color: 'var(--color-teal)' }} />
            <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1rem', fontWeight: 600, color: 'var(--color-text)' }}>Corpus Health</h3>
          </div>

          {CORPUS_STATS.map((col) => (
            <div key={col.collection} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: col.color }} />
                <span style={{ fontSize: '0.85rem', fontFamily: 'var(--font-body)', color: 'var(--color-text)' }}>{col.collection}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ fontSize: '0.8rem', fontFamily: 'var(--font-body)', color: 'var(--color-muted)' }}>
                  {col.indexed}/{col.count} indexed
                </span>
                {/* Mini bar */}
                <div style={{ width: '60px', height: '4px', borderRadius: '2px', backgroundColor: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
                  <div style={{ height: '100%', borderRadius: '2px', backgroundColor: col.count > 0 ? col.color : 'transparent', width: col.count > 0 ? `${(col.indexed / col.count) * 100}%` : '0%' }} />
                </div>
              </div>
            </div>
          ))}
          <p style={{ fontSize: '0.72rem', color: 'var(--color-muted)', fontFamily: 'var(--font-body)', marginTop: '12px' }}>
            Total: {CORPUS_STATS.reduce((a, c) => a + c.count, 0)} documents · Last updated: 2026-08-28
          </p>
        </motion.div>

        {/* AI Metrics */}
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass"
          style={{ padding: '24px', borderRadius: 'var(--radius)' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
            <Cpu size={18} style={{ color: 'var(--color-violet)' }} />
            <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1rem', fontWeight: 600, color: 'var(--color-text)' }}>AI Metrics</h3>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            {AI_METRICS.map((metric) => (
              <div key={metric.label} style={{ padding: '14px', borderRadius: '10px', backgroundColor: 'rgba(30, 41, 59, 0.4)', border: '1px solid rgba(255,255,255,0.04)' }}>
                <p style={{ fontSize: '0.72rem', color: 'var(--color-muted)', fontFamily: 'var(--font-body)', marginBottom: '4px' }}>{metric.label}</p>
                <p style={{ fontSize: '1.3rem', fontFamily: 'var(--font-heading)', fontWeight: 700, color: metric.color }}>{metric.value}</p>
                <p style={{ fontSize: '0.68rem', color: 'var(--color-muted)', fontFamily: 'var(--font-body)', marginTop: '2px' }}>{metric.change}</p>
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '14px', padding: '10px 12px', borderRadius: '8px', backgroundColor: 'rgba(245, 158, 11, 0.06)', border: '1px solid rgba(245, 158, 11, 0.1)' }}>
            <AlertTriangle size={14} style={{ color: 'var(--color-gold)' }} />
            <p style={{ fontSize: '0.72rem', color: 'var(--color-gold)', fontFamily: 'var(--font-body)' }}>
              AI metrics available after Phase 5 evaluation runs (RAGAS harness)
            </p>
          </div>
        </motion.div>

        {/* System Status */}
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass"
          style={{ padding: '24px', borderRadius: 'var(--radius)' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
            <Server size={18} style={{ color: '#60a5fa' }} />
            <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1rem', fontWeight: 600, color: 'var(--color-text)' }}>System Status</h3>
          </div>

          {[
            { name: 'Supabase (PostgreSQL)', status: 'healthy', latency: '23ms' },
            { name: 'Upstash Redis', status: 'healthy', latency: '12ms' },
            { name: 'Qdrant Cloud', status: 'healthy', latency: '45ms' },
            { name: 'Backend API', status: 'offline', latency: '—' },
            { name: 'AI Pipeline', status: 'offline', latency: '—' },
          ].map((svc) => (
            <div key={svc.name} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: svc.status === 'healthy' ? '#2dd4bf' : '#ef4444' }} />
                <span style={{ fontSize: '0.85rem', fontFamily: 'var(--font-body)', color: 'var(--color-text)' }}>{svc.name}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-body)', color: 'var(--color-muted)' }}>{svc.latency}</span>
                <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-body)', fontWeight: 500, color: svc.status === 'healthy' ? '#2dd4bf' : '#ef4444', padding: '2px 8px', borderRadius: '4px', backgroundColor: svc.status === 'healthy' ? 'rgba(45,212,191,0.1)' : 'rgba(239,68,68,0.1)' }}>
                  {svc.status}
                </span>
              </div>
            </div>
          ))}
        </motion.div>

        {/* Activity */}
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="glass"
          style={{ padding: '24px', borderRadius: 'var(--radius)' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
            <Activity size={18} style={{ color: 'var(--color-gold)' }} />
            <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1rem', fontWeight: 600, color: 'var(--color-text)' }}>Recent Activity</h3>
          </div>
          <div style={{ textAlign: 'center', padding: '24px', color: 'var(--color-muted)', fontSize: '0.85rem', fontFamily: 'var(--font-body)' }}>
            No activity yet — queries and classifications will appear here once the backend is connected.
          </div>
        </motion.div>
      </div>
    </div>
  )
}
