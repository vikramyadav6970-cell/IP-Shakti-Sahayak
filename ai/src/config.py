"""AI layer configuration — loads all env vars via pydantic-settings.

Single source of truth for all config across the AI layer.
Import `settings` from this module; never read os.environ directly elsewhere.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """AI layer settings, populated from .env file or environment variables."""

    # --- Qdrant Cloud ---
    qdrant_url: str = Field(..., description="Qdrant Cloud cluster URL")
    qdrant_api_key: str = Field(..., description="Qdrant Cloud API key")

    # --- Supabase (Postgres) ---
    database_url: str = Field(..., description="Supabase transaction-mode pooler connection string")

    # --- Upstash Redis ---
    redis_url: str = Field(..., description="Upstash Redis rediss:// URL")

    # --- LLM Provider ---
    llm_provider: str = Field(default="gemini", description="One of: openai | anthropic | gemini")
    llm_model: str = Field(default="gemini-2.0-flash", description="Model name for the chosen provider")
    llm_api_key: str = Field(..., description="API key for the LLM provider")

    # --- Embedding Model ---
    embedding_model: str = Field(default="BAAI/bge-m3", description="Embedding model name/path")

    # --- Cohere Rerank (optional) ---
    cohere_api_key: Optional[str] = Field(default=None, description="If set, uses Cohere Rerank instead of local BGE reranker")

    # --- Neo4j AuraDB (optional, Phase 5 stretch) ---
    neo4j_uri: Optional[str] = Field(default=None, description="Neo4j AuraDB connection URI")
    neo4j_password: Optional[str] = Field(default=None, description="Neo4j AuraDB password")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Singleton — import this everywhere instead of re-instantiating Settings
settings = Settings()
