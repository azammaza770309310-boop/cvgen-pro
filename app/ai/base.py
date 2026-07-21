"""Abstract AI provider interface — all providers implement this."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from app.core.exceptions import AIProviderNotConfiguredError


class AIProvider(ABC):
    """Common interface for every cloud AI provider."""

    id: str = "base"
    name: str = "Base Provider"
    base_url: str = ""

    def __init__(self, api_keys: list[str]):
        if not api_keys:
            raise AIProviderNotConfiguredError(
                f"No API key configured for provider '{self.id}'"
            )
        self._keys = list(api_keys)
        self._key_index = 0

    @property
    def current_key(self) -> str:
        if not self._keys:
            return ""
        return self._keys[self._key_index % len(self._keys)]

    def rotate_key(self) -> bool:
        """Rotate to the next key. Returns True if a fresh key is available."""
        if len(self._keys) <= 1:
            return False
        self._key_index += 1
        return True

    @abstractmethod
    async def parse_resume(self, text: str, lang: str = "auto") -> dict:
        """Parse a raw CV into structured JSON matching ResumeData."""

    async def improve_resume(self, section: str, content: str, lang: str = "en") -> str:
        """Improve a section of text. Default: use parse-style prompt."""
        return content

    async def generate_summary(self, role: str, experience_years: int, skills: list[str], lang: str = "en") -> str:
        """Generate a professional summary."""
        return ""

    async def analyze_ats(self, resume_dict: dict, job_description: str = "") -> dict:
        """AI-powered ATS analysis. Returns dict with recommendations."""
        return {}

    async def generate_cover_letter(self, resume_dict: dict, job_description: str = "") -> str:
        return ""

    async def translate_json(self, system: str, user: str) -> str:
        """Generic JSON-mode call for the bilingual sync translation service.

        Default implementation returns empty string; providers override with
        their raw _generate call (json_mode=True).
        """
        return ""
