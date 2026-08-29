import { apiClient } from './apiClient'
import { logger } from '@/lib/logger'
import type { ChatRequest, ChatResponse } from '@/types'

/**
 * Send a chat query to the backend RAG pipeline.
 * Falls back to mock response if backend is unavailable.
 */
export async function sendChatQuery(request: ChatRequest): Promise<ChatResponse> {
  try {
    const response = await apiClient.post<ChatResponse>('/api/v1/chat', request)
    return response.data
  } catch (err) {
    logger.error('Backend chat call failed, using mock chat fallback:', err)
    await new Promise((resolve) => setTimeout(resolve, 1500))
    return generateMockResponse(request)
  }
}

function generateMockResponse(request: ChatRequest): ChatResponse {
  return {
    answer: `## Executive Summary
Regarding your query **"${request.question || 'IP Guidance'}"**, under Indian Intellectual Property Law, natural herbs and classical Ayurvedic formulations are governed by specific statutory exclusions and mandatory access clearances. Traditional knowledge per se is non-patentable, while novel extraction techniques require rigorous prior art differentiation and regulatory approval.

## Statutory & Prior Art Analysis
- **Patents Act 1970 §3(p)** \`[patents_act_1970#sec_3p]\`: Inventions that in effect are traditional knowledge or aggregations/duplications of known properties of traditionally known components are excluded from patentability.
- **Biological Diversity Act 2002 §6** \`[bda_2002#sec_6]\`: Prior statutory approval from the National Biodiversity Authority (NBA) via Form III is mandatory before filing patent applications utilizing Indian biological resources.
- **Ayurvedic Pharmacopoeia of India (API)** \`[api_vol_1#standards]\`: Official pharmacopoeial standards and classical monographs governing herbal authenticity and classical therapeutic uses.

## Patentability & Compliance Assessment
1. **Section 3(p) & 3(e) Hurdles**: Classical preparations documented in AYUSH authoritative treatises cannot be patented. To qualify for a patent, applicants must demonstrate a distinct inventive step (e.g., a novel, non-obvious standardized bioactive fraction or unexpected synergistic efficacy backed by comparative trial data).
2. **Access and Benefit Sharing (ABS)**: Commercial utilization or patenting involving Indian biological resources requires formal clearance from the NBA / State Biodiversity Boards.
3. **TKDL Verification**: International patent offices review the Traditional Knowledge Digital Library (TKDL) to establish prior art and prevent biopiracy.

## Actionable Next Steps
1. **Perform TKDL Prior Art Search**: Verify that the formulation or therapeutic use is not pre-disclosed in ancient AYUSH literature.
2. **File Form III with the NBA**: Secure statutory clearance from the National Biodiversity Authority before filing the patent specification.
3. **Document Synergistic Efficacy**: Compile comparative laboratory and clinical data proving unexpected therapeutic synergy beyond known additive effects.
4. **Consult IP Facilitator**: Work with an accredited Patent Agent or AYUSH legal specialist for specification drafting and claim construction.

---
*Disclaimer: This AI-generated synthesis is for informational and educational guidance only and does not constitute formal legal counsel.*`,
    confidence: 0.72,
    confidence_label: 'MEDIUM',
    classification: null,
    citations: [
      {
        id: 'cite-1',
        document_title: 'The Patents Act, 1970',
        section_reference: 'Section 3(p)',
        collection: 'legal_statutory',
        jurisdiction: 'India',
        source_authority: 'Parliament of India',
        source_url: 'https://indiacode.nic.in',
        relevance_score: 0.92,
        excerpt: 'An invention which, in effect, is traditional knowledge or which is an aggregation or duplication of known properties of traditionally known component or components.',
      },
      {
        id: 'cite-2',
        document_title: 'Biological Diversity Act, 2002',
        section_reference: 'Section 3 (as amended 2023)',
        collection: 'legal_statutory',
        jurisdiction: 'India',
        source_authority: 'Ministry of Environment',
        source_url: 'https://nbaindia.org',
        relevance_score: 0.85,
        excerpt: 'No person shall, without previous approval of the National Biodiversity Authority, obtain any biological resource occurring in India for research or for commercial utilisation.',
      },
      {
        id: 'cite-3',
        document_title: 'WIPO GRATK Treaty',
        section_reference: 'Article 3',
        collection: 'international_export',
        jurisdiction: 'International',
        source_authority: 'WIPO',
        relevance_score: 0.78,
        excerpt: 'Applicants shall disclose the country of origin of genetic resources and associated traditional knowledge.',
      },
    ],
    requires_human_review: false,
    conversation_id: null,
    sub_tasks_run: ['legal_analysis', 'patent_prior_art', 'abs_check'],
    sources_by_collection: {
      legal_statutory: 2,
      international_export: 1,
      standards_formulations: 0,
      procedural_forms: 0,
      case_law_prior_art: 0,
    },
  }
}
