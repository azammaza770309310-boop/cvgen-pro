"""AI Provider Manager — selects the configured provider and fails over.

Single source of truth for provider instantiation and failover logic.
No local AI fallback. If all cloud providers fail, a clear error is raised.
"""
from __future__ import annotations

import logging
from typing import Optional

from app.ai.anthropic import AnthropicProvider
from app.ai.base import AIProvider
from app.ai.compat import DeepSeekProvider, MistralProvider, XAIProvider
from app.ai.gemini import GeminiProvider
from app.ai.groq import GroqProvider
from app.ai.openai import OpenAIProvider
from app.ai.openrouter import OpenRouterProvider
from app.ai.zai import ZAIProvider
from app.core.config import settings
from app.core.exceptions import (
    AIAllProvidersFailedError,
    AIProviderError,
    AIProviderNotConfiguredError,
)

logger = logging.getLogger("cvgen.ai")

# Provider class registry (single source of truth)
PROVIDER_CLASSES: dict[str, type[AIProvider]] = {
    "gemini": GeminiProvider,
    "google": GeminiProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "claude": AnthropicProvider,
    "openrouter": OpenRouterProvider,
    "groq": GroqProvider,
    "deepseek": DeepSeekProvider,
    "mistral": MistralProvider,
    "xai": XAIProvider,
    "zai": ZAIProvider,
}

# Safe metadata for the frontend (never the key)
PROVIDER_META: dict[str, dict] = {
    "gemini": {"name": "Google Gemini", "website": "https://ai.google.dev", "description": "Primary — Google Gemini 2.0 Flash"},
    "openai": {"name": "OpenAI", "website": "https://platform.openai.com", "description": "GPT-4o mini"},
    "anthropic": {"name": "Anthropic Claude", "website": "https://anthropic.com", "description": "Claude 3.5 Sonnet"},
    "openrouter": {"name": "OpenRouter", "website": "https://openrouter.ai", "description": "Multi-model router"},
    "groq": {"name": "Groq", "website": "https://groq.com", "description": "Llama 3.3 70B, fast"},
    "deepseek": {"name": "DeepSeek", "website": "https://deepseek.com", "description": "DeepSeek Chat"},
    "mistral": {"name": "Mistral AI", "website": "https://mistral.ai", "description": "Mistral Large"},
    "xai": {"name": "xAI Grok", "website": "https://x.ai", "description": "Grok 2"},
    "zai": {"name": "ZAI Gateway", "website": "https://z.ai", "description": "Internal ZAI Cloud AI gateway"},
}


class AIManager:
    """Selects and runs the configured cloud AI provider with failover."""

    def __init__(self):
        self._primary = settings.default_ai_provider.lower()
        self._backup = settings.backup_ai_provider.lower()

    # ------------------------------------------------------------------
    # Metadata for frontend
    # ------------------------------------------------------------------

    def list_providers(self) -> list[dict]:
        out = []
        for pid, meta in PROVIDER_META.items():
            keys = settings.get_provider_keys(pid)
            out.append({
                "id": pid,
                "name": meta["name"],
                "website": meta["website"],
                "description": meta["description"],
                "configured": len(keys) > 0,
                "enabled": True,
                "has_backup": len(keys) > 1,
            })
        return out

    def is_configured(self, provider: str) -> bool:
        return len(settings.get_provider_keys(provider)) > 0

    # ------------------------------------------------------------------
    # Provider instantiation
    # ------------------------------------------------------------------

    def _instantiate(self, provider: str) -> AIProvider:
        pid = provider.lower()
        cls = PROVIDER_CLASSES.get(pid)
        if not cls:
            raise AIProviderNotConfiguredError(f"Unknown provider: {provider}")
        keys = settings.get_provider_keys(pid)
        if not keys:
            raise AIProviderNotConfiguredError(
                f"Provider '{pid}' has no API key configured. "
                f"Set the corresponding environment variable on the server."
            )
        return cls(keys)

    def _failover_chain(self, requested: str) -> list[str]:
        """Build an ordered list of providers to try: requested → backup → any configured."""
        chain: list[str] = []
        seen = set()
        for p in (requested, self._backup, self._primary):
            if p and p not in seen and self.is_configured(p):
                chain.append(p)
                seen.add(p)
        # add any other configured providers as last resort
        for pid in PROVIDER_META:
            if pid not in seen and self.is_configured(pid):
                chain.append(pid)
                seen.add(pid)
        return chain

    # ------------------------------------------------------------------
    # Public API (delegated to providers)
    # ------------------------------------------------------------------

    async def parse_resume(self, text: str, provider: str = "", lang: str = "auto") -> dict:
        return await self._run_with_failover(
            "parse_resume", provider=provider or self._primary, args=(text,), kwargs={"lang": lang}
        )

    async def improve_resume(self, section: str, content: str, provider: str = "", lang: str = "en") -> str:
        return await self._run_with_failover(
            "improve_resume", provider=provider or self._primary, args=(section, content), kwargs={"lang": lang}
        )

    async def generate_summary(self, role: str, years: int, skills: list[str], provider: str = "", lang: str = "en") -> str:
        return await self._run_with_failover(
            "generate_summary", provider=provider or self._primary, args=(role, years, skills), kwargs={"lang": lang}
        )

    async def analyze_ats(self, resume_dict: dict, job_description: str = "", provider: str = "") -> dict:
        return await self._run_with_failover(
            "analyze_ats", provider=provider or self._primary, args=(resume_dict,), kwargs={"job_description": job_description}
        )

    async def generate_cover_letter(self, resume_dict: dict, job_description: str = "", provider: str = "") -> str:
        return await self._run_with_failover(
            "generate_cover_letter", provider=provider or self._primary, args=(resume_dict,), kwargs={"job_description": job_description}
        )

    # ------------------------------------------------------------------
    # Failover engine
    # ------------------------------------------------------------------

    async def _run_with_failover(self, method: str, *, provider: str, args: tuple, kwargs: dict):
        chain = self._failover_chain(provider)
        if not chain:
            raise AIAllProvidersFailedError(
                "No AI provider is configured. Set at least one API key "
                "(e.g. GEMINI_API_KEY) on the server."
            )
        errors: list[str] = []
        for pid in chain:
            try:
                inst = self._instantiate(pid)
                fn = getattr(inst, method)
                result = await fn(*args, **kwargs)
                if pid != chain[0]:
                    logger.info("AI failover succeeded with '%s' (primary '%s' failed)", pid, chain[0])
                return result
            except AIProviderNotConfiguredError as e:
                errors.append(f"{pid}: {e.message}")
                continue
            except AIProviderError as e:
                errors.append(f"{pid}: {e.message}")
                logger.warning("AI provider '%s' failed: %s", pid, e.message)
                continue
            except Exception as e:  # noqa: BLE001
                errors.append(f"{pid}: {type(e).__name__}: {e}")
                logger.exception("Unexpected error from provider '%s'", pid)
                continue
        raise AIAllProvidersFailedError(
            "All configured AI providers failed. Errors: " + " | ".join(errors)
        )


# Singleton
ai_manager = AIManager()
