import logging
from app.config import settings

logger = logging.getLogger(__name__)

# Database engine + session — created lazily only if DATABASE_URL is set
engine = None
async_session = None

if settings.DATABASE_URL:
    try:
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

        db_url = settings.DATABASE_URL
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        engine = create_async_engine(
            db_url,
            echo=False,
        )

        async_session = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        logger.info("Database engine configured")
    except Exception as e:
        logger.warning(f"Database setup failed: {e} — DB operations will be unavailable")
else:
    logger.warning("DATABASE_URL not set — database operations disabled")


async def get_db():
    """Yield a database session. Raises 503 if DB is not configured."""
    if async_session is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail="Database not configured. Set DATABASE_URL in .env"
        )
    async with async_session() as session:
        yield session
