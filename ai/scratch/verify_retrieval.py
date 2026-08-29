import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
import sys
from pathlib import Path
from dotenv import load_dotenv

ai_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ai_root))
load_dotenv(ai_root / '.env')

from qdrant_client import QdrantClient
from src.embeddings.embedding_provider import get_embedding_provider

client = QdrantClient(url=os.getenv('QDRANT_URL'), api_key=os.getenv('QDRANT_API_KEY'), timeout=60.0)
cols = ['legal_statutory', 'standards_formulations', 'case_law_prior_art', 'procedural_forms', 'international_export']

print('=' * 60)
print('QDRANT CLOUD LIVE COLLECTION POINT COUNTS')
print('=' * 60)
for c in cols:
    try:
        info = client.get_collection(c)
        print(f'  - {c:<26}: {info.points_count} points')
    except Exception as e:
        print(f'  - {c:<26}: error {e}')

print('\n' + '=' * 60)
print('VALIDATING SEMANTIC RETRIEVAL QUALITY')
print('=' * 60)

embedder = get_embedding_provider()

# Test 1: Legal / Statutory query
q1 = 'Who is entitled to apply for patents under Section 6 of the Patents Act?'
print(f'\n[Query 1: Legal Statutory] "{q1}"')
v1 = embedder.embed_query(q1)
hits1 = client.query_points(collection_name='legal_statutory', query=v1, limit=2).points
for h in hits1:
    cid = h.payload.get('chunk_id')
    txt = h.payload.get('text', '')[:200].replace('\n', ' ')
    print(f'  -> Score: {h.score:.4f} | ID: {cid}')
    print(f'     Text: {txt}...')

# Test 2: Standards & Formulations query
q2 = 'Classical formulation ingredients of Ashoka Ghrita or Taila'
print(f'\n[Query 2: Standards Formulations] "{q2}"')
v2 = embedder.embed_query(q2)
hits2 = client.query_points(collection_name='standards_formulations', query=v2, limit=2).points
for h in hits2:
    cid = h.payload.get('chunk_id')
    txt = h.payload.get('text', '')[:200].replace('\n', ' ')
    print(f'  -> Score: {h.score:.4f} | ID: {cid}')
    print(f'     Text: {txt}...')

# Test 3: Procedural Forms query
q3 = 'Form 1 application for grant of patent'
print(f'\n[Query 3: Procedural Forms] "{q3}"')
v3 = embedder.embed_query(q3)
hits3 = client.query_points(collection_name='procedural_forms', query=v3, limit=2).points
for h in hits3:
    cid = h.payload.get('chunk_id')
    txt = h.payload.get('text', '')[:200].replace('\n', ' ')
    print(f'  -> Score: {h.score:.4f} | ID: {cid}')
    print(f'     Text: {txt}...')
