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

    Pipeline:
        Raw text → AI extraction (EN + AR) → normalize → bilingual sync
        (translate any missing Arabic via cloud AI) → validate 1:1 → return

    English text is NEVER copied into Arabic fields. When Arabic content is
    missing or incomplete, a second AI call translates it for real.

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
    resume = normalize_resume_data(raw, full_text=text)

    # Bilingual sync — translate any missing Arabic content via the cloud AI.
    # This is the "Bilingual Translation / Synchronization" step. It does NOT
    # copy English into Arabic; it generates REAL Arabic translations.
    from app.ai.bilingual_sync import sync_bilingual, validate_bilingual_match
    try:
        resume = await sync_bilingual(resume, provider=provider)
    except (AIProviderNotConfiguredError, AIAllProvidersFailedError) as e:
        # Translation sync failed, but we still return the parsed resume.
        # Arabic fields that are empty will simply not render in the Arabic
        # column — English is NEVER silently copied in. Log the warning.
        logger.warning("Bilingual sync skipped: %s", getattr(e, "message", str(e)))

    # Validate 1:1 match (informational — logged, not fatal)
    problems = validate_bilingual_match(resume)
    if problems:
        logger.info("Bilingual 1:1 validation notes: %s", "; ".join(problems))

    return resume
