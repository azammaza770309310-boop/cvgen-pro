"""Export API routes — PDF and DOCX.

PDF supports two engines via the `engine` query parameter:
  - `weasyprint` (default): server-side HTML/CSS→PDF, no browser dependency
  - `chromium`: uses Playwright/Chromium print-to-PDF for exact preview parity
"""
from __future__ import annotations

import logging
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.schemas.export import ExportRequest
from app.services.docx_service import export_docx
from app.services.pdf_service import export_pdf
from app.services.resume_normalizer import normalize_resume_data

logger = logging.getLogger("cvgen.api.export")

router = APIRouter(prefix="/api/export", tags=["export"])


def _safe_filename(name: str, ext: str) -> str:
    base = (name or "resume").strip().replace(" ", "_") or "resume"
    keep = "".join(c for c in base if c.isalnum() or c in "_-")
    if not keep:
        keep = "resume"
    return f"{keep}.{ext}"


@router.post("/pdf")
async def export_pdf_route(req: ExportRequest, engine: str = Query("weasyprint", pattern="^(weasyprint|chromium)$")):
    try:
        resume = normalize_resume_data(req.data)
        if req.template_id:
            resume.template_id = req.template_id
        if req.lang:
            resume.lang = req.lang

        if engine == "chromium":
            from app.services.chromium_pdf_service import export_pdf_chromium
            pdf_bytes = export_pdf_chromium(resume, req.template_id)
        else:
            pdf_bytes = export_pdf(resume, req.template_id)

        filename = _safe_filename(req.filename or resume.personal.name or "resume", "pdf")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
        )
    except Exception as e:
        logger.exception("PDF export failed")
        raise HTTPException(status_code=500, detail=f"PDF export failed: {e}")


@router.post("/page-count")
async def get_page_count(req: ExportRequest, engine: str = Query("chromium", pattern="^(weasyprint|chromium)$")):
    """Return the TRUE page count by actually rendering the PDF.

    This is the authoritative page count — the browser DOM estimate is only
    an approximation. Use this endpoint when exact parity is required.
    """
    try:
        resume = normalize_resume_data(req.data)
        if req.template_id:
            resume.template_id = req.template_id
        if req.lang:
            resume.lang = req.lang

        import io
        import pypdf

        if engine == "chromium":
            from app.services.chromium_pdf_service import export_pdf_chromium
            pdf_bytes = export_pdf_chromium(resume, req.template_id)
        else:
            pdf_bytes = export_pdf(resume, req.template_id)

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        return {"page_count": len(reader.pages), "engine": engine}
    except Exception as e:
        logger.exception("Page count failed")
        raise HTTPException(status_code=500, detail=f"Page count failed: {e}")


@router.post("/docx")
async def export_docx_route(req: ExportRequest):
    try:
        resume = normalize_resume_data(req.data)
        if req.lang:
            resume.lang = req.lang
        docx_bytes = export_docx(resume)
        filename = _safe_filename(req.filename or resume.personal.name or "resume", "docx")
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
        )
    except Exception as e:
        logger.exception("DOCX export failed")
        raise HTTPException(status_code=500, detail=f"DOCX export failed: {e}")
