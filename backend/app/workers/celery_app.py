from celery import Celery
from app.config import settings

celery_app = Celery(
    "ip_shakti_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    # Route ingestion tasks specifically to an 'ai_ingestion' queue if desired
    # but for now we just use the default celery queue or rely on task routing later.
)
