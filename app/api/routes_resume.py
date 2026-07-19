"""Resume API routes — sample, normalize, save, load.

NOTE: There is NO local/deterministic parse endpoint. All semantic parsing is
performed by the cloud AI via /api/ai/parse. This module only provides sample
data, normalization of already-structured data, and draft persistence.
"""
from __future__ import annotations

import uuid
from typing import Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.resume import ResumeData, sample_resume
from app.services.resume_normalizer import normalize_resume_data

router = APIRouter(prefix="/api/resume", tags=["resume"])


class NormalizeRequest(BaseModel):
    data: dict


class SaveRequest(BaseModel):
    data: dict
    name: str = ""


# In-memory store (ready to swap for DB later)
_STORE: Dict[str, dict] = {}


@router.get("/sample")
async def get_sample(lang: str = "en"):
    """Return a sample resume for the requested language."""
    resume = sample_resume(lang if lang in ("en", "ar", "bilingual") else "en")
    return resume.model_dump()


@router.post("/normalize")
async def normalize_endpoint(req: NormalizeRequest):
    """Normalize an already-structured dict into clean ResumeData.

    This does NOT parse raw text — it only validates/cleans existing structured
    data (e.g. from the editor). For raw-text parsing, use /api/ai/parse.
    """
    resume = normalize_resume_data(req.data)
    return {"data": resume.model_dump()}


@router.post("/save")
async def save_resume(req: SaveRequest):
    """Save a resume draft (in-memory, ready for DB later)."""
    rid = str(uuid.uuid4())
    resume = normalize_resume_data(req.data)
    _STORE[rid] = {"id": rid, "name": req.name or resume.personal.name or "Untitled", "data": resume.model_dump()}
    return {"id": rid, "saved": True}


@router.get("/{rid}")
async def load_resume(rid: str):
    rec = _STORE.get(rid)
    if not rec:
        raise HTTPException(status_code=404, detail="Resume not found")
    return rec


@router.get("/")
async def list_resumes():
    return {"resumes": [{"id": r["id"], "name": r["name"]} for r in _STORE.values()]}
