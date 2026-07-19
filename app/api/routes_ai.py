"""AI API routes — parse, improve, summary, cover letter.

All semantic processing is cloud-AI-only. When no API key is configured, these
endpoints return a structured error with code 'ai_provider_not_configured' so
the frontend can show a clear message and direct the user to Settings.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel

from app.ai.manager import ai_manager
from app.core.exceptions import (
    AIAllProvidersFailedError,
    AIProviderNotConfiguredError,
)

logger = logging.getLogger("cvgen.api.ai")

router = APIRouter(prefix="/api/ai", tags=["ai"])


class AIParseRequest(BaseModel):
    text: str
    provider: str = ""
    lang: str = "auto"


class AIImproveRequest(BaseModel):
    section: str
    content: str
    provider: str = ""
    lang: str = "en"


class AISummaryRequest(BaseModel):
    role: str = ""
    experience_years: int = 0
    skills: list[str] = []
    provider: str = ""
    lang: str = "en"


class AICoverLetterRequest(BaseModel):
    data: dict
    job_description: str = ""
    provider: str = ""


NOT_CONFIGURED_MSG = (
    "AI API key is required to parse your resume. "
    "Please configure an AI provider in Settings."
)


@router.post("/parse")
async def ai_parse(req: AIParseRequest):
    """Parse raw CV text using cloud AI (whole-document).

    Returns success=false with a clear error code when no AI key is configured.
    NO local semantic fallback.
    """
    if not req.text.strip():
        return {"success": False, "error": "No text provided.", "code": "empty_text"}

    # Check if ANY provider is configured
    configured = [p["id"] for p in ai_manager.list_providers() if p["configured"]]
    if not configured:
        return {
            "success": False,
            "error": NOT_CONFIGURED_MSG,
            "code": "ai_provider_not_configured",
        }

    try:
        from app.services.resume_parser import parse_resume_ai
        resume = await parse_resume_ai(req.text, provider=req.provider, lang=req.lang)
        return {"success": True, "data": resume.model_dump()}
    except AIProviderNotConfiguredError as e:
        return {"success": False, "error": e.message or NOT_CONFIGURED_MSG, "code": e.code}
    except AIAllProvidersFailedError as e:
        return {"success": False, "error": e.message, "code": e.code}


@router.post("/improve")
async def ai_improve(req: AIImproveRequest):
    if not any(p["configured"] for p in ai_manager.list_providers()):
        return {"success": False, "error": NOT_CONFIGURED_MSG, "code": "ai_provider_not_configured"}
    try:
        result = await ai_manager.improve_resume(req.section, req.content, provider=req.provider, lang=req.lang)
        return {"success": True, "content": result}
    except AIProviderNotConfiguredError:
        return {"success": False, "error": NOT_CONFIGURED_MSG, "code": "ai_provider_not_configured"}
    except AIAllProvidersFailedError as e:
        return {"success": False, "error": e.message, "code": e.code}


@router.post("/summary")
async def ai_summary(req: AISummaryRequest):
    if not any(p["configured"] for p in ai_manager.list_providers()):
        return {"success": False, "error": NOT_CONFIGURED_MSG, "code": "ai_provider_not_configured"}
    try:
        result = await ai_manager.generate_summary(req.role, req.experience_years, req.skills, provider=req.provider, lang=req.lang)
        return {"success": True, "summary": result}
    except AIProviderNotConfiguredError:
        return {"success": False, "error": NOT_CONFIGURED_MSG, "code": "ai_provider_not_configured"}
    except AIAllProvidersFailedError as e:
        return {"success": False, "error": e.message, "code": e.code}


@router.post("/cover-letter")
async def ai_cover_letter(req: AICoverLetterRequest):
    if not any(p["configured"] for p in ai_manager.list_providers()):
        return {"success": False, "error": NOT_CONFIGURED_MSG, "code": "ai_provider_not_configured"}
    try:
        result = await ai_manager.generate_cover_letter(req.data, req.job_description, provider=req.provider)
        return {"success": True, "content": result}
    except AIProviderNotConfiguredError:
        return {"success": False, "error": NOT_CONFIGURED_MSG, "code": "ai_provider_not_configured"}
    except AIAllProvidersFailedError as e:
        return {"success": False, "error": e.message, "code": e.code}
