"""ATS analysis schemas."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class ATSCheck(BaseModel):
    category: str
    passed: bool
    score: int  # 0-100 contribution
    message: str
    detail: str = ""


class ATSRecommendation(BaseModel):
    priority: str  # high | medium | low
    category: str
    message: str


class ATSRequest(BaseModel):
    data: dict
    job_description: str = ""
    use_ai: bool = False
    provider: str = "gemini"


class ATSResponse(BaseModel):
    score: int  # 0-100
    grade: str  # A-F
    checks: List[ATSCheck] = Field(default_factory=list)
    recommendations: List[ATSRecommendation] = Field(default_factory=list)
    keywords_found: List[str] = Field(default_factory=list)
    keywords_missing: List[str] = Field(default_factory=list)
