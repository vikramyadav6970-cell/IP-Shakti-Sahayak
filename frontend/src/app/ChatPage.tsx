import { useEffect, useState, useCallback, useRef } from 'react'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { Send, Loader2, Menu, X } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useIntentStore, useJurisdictionStore } from '@/store'
import { sendChatQuery } from '@/services/chatService'
import { CitationCard, NoCitationsCard, ConfidenceBadge } from '@/components/citations/CitationCard'
import type { ChatMessage, ChatResponse, QdrantCollection } from '@/types'

const COLLECTION_LABELS: Record<QdrantCollection, string> = {
  legal_statutory: 'Statutes',
  standards_formulations: 'Formulations',
  case_law_prior_art: 'Case Law',
  procedural_forms: 'Forms',
  international_export: 'International',
}

const COLLECTION_COLORS: Record<QdrantCollection, string> = {
  legal_statutory: '#2dd4bf',
  standards_formulations: '#f59e0b',
  case_law_prior_art: '#fbbf24',
  procedural_forms: '#8b5cf6',
  international_export: '#60a5fa',
}

/**
 * Chat / answer screen — two-panel layout.
 * Left: Evidence Map. Right: Conversation.
 * See context.md §2 for hard constraints on jurisdiction separation and disclaimers.
 */
export function ChatPage() {
  const prefersReducedMotion = useReducedMotion()
  const { domain_intent, context_object, session_id } = useIntentStore()
  const { mode: jurisdiction } = useJurisdictionStore()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [latestResponse, setLatestResponse] = useState<ChatResponse | null>(null)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [showSidebar, setShowSidebar] = useState(false)
  const [showEscalation, setShowEscalation] = useState(false)

  // Auto-submit on mount if coming from /context
  useEffect(() => {
    if (domain_intent && context_object && messages.length === 0) {
      const summary = buildContextSummary()
      const userMsg: ChatMessage = {
        id: `msg-${Date.now()}`,
        role: 'user',
        content: summary,
        timestamp: new Date(),
      }
      setMessages([userMsg])
      void submitQuery(summary)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  function buildContextSummary(): string {
    if (!domain_intent) return ''
    if (context_object?.free_description) return context_object.free_description
    let summary = `**${domain_intent}** guidance request\n\n`
    if (context_object?.answers) {
      for (const [key, val] of Object.entries(context_object.answers)) {
        const label = key.replace(/_/g, ' ').replace(/^(biz|exp|med|pat|res)\s/, '')
        summary += `- **${label}**: ${Array.isArray(val) ? val.join(', ') : val}\n`
      }
    }
    return summary
  }

  const submitQuery = useCallback(async (question: string) => {
    setLoading(true)
    try {
      const response = await sendChatQuery({
        question,
        domain_intent: domain_intent ?? 'OTHER',
        session_id: session_id,
        jurisdiction: jurisdiction,
        language: 'en',
        conversation_id: conversationId,
      })
      setLatestResponse(response)
      // Track conversation_id for follow-up messages
      if (response.conversation_id) {
        setConversationId(response.conversation_id)
      }
      const assistantMsg: ChatMessage = {
        id: `msg-${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        citations: response.citations,
        confidence: response.confidence,
        confidence_label: response.confidence_label,
        requires_human_review: response.requires_human_review,
        sub_tasks_run: response.sub_tasks_run,
        sources_by_collection: response.sources_by_collection,
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch {
      const errorMsg: ChatMessage = {
        id: `msg-${Date.now()}`,
        role: 'assistant',
        content: 'An error occurred while processing your query. Please try again.',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMsg])
    }
    setLoading(false)
  }, [domain_intent, session_id, jurisdiction, conversationId])

  const handleSend = useCallback(() => {
    if (!input.trim() || loading) return
    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMsg])
    const question = input.trim()
    setInput('')
    void submitQuery(question)
  }, [input, loading, submitQuery])

  return (
    <div style={{ display: 'flex', gap: '20px', minHeight: 'calc(100vh - 160px)' }}>
      {/* Mobile sidebar toggle */}
      <button
        onClick={() => setShowSidebar(!showSidebar)}
        aria-label="Toggle evidence map"
        style={{
          display: 'none',
          position: 'fixed',
          bottom: '56px',
          right: '16px',
          zIndex: 30,
          width: '44px',
          height: '44px',
          borderRadius: '12px',
          backgroundColor: 'var(--color-surface)',
          border: '1px solid rgba(255,255,255,0.08)',
          color: 'var(--color-teal)',
          cursor: 'pointer',
          alignItems: 'center',
          justifyContent: 'center',
        }}
        className="mobile-sidebar-toggle"
      >
        {showSidebar ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* LEFT PANEL — Evidence Map */}
      <aside
        className="glass"
        style={{
          width: '280px',
          minWidth: '280px',
          borderRadius: 'var(--radius)',
          padding: '20px',
          alignSelf: 'flex-start',
          position: 'sticky',
          top: '80px',
          display: showSidebar ? 'block' : undefined,
        }}
      >
        <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '0.9rem', fontWeight: 600, color: 'var(--color-text)', marginBottom: '16px' }}>
          Evidence Map
        </h3>

        {/* Collection nodes */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '20px' }}>
          {(Object.entries(COLLECTION_LABELS) as [QdrantCollection, string][]).map(([key, label]) => {
            const isActive = latestResponse?.sources_by_collection?.[key] && latestResponse.sources_by_collection[key] > 0
            const count = latestResponse?.sources_by_collection?.[key] ?? 0
            return (
              <motion.div
                key={key}
                animate={isActive ? { opacity: 1 } : { opacity: 0.4 }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '8px 12px',
                  borderRadius: '8px',
                  backgroundColor: isActive ? `${COLLECTION_COLORS[key]}10` : 'rgba(255,255,255,0.02)',
                  border: `1px solid ${isActive ? `${COLLECTION_COLORS[key]}25` : 'rgba(255,255,255,0.04)'}`,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <motion.span
                    animate={isActive && !prefersReducedMotion ? {
                      boxShadow: [`0 0 4px ${COLLECTION_COLORS[key]}`, `0 0 12px ${COLLECTION_COLORS[key]}`, `0 0 4px ${COLLECTION_COLORS[key]}`],
                    } : {}}
                    transition={{ duration: 2, repeat: Infinity }}
                    style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      backgroundColor: isActive ? COLLECTION_COLORS[key] : 'var(--color-muted)',
                    }}
                  />
                  <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-body)', color: isActive ? 'var(--color-text)' : 'var(--color-muted)' }}>
                    {label}
                  </span>
                </div>
                {isActive && (
                  <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-body)', color: COLLECTION_COLORS[key], fontWeight: 600 }}>
                    {count}
                  </span>
                )}
              </motion.div>
            )
          })}
        </div>

        {/* Sub-tasks badges */}
        {latestResponse?.sub_tasks_run && latestResponse.sub_tasks_run.length > 0 && (
          <div>
            <p style={{ fontSize: '0.72rem', color: 'var(--color-muted)', fontFamily: 'var(--font-body)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Sub-tasks run
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
              {latestResponse.sub_tasks_run.map((task) => (
                <span
                  key={task}
                  style={{
                    padding: '3px 8px',
                    fontSize: '0.68rem',
                    fontFamily: 'var(--font-body)',
                    borderRadius: '4px',
                    backgroundColor: 'rgba(30, 41, 59, 0.8)',
                    color: 'var(--color-muted)',
                    border: '1px solid rgba(255,255,255,0.06)',
                  }}
                >
                  {task.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Confidence */}
        {latestResponse && (
          <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
            <ConfidenceBadge
              confidence={latestResponse.confidence}
              label={latestResponse.confidence_label}
              requiresHumanReview={latestResponse.requires_human_review}
              onEscalate={() => setShowEscalation(true)}
            />
          </div>
        )}
      </aside>

      {/* RIGHT PANEL — Conversation */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* Messages */}
        <div style={{ flex: 1, overflowY: 'auto', paddingBottom: '20px' }}>
          <AnimatePresence mode="sync">
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={prefersReducedMotion ? {} : { opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                style={{
                  marginBottom: '16px',
                  display: 'flex',
                  justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                }}
              >
                <div
                  className={msg.role === 'assistant' ? 'glass' : ''}
                  style={{
                    maxWidth: msg.role === 'user' ? '70%' : '100%',
                    padding: msg.role === 'user' ? '12px 18px' : '24px',
                    borderRadius: 'var(--radius)',
                    backgroundColor: msg.role === 'user' ? 'rgba(45, 212, 191, 0.1)' : undefined,
                    border: msg.role === 'user' ? '1px solid rgba(45, 212, 191, 0.15)' : undefined,
                  }}
                >
                  {/* Role label */}
                  <p style={{
                    fontSize: '0.7rem',
                    fontFamily: 'var(--font-body)',
                    fontWeight: 600,
                    color: msg.role === 'user' ? 'var(--color-teal)' : 'var(--color-violet)',
                    marginBottom: '8px',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                  }}>
                    {msg.role === 'user' ? 'You' : 'IP-SAKTI Sahayak'}
                  </p>

                  {/* Content */}
                  <div
                    style={{
                      fontSize: '0.88rem',
                      fontFamily: 'var(--font-body)',
                      color: 'var(--color-text)',
                      lineHeight: 1.7,
                    }}
                    className="prose-content"
                  >
                    {msg.role === 'assistant' ? (
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>
                    ) : (
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>
                    )}
                  </div>

                  {/* Citations */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                      <p style={{ fontSize: '0.75rem', fontFamily: 'var(--font-body)', fontWeight: 600, color: 'var(--color-muted)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        Sources ({msg.citations.length})
                      </p>
                      {msg.citations.map((c, i) => (
                        <CitationCard key={c.id} citation={c} index={i} />
                      ))}
                    </div>
                  )}
                  {msg.role === 'assistant' && msg.citations && msg.citations.length === 0 && (
                    <div style={{ marginTop: '16px' }}>
                      <NoCitationsCard />
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Loading skeleton */}
          {loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="glass"
              style={{ padding: '24px', borderRadius: 'var(--radius)', marginBottom: '16px' }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                <Loader2 size={16} style={{ color: 'var(--color-violet)', animation: 'spin 1s linear infinite' }} />
                <span style={{ fontSize: '0.78rem', color: 'var(--color-violet)', fontFamily: 'var(--font-body)' }}>
                  Searching across collections and synthesizing answer...
                </span>
              </div>
              {[1, 2, 3].map((n) => (
                <div
                  key={n}
                  style={{
                    height: '12px',
                    borderRadius: '4px',
                    backgroundColor: 'rgba(255,255,255,0.04)',
                    marginBottom: '8px',
                    width: `${100 - n * 15}%`,
                    animation: 'pulse 1.5s ease-in-out infinite',
                  }}
                />
              ))}
              <style>{`@keyframes pulse { 0%,100% { opacity: 0.4; } 50% { opacity: 0.8; } }`}</style>
            </motion.div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input box */}
        <div
          className="glass"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '12px 16px',
            borderRadius: 'var(--radius)',
            position: 'sticky',
            bottom: '44px',
          }}
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') handleSend() }}
            placeholder="Ask a follow-up question..."
            disabled={loading}
            style={{
              flex: 1,
              padding: '10px 14px',
              fontSize: '0.88rem',
              fontFamily: 'var(--font-body)',
              color: 'var(--color-text)',
              backgroundColor: 'rgba(30, 41, 59, 0.5)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '8px',
              outline: 'none',
            }}
            onFocus={(e) => { e.target.style.borderColor = 'rgba(45, 212, 191, 0.3)' }}
            onBlur={(e) => { e.target.style.borderColor = 'rgba(255, 255, 255, 0.08)' }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            aria-label="Send message"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              border: 'none',
              backgroundColor: input.trim() && !loading ? 'var(--color-teal)' : 'rgba(45, 212, 191, 0.2)',
              color: input.trim() && !loading ? '#030712' : 'var(--color-muted)',
              cursor: input.trim() && !loading ? 'pointer' : 'not-allowed',
              transition: 'all 0.2s ease',
            }}
          >
            <Send size={18} />
          </button>
        </div>
      </div>

      {/* Escalation dialog — placeholder for T4.3 */}
      <AnimatePresence>
        {showEscalation && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowEscalation(false)}
            style={{
              position: 'fixed',
              inset: 0,
              zIndex: 100,
              backgroundColor: 'rgba(0,0,0,0.6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="glass"
              style={{ padding: '32px', borderRadius: 'var(--radius)', maxWidth: '480px', width: '90%' }}
            >
              <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.1rem', fontWeight: 600, color: 'var(--color-text)', marginBottom: '12px' }}>
                Request Expert Review
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--color-muted)', fontFamily: 'var(--font-body)', marginBottom: '16px' }}>
                This query has been flagged for human IP facilitator review due to low confidence. Add any additional context:
              </p>
              <textarea
                rows={3}
                placeholder="Additional context..."
                style={{
                  width: '100%', padding: '10px 14px', fontSize: '0.85rem', fontFamily: 'var(--font-body)',
                  color: 'var(--color-text)', backgroundColor: 'rgba(30, 41, 59, 0.5)',
                  border: '1px solid rgba(255,255,255,0.08)', borderRadius: '8px', outline: 'none', resize: 'vertical',
                }}
              />
              <div style={{ display: 'flex', gap: '10px', marginTop: '16px', justifyContent: 'flex-end' }}>
                <button onClick={() => setShowEscalation(false)} style={{ padding: '8px 16px', fontSize: '0.8rem', fontFamily: 'var(--font-body)', color: 'var(--color-muted)', backgroundColor: 'transparent', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '8px', cursor: 'pointer' }}>Cancel</button>
                <button onClick={() => setShowEscalation(false)} style={{ padding: '8px 20px', fontSize: '0.8rem', fontFamily: 'var(--font-body)', fontWeight: 600, color: '#030712', backgroundColor: 'var(--color-gold)', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>Submit for review</button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
