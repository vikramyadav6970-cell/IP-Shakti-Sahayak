import { apiClient } from './apiClient'
import { logger } from '@/lib/logger'
import type { ChatRequest, ChatResponse } from '@/types'

/**
 * Send a chat query to the backend RAG pipeline.
 * Falls back to mock response if backend is unavailable.
 *
 * // TODO(contract): confirm request/response shape against backend/status.md once T3.1 is done.
 */
export async function sendChatQuery(request: ChatRequest): Promise<ChatResponse> {
  try {
    const response = await apiClient.post<ChatResponse>('/api/v1/chat', request)
    return response.data
  } catch {
    logger.info('Backend not available, using mock chat response')
    await new Promise((resolve) => setTimeout(resolve, 1500))
    return generateMockResponse(request)
  }
}

function generateMockResponse(request: ChatRequest): ChatResponse {
  return {
    answer: `## Analysis for ${request.domain_intent} Intent

Based on your query regarding **${request.domain_intent.toLowerCase()}** matters in Ayurvedic intellectual property:

### Key Findings

This is a **mock response** generated because the backend RAG pipeline is not yet connected. When operational, this section will contain:

1. **Citation-grounded legal analysis** — every claim traced to a specific section of Indian IP law or international treaty
2. **Jurisdiction-specific guidance** — India and International answers clearly separated
3. **Product classification** — whether your product falls under classical medicine, proprietary medicine, new drug, phytopharmaceutical, or Ayurveda-Aahara

### Relevant Legal Framework

- **Patents Act 1970, Section 3(p)** — inventions that are essentially traditional knowledge are not patentable
- **Biological Diversity Act 2002** (as amended 2023) — governs access and benefit sharing for biological resources
- **TKDL** — Traditional Knowledge Digital Library for prior art searches

### Next Steps

1. Complete the product classification wizard to determine your regulatory pathway
2. Review the source documents cited in your full analysis
3. Consider consulting a qualified IP professional for formal advice

> **Note:** This response is for demonstration purposes. The production system will provide real, evidence-backed analysis with full citations.`,
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
