from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import redis.asyncio as redis
import boto3
from botocore.exceptions import ClientError
import sentry_sdk
from app.config import settings
from app.db import async_session
from fastapi import APIRouter

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0,
    )

app = FastAPI(title="IP-SAKTI Sahayak API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import Request
from fastapi.responses import JSONResponse

MAX_REQUEST_SIZE_BYTES = 5 * 1024 * 1024 # 5MB

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
        "supabase_storage": "unknown"
    }

    # 1. Supabase DB Check
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        status["supabase_db"] = "ok"
    except Exception as e:
        status["supabase_db"] = f"error: {str(e)}"

    # 2. Upstash Redis Check
    try:
        r = redis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.close()
        status["upstash_redis"] = "ok"
    except Exception as e:
        status["upstash_redis"] = f"error: {str(e)}"

    # 3. Supabase Storage Check
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=settings.SUPABASE_STORAGE_URL,
            aws_access_key_id=settings.SUPABASE_STORAGE_KEY,
            aws_secret_access_key=settings.SUPABASE_STORAGE_SECRET,
            region_name="auto"
        )
        s3.head_bucket(Bucket=settings.SUPABASE_STORAGE_BUCKET)
        status["supabase_storage"] = "ok"
    except Exception as e:
        status["supabase_storage"] = f"error: {str(e)}"

    is_healthy = all(v == "ok" for v in status.values())
    return {"status": "ok" if is_healthy else "degraded", "services": status}
