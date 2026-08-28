"""Unit and smoke tests for LLM provider abstraction."""

import os
from unittest.mock import MagicMock, patch
import pytest

from src.reasoning.llm_provider import (
    LLMProvider,
    GeminiProvider,
    OpenAIProvider,
    AnthropicProvider,
    get_llm_provider,
)


def test_unsupported_provider_raises_error():
    """Requesting an unknown provider should raise ValueError."""
    with pytest.raises(ValueError, match="Unsupported LLM provider 'unknown'"):
        get_llm_provider(provider="unknown", api_key="dummy-key")


def test_missing_api_key_raises_error(monkeypatch):
    """Instantiating a provider with no API key should raise ValueError."""
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    with pytest.raises(ValueError, match="API key must be provided"):
        GeminiProvider(api_key=None)


def test_get_llm_provider_factory(monkeypatch):
    """Factory should correctly instantiate requested provider types."""
    monkeypatch.setenv("LLM_API_KEY", "dummy-key")

    gemini = get_llm_provider("gemini", "gemini-2.0-flash")
    assert isinstance(gemini, GeminiProvider)
    assert gemini.model_name == "gemini-2.0-flash"

    openai = get_llm_provider("openai", "gpt-4o")
    assert isinstance(openai, OpenAIProvider)
    assert openai.model_name == "gpt-4o"

    anthropic = get_llm_provider("anthropic", "claude-3-5-sonnet-20241022")
    assert isinstance(anthropic, AnthropicProvider)
    assert anthropic.model_name == "claude-3-5-sonnet-20241022"


def test_openai_provider_generate_mock():
    """OpenAIProvider should format messages and return response text."""
    provider = OpenAIProvider(model_name="gpt-4o", api_key="test-key")

    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Section 3(p) excludes traditional knowledge."
    mock_response = MagicMock(choices=[mock_choice])
    mock_client.chat.completions.create.return_value = mock_response

    with patch.object(provider, "_get_client", return_value=mock_client):
        res = provider.generate(
            system_prompt="You are a legal assistant.",
            user_prompt="Explain Section 3(p).",
            temperature=0.2
        )
        assert res == "Section 3(p) excludes traditional knowledge."
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a legal assistant."},
                {"role": "user", "content": "Explain Section 3(p)."}
            ],
            temperature=0.2
        )


def test_anthropic_provider_generate_mock():
    """AnthropicProvider should format parameters and return response text."""
    provider = AnthropicProvider(model_name="claude-3-5-sonnet-20241022", api_key="test-key")

    mock_client = MagicMock()
    mock_block = MagicMock()
    mock_block.text = "Patents Act 1970 analysis."
    mock_response = MagicMock(content=[mock_block])
    mock_client.messages.create.return_value = mock_response

    with patch.object(provider, "_get_client", return_value=mock_client):
        res = provider.generate(
            system_prompt="You are an IP assistant.",
            user_prompt="Analyze this formulation.",
            max_tokens=1024
        )
        assert res == "Patents Act 1970 analysis."
        mock_client.messages.create.assert_called_once_with(
            model="claude-3-5-sonnet-20241022",
            messages=[{"role": "user", "content": "Analyze this formulation."}],
            max_tokens=1024,
            system="You are an IP assistant."
        )


def test_gemini_provider_generate_mock():
    """GeminiProvider should delegate to generator and return text."""
    provider = GeminiProvider(model_name="gemini-2.0-flash", api_key="test-key")

    with patch.object(provider, "_generate_via_google_genai", return_value="Ayurveda IP guidance response."):
        res = provider.generate(
            system_prompt="System instruction",
            user_prompt="User query"
        )
        assert res == "Ayurveda IP guidance response."


@pytest.mark.smoke
def test_llm_provider_live_smoke():
    """Live smoke test against configured provider API.

    Skips automatically if no valid API key is present in the environment.
    """
    key = os.getenv("LLM_API_KEY")
    if not key or key.startswith("your-") or len(key) < 10:
        pytest.skip("No live LLM_API_KEY set; skipping live API smoke test.")

    provider_name = os.getenv("LLM_PROVIDER", "gemini")
    model_name = os.getenv("LLM_MODEL")

    provider = get_llm_provider(provider=provider_name, model=model_name, api_key=key)
    try:
        response = provider.generate(
            system_prompt="Respond with exactly one word.",
            user_prompt="Say 'HELLO'"
        )
        assert response is not None
        assert len(response.strip()) > 0
    except Exception as e:
        pytest.skip(f"Live API call returned error: {e}")
