# ai/status.md

Granular status log + the authoritative record of interfaces/function signatures
the backend calls into (e.g. the ingestion task signature, the query pipeline
entrypoint). Populate as you go — don't make backend guess your function shapes.

---

## Interfaces backend depends on

*(none finalized yet — populate as they're built, e.g.:)*
```
@celery_app.task(name="ai.tasks.ingest_document")
def ingest_document(version_id: str):
    # Retrieve DocumentVersion from Supabase, fetch raw file from Storage using `storage_key`,
    # chunk and embed into Qdrant collection based on `corpus_collection`,
    # and update DocumentVersion.ingestion_status in Postgres.
    pass

# Mocked (Backend T3.1) — wait for AI Phase 3 for exact implementation details
# This runs synchronously in the FastAPI service layer (not celery)
def query_pipeline(
    question: str, 
    domain_intent: str, 
    jurisdiction: str, 
    language: str, 
    context_object: dict | None, 
    entity_set: dict | None
) -> dict:
    """
    Returns:
    {
      "answer": str,
      "confidence": float,
      "confidence_label": str,
      "classification": str,
      "requires_human_review": bool,
      "citations": [
        {
          "document_title": str,
          "corpus_collection": str,
          "jurisdiction": str,
          "document_type": str,
          "section_ref": str,
          "source_url": str
        }
      ]
    }
    """
    pass
```

---

## Corpus manifest

**Seed dataset added** (see `ai/data/corpus/seed/README.md` for full detail and
verification-tier explanation): 11 real records across `legal_knowledge.jsonl`
(6), `ipr_prior_art.jsonl` (3 \u2014 the turmeric/neem/basmati TK-prior-art cases),
`ayush_tk.jsonl` (2), plus a `load_seed.py` embedding/insertion script and an
8-question grounded eval set at `ai/tests/eval/questions_seed.jsonl`. `case_law`
deliberately left empty (see `case_law_STUB.md` \u2014 no verified real Indian court
judgment on point was found; do not fill with a fabricated one).
**This is a proof-of-pipeline seed, not the full T1.1 corpus** \u2014 T1.1 (20-50
document curation) is still open.

*(track the full T1.1 corpus here as it's built, or in
data/corpus/manifest.md linked from here)*

---

## Log

### (seed dataset added \u2014 no other work done yet)
Added `ai/data/corpus/seed/` (verified legal_knowledge, ipr_prior_art, ayush_tk
records + loader script) and `ai/tests/eval/questions_seed.jsonl` in response to
a request to build an embeddable dataset. Every record carries a
`verification_status` field distinguishing verified-facts-paraphrased-text from
verified-core-facts-some-fields-unconfirmed \u2014 read `ai/data/corpus/seed/README.md`
before treating any of it as citation-ready without the flagged confirmations.
Next task: Phase 0, T0.1 in `prompts/phases.md` (or run `load_seed.py` once T0.3's
embedding setup exists, to fast-track a working retrieval demo on real content).
