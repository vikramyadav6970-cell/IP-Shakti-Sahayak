"""End-to-end corpus ingestion script for IP-SAKTI Sahayak.

Parses all available legal, regulatory, pharmacopoeia, and form documents,
chunks them into the normalized 200-800 token band, generates dense embeddings
using BAAI/bge-m3, and upserts them idempotently into Qdrant Cloud collections.
"""

import glob
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Ensure stdout handles UTF-8 cleanly
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ai_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ai_root))

from dotenv import load_dotenv
load_dotenv(ai_root / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ingestion")

import torch
if torch.cuda.is_available():
    logger.info("CUDA is ACTIVE: %s (Capability %s)", torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))
else:
    logger.info("CUDA is NOT available, running on CPU")

from src.embeddings.indexer import QdrantIndexer, ALL_COLLECTIONS
from src.embeddings.embedding_provider import get_embedding_provider
from src.ingestion.parser import parse_document, ParsedDocument
from src.ingestion.chunker import chunk_document, Chunk

DATA_DIR = Path(r"D:\Hackathons\SIH 2026\Data")

# Route files to collection and jurisdiction
def route_document(dir_name: str, file_name: str) -> Optional[Tuple[str, str, str]]:
    fl = file_name.lower()
    if fl.startswith("ppteg"):
        return None  # Scratches / raw committee drafts without clean structure
    
    # Scanned forms without text layer — skip and record gap
    if fl in ["form 2 patent filing.pdf", "form_18 a patent filing.pdf"]:
        return None

    if dir_name == "intl":
        return ("international_export", "INTERNATIONAL", "TREATY")
    if dir_name == "forms":
        return ("procedural_forms", "INDIA", "FORM")
    if dir_name == "herbs and drugs":
        jur = "INTERNATIONAL" if fl.startswith("who") else "INDIA"
        return ("standards_formulations", jur, "MONOGRAPH")
    if fl.startswith("afi"):
        return ("standards_formulations", "INDIA", "MONOGRAPH")
    
    # Defaults to statutory
    doc_type = "RULE" if "rule" in fl else ("REGULATION" if "regulation" in fl else "STATUTE")
    return ("legal_statutory", "INDIA", doc_type)


def collect_documents() -> List[ParsedDocument]:
    """Parse all available PDF files and seed files into ParsedDocuments."""
    seen_paths = set()
    parsed_docs: List[ParsedDocument] = []
    
    pdf_paths = sorted(glob.glob(str(DATA_DIR / "*/*.pdf"))) + sorted(glob.glob(str(DATA_DIR / "*/*.PDF")))
    
    logger.info("Found %d PDF files in %s", len(pdf_paths), DATA_DIR)
    
    for p_str in pdf_paths:
        p = Path(p_str)
        canonical = str(p.resolve()).lower()
        if canonical in seen_paths:
            continue
        seen_paths.add(canonical)
        
        dir_name = p.parent.name
        file_name = p.name
        
        routing = route_document(dir_name, file_name)
        if routing is None:
            logger.info("Skipping file (scanned or excluded): %s", file_name)
            continue
            
        coll, jur, dtype = routing
        doc_id = p.stem.lower().replace(" ", "_").replace("-", "_").replace(",", "")
        
        meta = {
            "document_id": doc_id,
            "title": p.stem,
            "corpus_collection": coll,
            "jurisdiction": jur,
            "document_type": dtype,
            "source_file": file_name,
        }
        
        try:
            logger.info("Parsing [%s] -> %s (%s)", coll, file_name, jur)
            doc = parse_document(p, meta)
            parsed_docs.append(doc)
        except Exception as e:
            logger.error("Failed to parse %s: %s", file_name, e)

    # Also check seed JSONL files for case law and TK datasets
    seed_dir = ai_root / "data" / "corpus" / "seed"
    if seed_dir.exists():
        for jsonl_file in seed_dir.glob("*.jsonl"):
            if "schema_examples" in jsonl_file.name:
                continue
            canonical = str(jsonl_file.resolve()).lower()
            if canonical in seen_paths:
                continue
            seen_paths.add(canonical)
            
            coll = "case_law_prior_art" if "prior_art" in jsonl_file.name else (
                "standards_formulations" if "ayush" in jsonl_file.name else "legal_statutory"
            )
            meta = {
                "document_id": jsonl_file.stem,
                "title": jsonl_file.stem.replace("_", " ").title(),
                "corpus_collection": coll,
                "jurisdiction": "INDIA",
                "document_type": "JSONL_SEED",
            }
            try:
                logger.info("Parsing seed JSONL [%s] -> %s", coll, jsonl_file.name)
                doc = parse_document(jsonl_file, meta)
                parsed_docs.append(doc)
            except Exception as e:
                logger.error("Failed to parse seed %s: %s", jsonl_file.name, e)

    return parsed_docs


def run_ingestion(batch_size: int = 64):
    """Execute end-to-end ingestion pipeline."""
    start_time = time.time()
    logger.info("=" * 70)
    logger.info("STARTING IP-SAKTI SAHAYAK CORPUS INGESTION")
    logger.info("=" * 70)
    
    # 1. Parse documents
    parsed_docs = collect_documents()
    logger.info("Successfully parsed %d documents.", len(parsed_docs))
    
    # 2. Chunk documents with 200-800 token normalization
    all_chunks: List[Chunk] = []
    chunks_by_coll: Dict[str, List[Chunk]] = {col: [] for col in ALL_COLLECTIONS}
    
    for doc in parsed_docs:
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)
        for c in chunks:
            chunks_by_coll[c.corpus_collection].append(c)
            
    logger.info("=" * 70)
    logger.info("TOTAL NORMALIZED CHUNKS PRODUCED: %d", len(all_chunks))
    for col, c_list in chunks_by_coll.items():
        logger.info("  - %-26s: %4d chunks", col, len(c_list))
    logger.info("=" * 70)
    
    # 3. Initialize Qdrant Indexer
    logger.info("Initializing Qdrant Cloud Indexer with BAAI/bge-m3...")
    indexer = QdrantIndexer()
    indexer.ensure_collections()
    
    # 4. Batch embed and upsert into Qdrant Cloud
    logger.info("Starting batch vector embedding and idempotent upsert...")
    indexed_stats = indexer.index_chunks(all_chunks, batch_size=batch_size)
    
    # 5. Fetch final collection statistics from Qdrant Cloud
    final_stats = indexer.get_collection_stats()
    
    elapsed = time.time() - start_time
    logger.info("=" * 70)
    logger.info("INGESTION COMPLETED SUCCESSFULLY in %.2f seconds", elapsed)
    logger.info("=" * 70)
    logger.info("QDRANT CLOUD COLLECTION POINT COUNTS:")
    for col, count in final_stats.items():
        logger.info("  - %-26s: %5d points", col, count)
    logger.info("=" * 70)


if __name__ == "__main__":
    run_ingestion()
