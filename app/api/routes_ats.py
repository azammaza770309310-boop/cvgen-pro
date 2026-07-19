"""ATS API routes."""
from __future__ import annotations

from fastapi import APIRouter

from app.models.resume import ResumeData
from app.schemas.ats import ATSRequest, ATSResponse
from app.services.ats_service import analyze_resume

router = APIRouter(prefix="/api/ats", tags=["ats"])


@router.post("/analyze", response_model=ATSResponse)
async def ats_analyze(req: ATSRequest):
    from app.services.resume_normalizer import normalize_resume_data
    resume = normalize_resume_data(req.data)
    result = await analyze_resume(resume, req.job_description, req.use_ai, req.provider)
    return result
