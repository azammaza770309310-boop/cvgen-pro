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
from app.core.config import settings
from app.core.exceptions import (
    AIAllProvidersFailedError,
    AIInvalidKeyError,
    AIProviderError,
    AIProviderNotConfiguredError,
    AIQuotaExceededError,
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
}


class AIManager:
    """Selects and runs the configured cloud AI provider with failover.

    Keys come from BOTH environment variables AND the file-based key store
    (added via the website UI). The manager merges them at runtime and
    rotates through all available keys when one fails (429/500/etc).
    """

    def __init__(self):
        self._primary = settings.default_ai_provider.lower()
        self._backup = settings.backup_ai_provider.lower()

    # ------------------------------------------------------------------
    # Metadata for frontend
    # ------------------------------------------------------------------

    def list_providers(self) -> list[dict]:
        out = []
        for pid, meta in PROVIDER_META.items():
            # Merge env keys + file keys
            keys = self._get_all_keys(pid)
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

    def _get_all_keys(self, provider: str) -> list[str]:
        """Get all keys for a provider: env vars + file store (UI-added)."""
        # Env keys
        env_keys = settings.get_provider_keys(provider)
        if env_keys is None:
            env_keys = []
        # File keys (added via website UI)
        try:
            from app.services.key_store import get_keys_for_provider
            file_keys = get_keys_for_provider(provider)
            if file_keys is None:
                file_keys = []
        except Exception:
            file_keys = []
        # Merge + deduplicate
        seen = set()
        all_keys = []
        for k in env_keys + file_keys:
            if k and k not in seen:
                seen.add(k)
                all_keys.append(k)
        return all_keys

    def is_configured(self, provider: str) -> bool:
        return len(self._get_all_keys(provider)) > 0

    # ------------------------------------------------------------------
    # Provider instantiation
    # ------------------------------------------------------------------

    def _instantiate(self, provider: str) -> AIProvider:
        pid = provider.lower()
        cls = PROVIDER_CLASSES.get(pid)
        if not cls:
            raise AIProviderNotConfiguredError(f"Unknown provider: {provider}")
        keys = self._get_all_keys(pid)
        if not keys:
            raise AIProviderNotConfiguredError(
                f"Provider '{pid}' has no API key configured. "
                f"Add a key via the Settings page or set the environment variable."
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

    async def translate_json(self, system: str, user: str, provider: str = "") -> str:
        """Generic JSON-in/JSON-out call used by the bilingual sync service.

        Reuses the failover engine. Providers implement `translate_json` as a
        thin wrapper around their raw _generate call with JSON mode enabled.
        """
        return await self._run_with_failover(
            "translate_json", provider=provider or self._primary, args=(system, user), kwargs={}
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
        # Track the most informative error type for the final message.
        last_invalid_key: str | None = None
        last_quota_error: str | None = None
        last_other_error: str | None = None
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
            except AIInvalidKeyError as e:
                # Invalid key — try next provider (it has a different key).
                errors.append(f"{pid}: {e.message}")
                last_invalid_key = e.message
                logger.warning("AI provider '%s' invalid key: %s", pid, e.message)
                continue
            except AIQuotaExceededError as e:
                # Quota/rate limit — try next provider. The key is VALID.
                errors.append(f"{pid}: {e.message}")
                last_quota_error = e.message
                logger.warning("AI provider '%s' quota exceeded: %s", pid, e.message)
                continue
            except AIProviderError as e:
                errors.append(f"{pid}: {e.message}")
                last_other_error = e.message
                logger.warning("AI provider '%s' failed: %s", pid, e.message)
                continue
            except Exception as e:  # noqa: BLE001
                errors.append(f"{pid}: {type(e).__name__}: {e}")
                last_other_error = f"{type(e).__name__}: {e}"
                logger.exception("Unexpected error from provider '%s'", pid)
                continue

        # Build the clearest possible final error message.
        # Priority: quota > invalid key > other — because if ANY provider said
        # 'quota exceeded', the user's keys are valid and the issue is just
        # rate limits, which is more actionable than 'invalid key'.
        if last_quota_error and not last_invalid_key:
            # All providers hit quota — keys are valid.
            raise AIAllProvidersFailedError(
                "All configured AI providers hit their quota/rate limit. "
                "Your API keys are valid — please wait and retry, or add a "
                "provider with available quota. Details: " + " | ".join(errors)
            )
        if last_invalid_key and not last_quota_error:
            raise AIAllProvidersFailedError(
                "All configured AI providers rejected the API key as invalid. "
                "Please verify your API keys in Settings. Details: " + " | ".join(errors)
            )
        if last_invalid_key and last_quota_error:
            # Mixed: some keys invalid, others quota'd. Report both clearly.
            raise AIAllProvidersFailedError(
                "AI providers failed — some keys are invalid, others hit quota. "
                "Please verify your API keys and check quota limits. "
                "Details: " + " | ".join(errors)
            )
        raise AIAllProvidersFailedError(
            "All configured AI providers failed. Errors: " + " | ".join(errors)
        )


# Singleton
ai_manager = AIManager()
