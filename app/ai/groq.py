"""Groq provider (OpenAI-compatible, fast inference)."""
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

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"


class GroqProvider(AIProvider):
    id = "groq"
    name = "Groq"
    base_url = "https://api.groq.com"

    async def _chat(self, system: str, user: str, *, json_mode: bool = True) -> str:
        headers = {"Authorization": f"Bearer {self.current_key}", "Content-Type": "application/json"}
        payload = {
            "model": GROQ_MODEL,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": 0.2,
            "max_tokens": 8192,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        last_err = None
        for _ in range(len(self._keys)):
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    resp = await client.post(GROQ_ENDPOINT, headers=headers, json=payload)
                    if resp.status_code in (429, 500, 502, 503):
                        last_err = f"Groq HTTP {resp.status_code}"
                        if self.rotate_key():
                            headers["Authorization"] = f"Bearer {self.current_key}"
                            continue
                        raise AIProviderError(f"Groq error {resp.status_code}: {resp.text[:200]}")
                    if resp.status_code != 200:
                        raise AIProviderError(f"Groq HTTP {resp.status_code}: {resp.text[:300]}")
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
            except httpx.HTTPError as e:
                last_err = str(e)
                if self.rotate_key():
                    headers["Authorization"] = f"Bearer {self.current_key}"
                    continue
                raise AIProviderError(f"Groq network error: {e}")
        raise AIProviderError(f"Groq failed after retries: {last_err}")

    async def parse_resume(self, text: str, lang: str = "auto") -> dict:
        raw = await self._chat(PARSE_SYSTEM_PROMPT, build_parse_prompt(text, lang))
        data = extract_json(raw)
        if not isinstance(data, dict):
            raise AIProviderError("Groq did not return valid JSON")
        return data

    async def improve_resume(self, section: str, content: str, lang: str = "en") -> str:
        return (await self._chat("You improve resume text.", build_improve_prompt(section, content, lang), json_mode=False)).strip()

    async def generate_summary(self, role: str, experience_years: int, skills: list[str], lang: str = "en") -> str:
        return (await self._chat("You write resume summaries.", build_summary_prompt(role, experience_years, skills, lang), json_mode=False)).strip()

    async def analyze_ats(self, resume_dict: dict, job_description: str = "") -> dict:
        raw = await self._chat("You are an ATS expert.", build_ats_prompt(resume_dict, job_description))
        data = extract_json(raw)
        return data if isinstance(data, dict) else {}

    async def generate_cover_letter(self, resume_dict: dict, job_description: str = "") -> str:
        return (await self._chat("You write cover letters.", build_cover_letter_prompt(resume_dict, job_description), json_mode=False)).strip()

    async def translate_json(self, system: str, user: str) -> str:
        """Generic JSON-mode call used by the bilingual sync translation service."""
        return await self._chat(system, user, json_mode=True)

