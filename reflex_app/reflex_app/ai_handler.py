"""AI parsing handler — native Reflex integration (no FastAPI needed).

This module imports the AI providers directly from app.ai.* (which are
FastAPI-independent — they use httpx, not FastAPI). The Reflex state calls
these functions via async/await to parse resumes and translate missing
Arabic content.

Single Source of Truth: the AI logic lives in app/ai/ and is shared by
both the FastAPI backend (when running standalone) and the Reflex frontend
(when running in production). No duplication.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("cvgen.reflex.ai")


async def parse_resume(text: str, provider: str = "", lang: str = "auto") -> dict:
    """Parse raw resume text using the cloud AI (Gemini by default).

    Returns a dict with:
      - success: bool
      - data: structured resume dict (on success)
      - error: str (on failure)
      - code: str (error code on failure)
    """
    if not text or not text.strip():
        return {"success": False, "error": "No text provided", "code": "empty_text"}

    try:
        from app.ai.manager import ai_manager
        from app.services.resume_parser import parse_resume_ai
        from app.core.exceptions import AIProviderNotConfiguredError, AIAllProvidersFailedError

        # Check if any provider is configured
        configured = [p["id"] for p in ai_manager.list_providers() if p["configured"]]
        if not configured:
            return {
                "success": False,
                "error": "AI API key is required. Please configure an AI provider in Settings.",
                "code": "ai_provider_not_configured",
            }

        resume = await parse_resume_ai(text, provider=provider, lang=lang)
        return {"success": True, "data": resume.model_dump()}
    except AIProviderNotConfiguredError as e:
        return {"success": False, "error": e.message, "code": e.code}
    except AIAllProvidersFailedError as e:
        return {"success": False, "error": e.message, "code": e.code}
    except Exception as e:
        logger.exception("AI parse error")
        return {"success": False, "error": str(e), "code": "unknown"}


def list_providers() -> list[dict]:
    """Return the list of configured AI providers (safe metadata, no keys)."""
    try:
        from app.ai.manager import ai_manager
        return ai_manager.list_providers()
    except Exception as e:
        logger.warning("list_providers failed: %s", e)
        return []


def is_any_provider_configured() -> bool:
    """Return True if at least one AI provider has a key configured."""
    try:
        from app.ai.manager import ai_manager
        return any(p["configured"] for p in ai_manager.list_providers())
    except Exception:
        return False


async def improve_section(section: str, content: str, provider: str = "", lang: str = "en") -> dict:
    """Improve a section of text via AI."""
    try:
        from app.ai.manager import ai_manager
        from app.core.exceptions import AIProviderNotConfiguredError, AIAllProvidersFailedError
        if not is_any_provider_configured():
            return {"success": False, "error": "AI not configured", "code": "ai_provider_not_configured"}
        result = await ai_manager.improve_resume(section, content, provider=provider, lang=lang)
        return {"success": True, "content": result}
    except (AIProviderNotConfiguredError, AIAllProvidersFailedError) as e:
        return {"success": False, "error": e.message, "code": e.code}
    except Exception as e:
        return {"success": False, "error": str(e), "code": "unknown"}
