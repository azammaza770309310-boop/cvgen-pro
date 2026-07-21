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
from app.core.exceptions import AIInvalidKeyError, AIProviderError, AIQuotaExceededError

GEMINI_MODEL = "gemini-1.5-flash"
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
)


def _categorize_gemini_error(status_code: int, body: str) -> AIProviderError:
    """Map an HTTP status + error body to the correct exception type.

    This is critical for correct user-facing messages AND correct failover:
      - 400 with 'API key not valid' / 'API_KEY_INVALID' → AIInvalidKeyError
      - 401 / 403 (auth/permission)                     → AIInvalidKeyError
      - 429 (quota/rate limit)                          → AIQuotaExceededError
      - 500/502/503 (Google server error)               → AIProviderError (transient)
      - other 400 (bad request, model not found)        → AIProviderError
    """
    body_lower = (body or "").lower()
    if status_code == 400:
        if "api key not valid" in body_lower or "api_key_invalid" in body_lower:
            return AIInvalidKeyError(f"Gemini API key is not valid. Please check your key. (HTTP 400: {body[:200]})")
        if "model" in body_lower and "not found" in body_lower:
            return AIProviderError(f"Gemini model '{GEMINI_MODEL}' not found or unavailable. (HTTP 400: {body[:200]})")
        return AIProviderError(f"Gemini bad request (HTTP 400): {body[:200]}")
    if status_code in (401, 403):
        if "permission" in body_lower or "forbidden" in body_lower:
            return AIInvalidKeyError(f"Gemini API key lacks permission (HTTP {status_code}): {body[:200]}")
        return AIInvalidKeyError(f"Gemini authentication failed (HTTP {status_code}): {body[:200]}")
    if status_code == 404:
        return AIProviderError(f"Gemini model '{GEMINI_MODEL}' not found (HTTP 404). The model may have been deprecated. {body[:200]}")
    if status_code == 429:
        return AIQuotaExceededError(
            "Gemini API key is valid but the quota/rate limit was reached (HTTP 429). "
            "The key is correct — please wait and retry, or add backup keys. " + body[:200]
        )
    if status_code in (500, 502, 503):
        return AIProviderError(f"Gemini server error (HTTP {status_code}). This is transient — please retry. {body[:200]}")
    return AIProviderError(f"Gemini HTTP {status_code}: {body[:200]}")


class GeminiProvider(AIProvider):
    id = "gemini"
    name = "Google Gemini"
    base_url = "https://generativelanguage.googleapis.com"

    async def _generate(self, system: str, user: str, *, json_mode: bool = True) -> str:
        payload = {
            "contents": [{"role": "user", "parts": [{"text": f"{system}\n\n{user}"}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 8192,
                "responseMimeType": "application/json" if json_mode else "text/plain",
            },
        }
        last_err: AIProviderError | None = None
        rotated = False
        for attempt in range(len(self._keys)):
            url = GEMINI_ENDPOINT.format(model=GEMINI_MODEL, key=self.current_key)
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    resp = await client.post(url, json=payload)

                if resp.status_code == 200:
                    data = resp.json()
                    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                    return "".join(p.get("text", "") for p in parts)

                # Categorize the error precisely.
                err = _categorize_gemini_error(resp.status_code, resp.text)

                # Only retry on TRANSIENT errors (429 quota, 5xx server) when we
                # have another key to rotate to. NEVER retry on invalid key —
                # the key is bad, rotating to the same provider's other keys is
                # fine (different keys), but we must report invalid_key clearly.
                if isinstance(err, AIQuotaExceededError) or resp.status_code in (500, 502, 503):
                    last_err = err
                    if self.rotate_key():
                        rotated = True
                        continue
                    # No more keys to rotate — raise the categorized error.
                    raise err
                # Invalid key or non-transient error: raise immediately so the
                # failover engine can move to the next PROVIDER (different keys).
                raise err

            except httpx.TimeoutException as e:
                last_err = AIProviderError(f"Gemini request timed out: {e}")
                if self.rotate_key():
                    rotated = True
                    continue
                raise last_err
            except httpx.HTTPError as e:
                last_err = AIProviderError(f"Gemini network error: {e}")
                if self.rotate_key():
                    rotated = True
                    continue
                raise last_err

        # Exhausted all key rotations with transient errors.
        if last_err is not None:
            raise last_err
        raise AIProviderError("Gemini failed for an unknown reason")

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

    async def translate_json(self, system: str, user: str) -> str:
        """Generic JSON-mode call used by the bilingual sync translation service."""
        return await self._generate(system, user, json_mode=True)
