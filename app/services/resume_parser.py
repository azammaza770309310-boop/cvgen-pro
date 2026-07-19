"""Resume parser — CLOUD AI ONLY.

This module performs NO local semantic parsing. The entire raw CV document is
sent to the configured cloud AI provider, which returns structured JSON. That
JSON is then validated and normalized by `normalize_resume_data()`.

Regex is used ONLY for basic contact validation (email/phone/URL format) inside
the normalizer — NEVER for section classification, experience grouping, skill
detection, or any other semantic understanding.

If no AI API key is configured, a clear user-facing error is raised. There is
NO silent fallback to local parsing.
"""
from __future__ import annotations

import logging
import re

from app.ai.manager import ai_manager
from app.core.exceptions import (
    AIAllProvidersFailedError,
    AIProviderNotConfiguredError,
)
from app.models.resume import ResumeData
from app.services.resume_normalizer import normalize_resume_data
from app.utils.arabic import detect_lang

logger = logging.getLogger("cvgen.parser")


def clean_text(raw: str) -> str:
    """Light text cleaning only — no semantic processing."""
    if not raw:
        return ""
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


async def parse_resume_ai(text: str, provider: str = "", lang: str = "auto") -> ResumeData:
    """Parse a raw CV using the cloud AI provider (whole-document).

    Raises AIProviderNotConfiguredError if no AI key is configured.
    Raises AIAllProvidersFailedError if all configured providers fail.
    There is NO local semantic fallback.
    """
    text = clean_text(text)
    if not text:
        raise AIProviderNotConfiguredError("No resume text provided.")

    # Determine if ANY provider is configured
    configured = [p["id"] for p in ai_manager.list_providers() if p["configured"]]
    if not configured:
        raise AIProviderNotConfiguredError(
            "AI API key is required to parse your resume. "
            "Please configure an AI provider in Settings."
        )

    detected_lang = lang if lang != "auto" else detect_lang(text)

    # Whole-document AI parse — no fragmentation
    raw = await ai_manager.parse_resume(text, provider=provider, lang=detected_lang)

    # Normalize: Pydantic validation + contact validation + dedup
    # (the normalizer uses regex ONLY for email/phone/URL validation, not semantics)
    return normalize_resume_data(raw, full_text=text)
