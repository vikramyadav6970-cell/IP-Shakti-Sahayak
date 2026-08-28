"""Smoke tests for the config module — verifying env var loading."""

import pytest
import os


def test_settings_loads_from_env(monkeypatch):
    """Settings should load all required vars without error when env is set."""
    monkeypatch.setenv("QDRANT_URL", "https://test.cloud.qdrant.io:6333")
    monkeypatch.setenv("QDRANT_API_KEY", "test-key")
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")
    monkeypatch.setenv("REDIS_URL", "rediss://default:test@test.upstash.io:6379")
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("LLM_MODEL", "gemini-2.0-flash")
    monkeypatch.setenv("LLM_API_KEY", "test-llm-key")

    from src.config import Settings
    s = Settings(_env_file=None)

    assert s.qdrant_url == "https://test.cloud.qdrant.io:6333"
    assert s.llm_provider == "gemini"
    assert s.embedding_model == "BAAI/bge-m3"  # default
    assert s.cohere_api_key is None  # optional, not set


def test_settings_fails_without_required_vars(monkeypatch):
    """Settings should raise if required env vars are missing."""
    for var in ["QDRANT_URL", "QDRANT_API_KEY", "DATABASE_URL", "REDIS_URL", "LLM_API_KEY"]:
        monkeypatch.delenv(var, raising=False)

    from src.config import Settings
    with pytest.raises(Exception):
        Settings(_env_file=None)
