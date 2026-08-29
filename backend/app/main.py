import sys
import os
from pathlib import Path

# Add ai/ directory to sys.path so we can import from src.reasoning, src.context_gathering, etc.
_ai_layer_path = str(Path(__file__).resolve().parent.parent.parent / "ai")
if _ai_layer_path not in sys.path:
    sys.path.insert(0, _ai_layer_path)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings

# Propagate environment variables for AI layer
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
if settings.QDRANT_URL:
    os.environ["QDRANT_URL"] = settings.QDRANT_URL
if settings.QDRANT_API_KEY:
    os.environ["QDRANT_API_KEY"] = settings.QDRANT_API_KEY
if settings.LLM_API_KEY:
    os.environ["LLM_API_KEY"] = settings.LLM_API_KEY
if settings.DATABASE_URL:
    os.environ["DATABASE_URL"] = settings.DATABASE_URL
if settings.REDIS_URL:
    os.environ["REDIS_URL"] = settings.REDIS_URL

# Sentry — optional
try:
    if settings.SENTRY_DSN:
        import sentry_sdk
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            traces_sample_rate=1.0,
        )
except Exception:
    pass

app = FastAPI(title="IP-SAKTI Sahayak API")

# CORS Configuration — allow multiple dev origins
_allowed_origins = [
    settings.FRONTEND_ORIGIN,
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]
# Deduplicate
_allowed_origins = list(set(_allowed_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_REQUEST_SIZE_BYTES = 5 * 1024 * 1024  # 5MB

@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    if request.method in ["POST", "PUT", "PATCH"]:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_SIZE_BYTES:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large"}
            )
    return await call_next(request)

from app.api.v1 import api_router
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    status = {
        "supabase_db": "unknown",
        "upstash_redis": "unknown",
        "supabase_storage": "unknown",
        "ai_layer": "unknown",
    }

    # 1. Supabase DB Check
    try:
        if settings.DATABASE_URL:
            from sqlalchemy import text
            from app.db import async_session
            async with async_session() as session:
                await session.execute(text("SELECT 1"))
            status["supabase_db"] = "ok"
        else:
            status["supabase_db"] = "not configured"
    except Exception as e:
        status["supabase_db"] = f"error: {str(e)}"

    # 2. Upstash Redis Check
    try:
        if settings.REDIS_URL:
            import redis.asyncio as aioredis
            r = aioredis.from_url(settings.REDIS_URL)
            await r.ping()
            await r.close()
            status["upstash_redis"] = "ok"
        else:
            status["upstash_redis"] = "not configured"
    except Exception as e:
        status["upstash_redis"] = f"error: {str(e)}"

    # 3. Supabase Storage Check
    try:
        if settings.SUPABASE_STORAGE_URL and settings.SUPABASE_STORAGE_KEY:
            import boto3
            s3 = boto3.client(
                "s3",
                endpoint_url=settings.SUPABASE_STORAGE_URL,
                aws_access_key_id=settings.SUPABASE_STORAGE_KEY,
                aws_secret_access_key=settings.SUPABASE_STORAGE_SECRET,
                region_name="auto"
            )
            s3.head_bucket(Bucket=settings.SUPABASE_STORAGE_BUCKET)
            status["supabase_storage"] = "ok"
        else:
            status["supabase_storage"] = "not configured"
    except Exception as e:
        status["supabase_storage"] = f"error: {str(e)}"

    # 4. AI Layer Check
    try:
        from src.reasoning.query_pipeline import QueryPipeline
        status["ai_layer"] = "ok"
    except Exception as e:
        status["ai_layer"] = f"error: {str(e)}"

    is_healthy = all(v == "ok" for v in status.values())
    return {"status": "ok" if is_healthy else "degraded", "services": status}
