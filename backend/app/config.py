from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SUPABASE_STORAGE_URL: str
    SUPABASE_STORAGE_KEY: str
    SUPABASE_STORAGE_SECRET: str
    SUPABASE_STORAGE_BUCKET: str
    JWT_SECRET: str
    LLM_API_KEY: str
    QDRANT_URL: str
    QDRANT_API_KEY: str
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    SENTRY_DSN: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
