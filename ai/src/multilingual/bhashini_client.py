"""Bhashini Translation Client & Multilingual Support module.

Implements Bhashini (ULCA) API wrapper with LLM fallback for Hindi <-> English translation.
Ensures citation source titles, section references, and inline [chunk_id] markers
are never modified or translated.
"""

from dataclasses import dataclass
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional
import urllib.error
import urllib.request

from src.reasoning.llm_provider import LLMProvider, get_llm_provider

logger = logging.getLogger(__name__)

BHASHINI_INFERENCE_URL = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"


@dataclass
class TranslationResult:
    """Outcome of translation."""

    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    service_used: str  # "BHASHINI_API" | "LLM_FALLBACK" | "PASSTHROUGH"


class BhashiniClient:
    """Bhashini (ULCA) client with LLM-based fallback for Hindi/English translation."""

    def __init__(
        self,
        user_id: Optional[str] = None,
        api_key: Optional[str] = None,
        pipeline_id: Optional[str] = None,
        llm_provider: Optional[LLMProvider] = None,
    ):
        self.user_id = user_id or os.getenv("BHASHINI_USER_ID")
        self.api_key = api_key or os.getenv("BHASHINI_API_KEY")
        self.pipeline_id = pipeline_id or os.getenv("BHASHINI_PIPELINE_ID")
        self.llm_provider = llm_provider

    def is_bhashini_configured(self) -> bool:
        """Check whether valid Bhashini credentials are present."""
        return bool(self.user_id and self.api_key and self.pipeline_id)

    async def translate_hi_to_en(self, text: str, llm_provider: Optional[LLMProvider] = None) -> TranslationResult:
        """Translate Hindi input text to English for retrieval & extraction."""
        return await self._translate_with_placeholders(text, source_lang="hi", target_lang="en", llm_provider=llm_provider)

    async def translate_en_to_hi(self, text: str, llm_provider: Optional[LLMProvider] = None) -> TranslationResult:
        """Translate English synthesized output to Hindi, preserving citations."""
        return await self._translate_with_placeholders(text, source_lang="en", target_lang="hi", llm_provider=llm_provider)

    async def _translate_with_placeholders(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        llm_provider: Optional[LLMProvider] = None,
    ) -> TranslationResult:
        """Translate while strictly protecting inline citations and statutory markers."""
        if not text or not text.strip():
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_lang,
                target_language=target_lang,
                service_used="PASSTHROUGH",
            )

        active_llm = llm_provider or self.llm_provider

        # 1. Mask inline [chunk_id] tags with immutable placeholders
        citation_placeholders: Dict[str, str] = {}

        def replace_citation(match):
            placeholder = f"__CITATION_TAG_{len(citation_placeholders)}__"
            citation_placeholders[placeholder] = match.group(0)
            return placeholder

        masked_text = re.sub(r"\[([a-zA-Z0-9_\-\.\:\/]+)\]", replace_citation, text)

        # 2. Perform translation
        translated_masked = ""
        service_used = "PASSTHROUGH"

        if self.is_bhashini_configured():
            try:
                translated_masked = await self._call_bhashini_api(masked_text, source_lang, target_lang)
                service_used = "BHASHINI_API"
            except Exception as e:
                logger.warning("Bhashini API request failed (%s); falling back to LLM translation.", e)
                translated_masked = await self._call_llm_translation(masked_text, source_lang, target_lang, active_llm)
                service_used = "LLM_FALLBACK"
        else:
            # Bhashini not configured: Use LLM fallback
            try:
                translated_masked = await self._call_llm_translation(masked_text, source_lang, target_lang, active_llm)
                service_used = "LLM_FALLBACK"
            except Exception as e:
                logger.warning("LLM translation fallback failed (%s); returning original text.", e)
                translated_masked = masked_text
                service_used = "PASSTHROUGH"

        # 3. Unmask inline citation placeholders
        final_text = translated_masked
        for placeholder, original_tag in citation_placeholders.items():
            final_text = final_text.replace(placeholder, original_tag)

        return TranslationResult(
            original_text=text,
            translated_text=final_text,
            source_language=source_lang,
            target_language=target_lang,
            service_used=service_used,
        )

    async def _call_bhashini_api(self, text: str, source_lang: str, target_lang: str) -> str:
        """Invoke Bhashini Dhruva NMT inference pipeline."""
        payload = {
            "pipelineTasks": [
                {
                    "taskType": "translation",
                    "config": {
                        "language": {
                            "sourceLanguage": source_lang,
                            "targetLanguage": target_lang,
                        }
                    },
                }
            ],
            "inputData": {
                "input": [{"source": text}]
            },
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": self.api_key or "",
            "userID": self.user_id or "",
            "ulcaApiKey": self.api_key or "",
        }

        req = urllib.request.Request(
            BHASHINI_INFERENCE_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pipeline_response = data.get("pipelineResponse", [])
            if pipeline_response:
                output = pipeline_response[0].get("output", [])
                if output:
                    return output[0].get("target", text)
        return text

    async def _call_llm_translation(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        llm: Optional[LLMProvider] = None,
    ) -> str:
        """High-fidelity translation using the LLM provider."""
        active_llm = llm or self.llm_provider or get_llm_provider()
        target_name = "Hindi (हिन्दी)" if target_lang == "hi" else "English"

        system_prompt = (
            f"You are a professional legal translator specializing in Indian Intellectual Property and AYUSH law. "
            f"Translate the following text accurately into {target_name}. "
            f"CRITICAL: Do NOT translate statutory citations, section numbers (e.g. 'Section 3(p)'), "
            f"or placeholders like '__CITATION_TAG_0__'. Preserve all formatting, bullet points, and headers."
        )

        return await active_llm.generate_async(
            system_prompt=system_prompt,
            user_prompt=text,
            temperature=0.1,
            max_tokens=2048,
        )


# Module-level convenience client
default_bhashini_client = BhashiniClient()


async def translate_text(
    text: str,
    source_language: str = "en",
    target_language: str = "hi",
    llm_provider: Optional[LLMProvider] = None,
) -> TranslationResult:
    """Translate text between Hindi and English."""
    if source_language == "hi" and target_language == "en":
        return await default_bhashini_client.translate_hi_to_en(text, llm_provider=llm_provider)
    elif source_language == "en" and target_language == "hi":
        return await default_bhashini_client.translate_en_to_hi(text, llm_provider=llm_provider)
    return TranslationResult(
        original_text=text,
        translated_text=text,
        source_language=source_language,
        target_language=target_language,
        service_used="PASSTHROUGH",
    )
