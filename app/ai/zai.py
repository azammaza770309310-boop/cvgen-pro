"""ZAI internal gateway provider — uses the environment's z-ai-web-dev-sdk
via a local Node.js bridge on port 3030.

This is a real Cloud AI provider (the SDK calls a remote LLM service).
It exists so the application can be tested end-to-end with real AI parsing
even when no external API keys (Gemini/OpenAI/etc.) are configured.
"""
from __future__ import annotations

import httpx

from app.ai.base import AIProvider
from app.ai.json_utils import extract_json
from app.ai.prompts import (
    PARSE_SYSTEM_PROMPT,
    build_ats_prompt,
    build_cover_letter_prompt,
    build_improve_prompt,
    build_parse_prompt,
    build_summary_prompt,
)
from app.core.exceptions import AIProviderError

ZAI_BRIDGE_URL = "http://localhost:3030"


class ZAIProvider(AIProvider):
    """Provider that talks to the local z-ai-web-dev-sdk bridge."""

    id = "zai"
    name = "ZAI Gateway"
    base_url = ZAI_BRIDGE_URL

    def __init__(self, api_keys: list[str]):
        # The bridge doesn't need a key (the SDK handles auth internally),
        # but we accept the list to satisfy the base class contract.
        self._keys = api_keys or ["internal"]
        self._key_index = 0

    async def _chat(self, system: str, user: str) -> str:
        payload = {
            "messages": [
                {"role": "assistant", "content": system},
                {"role": "user", "content": user},
            ]
        }
        try:
            async with httpx.AsyncClient(timeout=90) as client:
                resp = await client.post(ZAI_BRIDGE_URL, json=payload)
                if resp.status_code != 200:
                    raise AIProviderError(f"ZAI bridge HTTP {resp.status_code}: {resp.text[:200]}")
                data = resp.json()
                if not data.get("success"):
                    raise AIProviderError(f"ZAI bridge error: {data.get('error', 'unknown')}")
                return data.get("content", "")
        except httpx.HTTPError as e:
            raise AIProviderError(f"ZAI bridge network error: {e}")

    async def parse_resume(self, text: str, lang: str = "auto") -> dict:
        raw = await self._chat(PARSE_SYSTEM_PROMPT, build_parse_prompt(text, lang))
        data = extract_json(raw)
        if not isinstance(data, dict):
            raise AIProviderError("ZAI did not return valid JSON for resume parse")
        return data

    async def improve_resume(self, section: str, content: str, lang: str = "en") -> str:
        return (await self._chat("You improve resume text.", build_improve_prompt(section, content, lang))).strip()

    async def generate_summary(self, role: str, experience_years: int, skills: list[str], lang: str = "en") -> str:
        return (await self._chat("You write resume summaries.", build_summary_prompt(role, experience_years, skills, lang))).strip()

    async def analyze_ats(self, resume_dict: dict, job_description: str = "") -> dict:
        raw = await self._chat("You are an ATS expert.", build_ats_prompt(resume_dict, job_description))
        data = extract_json(raw)
        return data if isinstance(data, dict) else {}

    async def generate_cover_letter(self, resume_dict: dict, job_description: str = "") -> str:
        return (await self._chat("You write cover letters.", build_cover_letter_prompt(resume_dict, job_description))).strip()
