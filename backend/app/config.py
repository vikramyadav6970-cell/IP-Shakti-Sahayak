from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # --- Database (Supabase Postgres) ---
    DATABASE_URL: str = ""

    # --- Cache (Upstash Redis) ---
    REDIS_URL: str = ""

    # --- Object Storage (Supabase Storage) ---
    SUPABASE_STORAGE_URL: str = ""
    SUPABASE_STORAGE_KEY: str = ""
    SUPABASE_STORAGE_SECRET: str = ""
    SUPABASE_STORAGE_BUCKET: str = "corpus-documents"

    # --- Auth ---
    JWT_SECRET: str = "dev-secret-change-in-production-INSECURE"

    # --- LLM ---
    LLM_API_KEY: str = ""

    # --- Qdrant Cloud ---
    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""

    # --- Frontend ---
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # --- Monitoring ---
    SENTRY_DSN: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
