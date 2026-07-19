"""Templates API routes — dynamic registry discovery."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.template_service import (
    get_template_count,
    list_categories,
    list_templates,
    render_template,
)

router = APIRouter(prefix="/api/templates", tags=["templates"])


class RenderRequest(BaseModel):
    data: dict
    template_id: str = "ats_classic"


@router.get("/")
async def get_templates():
    """List ALL templates + dynamic count + categories.

    The count is ALWAYS computed from the registry — never hardcoded.
    """
    return {
        "templates": list_templates(),
        "count": get_template_count(),
        "categories": list_categories(),
    }


@router.get("/count")
async def get_count():
    """Return only the dynamic template count."""
    return {"count": get_template_count()}


@router.post("/render")
async def render_template_route(req: RenderRequest):
    """Render a resume into HTML for preview/thumbnail/PDF."""
    from app.services.resume_normalizer import normalize_resume_data
    resume = normalize_resume_data(req.data)
    if req.template_id:
        resume.template_id = req.template_id
    html = render_template(req.template_id, resume)
    return {"html": html}
