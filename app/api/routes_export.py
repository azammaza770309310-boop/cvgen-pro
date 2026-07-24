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
from pydantic import BaseModel

from app.schemas.export import ExportRequest
from app.services.docx_service import export_docx
from app.services.pdf_service import export_pdf, _load_css
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

        # Determine the font family to use for PDF (from req.font or controls.fontFamily)
        font_family = req.font
        if not font_family and req.controls and hasattr(req.controls, "fontFamily") and req.controls.fontFamily:
            font_family = req.controls.fontFamily

        if engine == "chromium":
            from app.services.chromium_pdf_service import export_pdf_chromium
            pdf_bytes = export_pdf_chromium(resume, req.template_id, controls=req.controls)
        else:
            pdf_bytes = export_pdf(resume, req.template_id, controls=req.controls, font_family=font_family)

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

    Error handling distinguishes between:
      - pypdf not installed (deployment misconfiguration → 500 with clear message)
      - PDF generation failure (engine error → 500)
      - PDF parsing failure (corrupt bytes → 500)
    """
    # Import pypdf at the top of the function with a clear error if missing.
    # This is a required production dependency (listed in requirements.txt).
    try:
        import io
        import pypdf
    except ImportError:
        logger.error("pypdf is not installed — add it to requirements.txt")
        raise HTTPException(
            status_code=500,
            detail="PDF page count is unavailable: the 'pypdf' package is not installed. "
                   "It is listed in requirements.txt — verify the production build installs it.",
        )

    try:
        resume = normalize_resume_data(req.data)
        if req.template_id:
            resume.template_id = req.template_id
        if req.lang:
            resume.lang = req.lang

        # Render the PDF using the requested engine.
        try:
            if engine == "chromium":
                from app.services.chromium_pdf_service import export_pdf_chromium
                pdf_bytes = export_pdf_chromium(resume, req.template_id, controls=req.controls)
            else:
                pdf_bytes = export_pdf(resume, req.template_id, controls=req.controls)
        except Exception as render_err:
            logger.exception("PDF rendering failed during page-count")
            raise HTTPException(
                status_code=500,
                detail=f"PDF rendering failed ({engine}): {render_err}",
            )

        if not pdf_bytes or len(pdf_bytes) == 0:
            logger.error("PDF engine returned empty bytes for page-count")
            raise HTTPException(
                status_code=500,
                detail=f"PDF engine '{engine}' returned empty output.",
            )

        # Count pages from the rendered bytes.
        try:
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            page_count = len(reader.pages)
        except Exception as parse_err:
            logger.exception("Failed to parse rendered PDF for page count")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to read page count from rendered PDF: {parse_err}",
            )

        return {"page_count": page_count, "engine": engine}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in page-count")
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


# ---------------------------------------------------------------------------
# PDF FROM PREVIEW HTML — renders the EXACT HTML from the preview DOM
# This guarantees 1:1 match between what the user sees and what gets exported.
# ---------------------------------------------------------------------------

class PdfFromHtmlRequest(BaseModel):
    """Takes the actual HTML from #a4Content + design vars + font, renders PDF."""
    html: str            # The inner HTML of #a4Content (the resume content)
    css_vars: str = ""   # CSS variable overrides (from applyDesignVars)
    font_family: str = ""
    filename: str = "resume"


@router.post("/pdf-from-html")
async def export_pdf_from_html(req: PdfFromHtmlRequest):
    """Render PDF from the EXACT preview HTML — guarantees 1:1 match.

    The frontend sends the actual DOM HTML from #a4Content (after all inline
    edits), plus the CSS variables and font family. WeasyPrint renders THAT
    exact HTML, so the PDF is identical to what the user sees in the preview.
    """
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration

        css = _load_css()
        font_link = ""
        if req.font_family:
            ff = req.font_family.replace(" ", "+")
            font_link = f'<link href="https://fonts.googleapis.com/css2?family={ff}:wght@400;500;600;700&display=swap" rel="stylesheet">'

        # Build the full HTML document — uses the EXACT content from the preview
        html_doc = f"""<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
<meta charset="utf-8">
<title>Resume</title>
{font_link}
<style>
{css}
{req.css_vars}
/* Apply font family to ALL elements */
body, .a4-page, .cv-root, .section, .section-row, .section-body,
.section-headings, .section-heading-en, .section-heading-ar,
.body-en, .body-ar, .item, .item-title, .contact-bar, .contact-item,
.editable, p, li, h1, h2, h3, span, div {{
  font-family: '{req.font_family}', Arial, sans-serif;
}}
/* PDF page setup */
@page {{
  size: A4;
  margin: 0;
}}
.a4-page {{
  width: 210mm;
  min-height: 297mm;
  max-height: 297mm;
  overflow: hidden;
  box-sizing: border-box;
}}
</style>
</head>
<body>
<div class="a4-page" id="resume-document">
{req.html}
</div>
</body>
</html>"""

        font_config = FontConfiguration()
        pdf_bytes = HTML(string=html_doc).write_pdf(font_config=font_config)
        filename = _safe_filename(req.filename, "pdf")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
        )
    except Exception as e:
        logger.exception("PDF-from-HTML export failed")
        raise HTTPException(status_code=500, detail=f"PDF export failed: {e}")
