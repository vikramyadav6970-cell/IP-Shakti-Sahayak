import { useState, useMemo } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { Search, ExternalLink, Filter } from 'lucide-react'
import type { QdrantCollection } from '@/types'

interface SourceDocument {
  id: string
  title: string
  collection: QdrantCollection
  jurisdiction: string
  document_type: string
  issuing_authority: string
  version_date: string
  source_url: string
}

const COLLECTION_META: Record<QdrantCollection, { label: string; color: string }> = {
  legal_statutory:       { label: 'Statutes', color: '#2dd4bf' },
  standards_formulations: { label: 'Formulations', color: '#f59e0b' },
  case_law_prior_art:    { label: 'Case Law', color: '#fbbf24' },
  procedural_forms:      { label: 'Forms', color: '#8b5cf6' },
  international_export:  { label: 'International', color: '#60a5fa' },
}

/** Mock corpus documents */
const MOCK_SOURCES: SourceDocument[] = [
  { id: '1', title: 'The Patents Act, 1970', collection: 'legal_statutory', jurisdiction: 'India', document_type: 'Act', issuing_authority: 'Parliament of India', version_date: '2023-04-01', source_url: 'https://indiacode.nic.in' },
  { id: '2', title: 'The Trade Marks Act, 1999', collection: 'legal_statutory', jurisdiction: 'India', document_type: 'Act', issuing_authority: 'Parliament of India', version_date: '2022-12-01', source_url: 'https://indiacode.nic.in' },
  { id: '3', title: 'Biological Diversity Act, 2002', collection: 'legal_statutory', jurisdiction: 'India', document_type: 'Act', issuing_authority: 'Ministry of Environment', version_date: '2023-08-01', source_url: 'https://nbaindia.org' },
  { id: '4', title: 'Geographical Indications of Goods Act, 1999', collection: 'legal_statutory', jurisdiction: 'India', document_type: 'Act', issuing_authority: 'Parliament of India', version_date: '2023-01-01', source_url: 'https://indiacode.nic.in' },
  { id: '5', title: 'Drugs and Cosmetics Act, 1940', collection: 'legal_statutory', jurisdiction: 'India', document_type: 'Act', issuing_authority: 'Ministry of Health', version_date: '2024-01-01', source_url: 'https://indiacode.nic.in' },
  { id: '6', title: 'Ayurvedic Pharmacopoeia of India (API) Vol. I–IX', collection: 'standards_formulations', jurisdiction: 'India', document_type: 'Pharmacopoeia', issuing_authority: 'Ministry of AYUSH', version_date: '2022-06-01', source_url: 'https://www.ayush.gov.in' },
  { id: '7', title: 'Ayurvedic Formulary of India (AFI) Part I–II', collection: 'standards_formulations', jurisdiction: 'India', document_type: 'Formulary', issuing_authority: 'Ministry of AYUSH', version_date: '2021-03-01', source_url: 'https://www.ayush.gov.in' },
  { id: '8', title: 'FSSAI Ayurveda-Aahara Regulations', collection: 'standards_formulations', jurisdiction: 'India', document_type: 'Regulation', issuing_authority: 'FSSAI', version_date: '2024-06-01', source_url: 'https://fssai.gov.in' },
  { id: '9', title: 'NBA Application Form — Form I (ABS Access)', collection: 'procedural_forms', jurisdiction: 'India', document_type: 'Form', issuing_authority: 'National Biodiversity Authority', version_date: '2024-01-01', source_url: 'https://nbaindia.org' },
  { id: '10', title: 'TRIPS Agreement (WTO)', collection: 'international_export', jurisdiction: 'International', document_type: 'Treaty', issuing_authority: 'WTO', version_date: '1995-01-01', source_url: 'https://www.wto.org' },
  { id: '11', title: 'Convention on Biological Diversity (CBD)', collection: 'international_export', jurisdiction: 'International', document_type: 'Treaty', issuing_authority: 'UNEP', version_date: '1993-12-29', source_url: 'https://www.cbd.int' },
  { id: '12', title: 'Nagoya Protocol on ABS', collection: 'international_export', jurisdiction: 'International', document_type: 'Protocol', issuing_authority: 'CBD Secretariat', version_date: '2014-10-12', source_url: 'https://www.cbd.int/abs' },
  { id: '13', title: 'WIPO GRATK Treaty (2024)', collection: 'international_export', jurisdiction: 'International', document_type: 'Treaty', issuing_authority: 'WIPO', version_date: '2024-05-24', source_url: 'https://www.wipo.int' },
]

export function SourcesPage() {
  const prefersReducedMotion = useReducedMotion()
  const [search, setSearch] = useState('')
  const [filterJurisdiction, setFilterJurisdiction] = useState<string>('all')
  const [filterCollection, setFilterCollection] = useState<string>('all')
  const [filterType, setFilterType] = useState<string>('all')

  const filtered = useMemo(() => {
    return MOCK_SOURCES.filter((doc) => {
      if (search && !doc.title.toLowerCase().includes(search.toLowerCase())) return false
      if (filterJurisdiction !== 'all' && doc.jurisdiction !== filterJurisdiction) return false
      if (filterCollection !== 'all' && doc.collection !== filterCollection) return false
      if (filterType !== 'all' && doc.document_type !== filterType) return false
      return true
    })
  }, [search, filterJurisdiction, filterCollection, filterType])

  const jurisdictions = [...new Set(MOCK_SOURCES.map((d) => d.jurisdiction))]
  const docTypes = [...new Set(MOCK_SOURCES.map((d) => d.document_type))]

  const selectStyle = {
    padding: '8px 12px', fontSize: '0.78rem', fontFamily: 'var(--font-body)',
    backgroundColor: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: '8px', color: 'var(--color-text)', cursor: 'pointer', outline: 'none',
  } as const

  return (
    <div>
      <motion.div initial={prefersReducedMotion ? {} : { opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: '24px' }}>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.5rem', fontWeight: 700, color: 'var(--color-text)', marginBottom: '8px' }}>Source Explorer</h2>
        <p style={{ fontFamily: 'var(--font-body)', fontSize: '0.9rem', color: 'var(--color-muted)' }}>
          Browse the corpus of {MOCK_SOURCES.length} authoritative documents used for retrieval.
        </p>
      </motion.div>

      {/* Filters */}
      <div className="glass" style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '12px', padding: '14px 18px', borderRadius: 'var(--radius)', marginBottom: '20px' }}>
        <Filter size={16} style={{ color: 'var(--color-muted)' }} />
        <div style={{ flex: 1, minWidth: '200px', position: 'relative' }}>
          <Search size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--color-muted)' }} />
          <input
            type="text" value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Search documents..."
            style={{ ...selectStyle, width: '100%', paddingLeft: '32px' }}
          />
        </div>
        <select value={filterJurisdiction} onChange={(e) => setFilterJurisdiction(e.target.value)} style={selectStyle} aria-label="Filter by jurisdiction">
          <option value="all">All jurisdictions</option>
          {jurisdictions.map((j) => <option key={j} value={j}>{j}</option>)}
        </select>
        <select value={filterCollection} onChange={(e) => setFilterCollection(e.target.value)} style={selectStyle} aria-label="Filter by collection">
          <option value="all">All collections</option>
          {(Object.entries(COLLECTION_META) as [QdrantCollection, { label: string }][]).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
        </select>
        <select value={filterType} onChange={(e) => setFilterType(e.target.value)} style={selectStyle} aria-label="Filter by type">
          <option value="all">All types</option>
          {docTypes.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>

      {/* Results */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '14px' }}>
        {filtered.map((doc, i) => {
          const col = COLLECTION_META[doc.collection]
          return (
            <motion.div
              key={doc.id}
              initial={prefersReducedMotion ? {} : { opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
              className="glass glass-hover"
              style={{ padding: '20px', borderRadius: 'var(--radius)', cursor: 'default' }}
            >
              <div style={{ display: 'flex', gap: '6px', marginBottom: '10px', flexWrap: 'wrap' }}>
                <span style={{ padding: '2px 8px', fontSize: '0.68rem', fontFamily: 'var(--font-body)', fontWeight: 600, borderRadius: '4px', backgroundColor: `${col.color}15`, color: col.color }}>{col.label}</span>
                <span style={{ padding: '2px 8px', fontSize: '0.68rem', fontFamily: 'var(--font-body)', borderRadius: '4px', backgroundColor: 'rgba(255,255,255,0.05)', color: 'var(--color-muted)' }}>{doc.jurisdiction}</span>
                <span style={{ padding: '2px 8px', fontSize: '0.68rem', fontFamily: 'var(--font-body)', borderRadius: '4px', backgroundColor: 'rgba(255,255,255,0.05)', color: 'var(--color-muted)' }}>{doc.document_type}</span>
              </div>
              <h4 style={{ fontFamily: 'var(--font-heading)', fontSize: '0.9rem', fontWeight: 600, color: 'var(--color-text)', marginBottom: '6px', lineHeight: 1.3 }}>{doc.title}</h4>
              <p style={{ fontSize: '0.75rem', color: 'var(--color-muted)', fontFamily: 'var(--font-body)', marginBottom: '10px' }}>
                {doc.issuing_authority} · Updated {doc.version_date}
              </p>
              <a href={doc.source_url} target="_blank" rel="noopener noreferrer" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: 'var(--color-teal)', fontFamily: 'var(--font-body)', textDecoration: 'none' }}>
                <ExternalLink size={12} /> View source
              </a>
            </motion.div>
          )
        })}
      </div>

      {filtered.length === 0 && (
        <div className="glass" style={{ padding: '48px', borderRadius: 'var(--radius)', textAlign: 'center' }}>
          <p style={{ fontSize: '0.9rem', color: 'var(--color-muted)', fontFamily: 'var(--font-body)' }}>No documents match your filters.</p>
        </div>
      )}
    </div>
  )
}
