"""Google Gemini AI provider (primary)."""
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

GEMINI_MODEL = "gemini-1.5-pro"
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
)


class GeminiProvider(AIProvider):
    id = "gemini"
    name = "Google Gemini"
    base_url = "https://generativelanguage.googleapis.com"

    async def _generate(self, system: str, user: str, *, json_mode: bool = True) -> str:
        url = GEMINI_ENDPOINT.format(model=GEMINI_MODEL, key=self.current_key)
        payload = {
            "contents": [{"role": "user", "parts": [{"text": f"{system}\n\n{user}"}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 8192,
                "responseMimeType": "application/json" if json_mode else "text/plain",
            },
        }
        last_err = None
        for attempt in range(len(self._keys)):
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 429 or resp.status_code in (500, 502, 503):
                        last_err = f"Gemini HTTP {resp.status_code}"
                        if self.rotate_key():
                            url = GEMINI_ENDPOINT.format(model=GEMINI_MODEL, key=self.current_key)
                            continue
                        raise AIProviderError(f"Gemini rate/error {resp.status_code}: {resp.text[:200]}")
                    if resp.status_code != 200:
                        raise AIProviderError(f"Gemini HTTP {resp.status_code}: {resp.text[:300]}")
                    data = resp.json()
                    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                    return "".join(p.get("text", "") for p in parts)
            except httpx.HTTPError as e:
                last_err = str(e)
                if self.rotate_key():
                    url = GEMINI_ENDPOINT.format(model=GEMINI_MODEL, key=self.current_key)
                    continue
                raise AIProviderError(f"Gemini network error: {e}")
        raise AIProviderError(f"Gemini failed after retries: {last_err}")

    async def parse_resume(self, text: str, lang: str = "auto") -> dict:
        raw = await self._generate(PARSE_SYSTEM_PROMPT, build_parse_prompt(text, lang))
        data = extract_json(raw)
        if not isinstance(data, dict):
            raise AIProviderError("Gemini did not return valid JSON for resume parse")
        return data

    async def improve_resume(self, section: str, content: str, lang: str = "en") -> str:
        return (await self._generate("You improve resume text.", build_improve_prompt(section, content, lang), json_mode=False)).strip()

    async def generate_summary(self, role: str, experience_years: int, skills: list[str], lang: str = "en") -> str:
        return (await self._generate("You write resume summaries.", build_summary_prompt(role, experience_years, skills, lang), json_mode=False)).strip()

    async def analyze_ats(self, resume_dict: dict, job_description: str = "") -> dict:
        raw = await self._generate("You are an ATS expert.", build_ats_prompt(resume_dict, job_description))
        data = extract_json(raw)
        if not isinstance(data, dict):
            raise AIProviderError("Gemini ATS analysis returned invalid JSON")
        return data

    async def generate_cover_letter(self, resume_dict: dict, job_description: str = "") -> str:
        return (await self._generate("You write cover letters.", build_cover_letter_prompt(resume_dict, job_description), json_mode=False)).strip()
