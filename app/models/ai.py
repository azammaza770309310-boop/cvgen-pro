"""AI-related models (provider metadata, parse requests/responses)."""
from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ProviderInfo(BaseModel):
    """Safe provider metadata returned to the frontend — never the key."""
    id: str
    name: str
    configured: bool
    enabled: bool = True
    has_backup: bool = False
    website: str = ""
    description: str = ""


class AIParseRequest(BaseModel):
    text: str
    provider: str = "gemini"
    lang: str = "auto"  # auto | en | ar | bilingual


class AIParseResponse(BaseModel):
    success: bool
    provider: str
    data: Optional[dict] = None
    error: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class AIImproveRequest(BaseModel):
    section: str
    content: str
    provider: str = "gemini"
    lang: str = "en"


class AISummaryRequest(BaseModel):
    role: str = ""
    experience_years: int = 0
    skills: List[str] = Field(default_factory=list)
    provider: str = "gemini"
    lang: str = "en"
