"""TKDL Public-Information Pointer module.

Enforces context.md §2 Rule 5 & §5:
Provides a deterministic, code-controlled response template (not free LLM generation)
for TKDL-intent inquiries:
- States clearly that full TKDL access is restricted to International Patent Offices
  under bilateral Non-Disclosure Access Agreements.
- Surfaces only publicly available First Schedule classical texts (standards_formulations)
  and CSIR landmark revocation dossiers (case_law_prior_art).
- Directs users to the official CSIR-TKDL portal at https://www.tkdl.res.in.
"""

from dataclasses import dataclass, field
import logging
import re
from typing import Dict, List, Optional, Sequence

from src.reasoning.query_pipeline import Citation
from src.retrieval.hybrid_retriever import EvidenceChunk

logger = logging.getLogger(__name__)

OFFICIAL_TKDL_PORTAL = "https://www.tkdl.res.in"


@dataclass
class TKDLResponse:
    """Structured response for TKDL inquiries."""

    answer: str
    portal_url: str = OFFICIAL_TKDL_PORTAL
    citations: List[Citation] = field(default_factory=list)
    public_texts_surfaced: List[str] = field(default_factory=list)
    landmark_cases_surfaced: List[str] = field(default_factory=list)


def generate_tkdl_response(
    question: str,
    evidence_chunks: Sequence[EvidenceChunk],
    language: str = "en",
) -> TKDLResponse:
    """Generate fixed, code-controlled guidance for TKDL-related inquiries."""
    is_hindi = language.lower().startswith("hi")

    citations: List[Citation] = []
    public_texts: List[str] = []
    landmark_cases: List[str] = []

    # Extract verified public evidence chunks
    for c in evidence_chunks:
        title = c.payload.get("act") or c.payload.get("source") or c.payload.get("case_name") or c.document_id
        if c.corpus_collection in ("standards_formulations", "legal_statutory"):
            if title not in public_texts:
                public_texts.append(title)
        elif c.corpus_collection == "case_law_prior_art":
            if title not in landmark_cases:
                landmark_cases.append(title)

        citations.append(
            Citation(
                chunk_id=c.chunk_id,
                document_id=c.document_id,
                collection=c.corpus_collection,
                jurisdiction=c.jurisdiction,
                title=title,
                section_or_ref=str(c.payload.get("section") or c.payload.get("citation_ref") or ""),
                snippet=c.text[:250],
            )
        )

    # Attach verified citation tags to evidence mentions
    evidence_bullets: List[str] = []
    for c in evidence_chunks[:4]:
        tag = f"[{c.chunk_id}]"
        ref_name = c.payload.get("source") or c.payload.get("act") or c.payload.get("case_name") or c.document_id
        evidence_bullets.append(f"- **{ref_name}** {tag}: {c.text.strip()[:200]}...")

    evidence_text = "\n".join(evidence_bullets) if evidence_bullets else "- No public formulation dossiers matched the specific query."

    if is_hindi:
        template = f"""### 🏛️ पारम्परिक ज्ञान डिजिटल लाइब्रेरी (CSIR-TKDL) सूचना मार्गदर्शन

**महत्वपूर्ण विधिक सूचना**: 
पारम्परिक ज्ञान डिजिटल लाइब्रेरी (TKDL) एक स्वामित्व डेटाबेस है जो सीएसआईआर (CSIR) और आयुष मंत्रालय द्वारा प्रबंधित किया जाता है। टीकेडीएल डेटाबेस तक पूर्ण प्रत्यक्ष पहुंच केवल अंतर्राष्ट्रीय पेटेंट कार्यालयों (जैसे USPTO, EPO, JPO, UKIPO) को द्विपक्षीय **गैर-प्रकटीकरण पहुंच समझौतों (Non-Disclosure Access Agreements)** के तहत प्रदान की जाती है।

---

#### 📖 उपलब्ध सार्वजनिक साक्ष्य एवं संदर्भ
हमारा सिस्टम सार्वजनिक रूप से उपलब्ध प्रथम अनुसूची के शास्त्रीय ग्रंथों (चरक संहिता, सुश्रुत संहिता, एपीआई) और सीएसआईआर के पूर्व पेटेंट निरस्तीकरण दस्तावेजों से जानकारी प्रस्तुत करता है:

{evidence_text}

---

#### ⚖️ ऐतिहासिक पूर्व कला निरस्तीकरण मामले (Landmark Revocation Cases)
- **हल्दी (Turmeric - US Patent 5,401,504)**: सीएसआईआर ने घाव भरने के पारंपरिक उपयोग के आधार पर पेटेंट रद्द कराया।
- **नीम (Neem - EP 0436257)**: ईपीओ ने कवकनाशी पेटेंट को पूर्व कला के आधार पर पूर्णतः निरस्त किया।
- **अश्वगंधा (Ashwagandha Pre-grant Opposition)**: भावप्रकाश निघंटु के आधार पर तीसरे पक्ष की आपत्तियों द्वारा पेटेंट रोका गया।

---

#### 🌐 आधिकारिक पोर्टल एवं अनुसंधान पहुंच
अनुसंधानकर्ताओं, शैक्षणिक संस्थानों और उद्योग के लिए आधिकारिक सीएसआईआर दिशा-निर्देशों के तहत सीमित पहुंच उपलब्ध है:
🔗 **आधिकारिक पोर्टल**: [CSIR-TKDL Portal](https://www.tkdl.res.in)"""
    else:
        template = f"""### Traditional Knowledge Digital Library (CSIR-TKDL) Information Guidance

> **Statutory Notice on TKDL Access Policy**:
> The Traditional Knowledge Digital Library (TKDL) is a proprietary repository created by the Council of Scientific and Industrial Research (CSIR) and the Ministry of AYUSH. **Full direct database access is strictly restricted to International Patent Offices** (e.g., USPTO, EPO, JPO, UKIPO) under bilateral **Non-Disclosure Access Agreements** to prevent wrongful patenting of traditional Indian knowledge.

---

#### Publicly Surfaced Evidence & Classical Treatises
Our platform surfaces verified prior art from publicly accessible First-Schedule classical Ayurvedic treatises (Charaka Samhita, Sushruta Samhita, API) and public CSIR opposition dossiers:

{evidence_text}

---

#### Landmark CSIR Prior Art Revocation Precedents
1. **Turmeric (Curcuma longa - US Patent 5,401,504)**: Successfully revoked by CSIR in 1997 citing ancient Sanskrit and Hindi texts establishing prior art for wound healing.
2. **Neem (Azadirachta indica - EP 0436257 B1)**: EPO Technical Board of Appeal completely revoked the fungicidal patent on grounds of lack of novelty and traditional prior art.
3. **Ashwagandha (Withania somnifera Pre-Grant Opposition)**: Third-party observations under EPC Article 115 citing Bhavaprakasha Nighantu.

---

#### Official Portal & Institutional Access
For research access, academic collaborations, or user agreements under the expanded CSIR framework, please visit the official government portal:
🔗 **Official CSIR-TKDL Portal**: [CSIR-TKDL Portal](https://www.tkdl.res.in)"""

    return TKDLResponse(
        answer=template.strip(),
        portal_url=OFFICIAL_TKDL_PORTAL,
        citations=citations,
        public_texts_surfaced=public_texts,
        landmark_cases_surfaced=landmark_cases,
    )
