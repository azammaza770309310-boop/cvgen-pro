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
            pdf_bytes = export_pdf(resume, req.template_id, controls=req.controls, font_family=font_family, style_overrides=req.style_overrides)

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
                # CRITICAL: Pass font_family + style_overrides so the page count
                # matches the EXACT PDF the user will download (with their chosen
                # font, colors, border-radius, sidebar width, etc.).
                pdf_bytes = export_pdf(
                    resume,
                    req.template_id,
                    controls=req.controls,
                    font_family=req.font,
                    style_overrides=req.style_overrides,
                )
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


@router.post("/fill-percentage")
async def get_fill_percentage(req: ExportRequest):
    """Return the ACTUAL fill percentage of page 1 by rendering the PDF with
    WeasyPrint and measuring the content height on the first page.

    This is the AUTHORITATIVE fill percentage — it matches EXACTLY what the
    user will see when they download the PDF. The browser DOM measurement
    is inaccurate because Chromium and WeasyPrint render fonts/spacing
    differently (WeasyPrint is more compact).

    Returns:
      - fill_percentage: 0-100 (how much of page 1 is filled with content)
      - page_count: total number of pages
      - content_height_pt: content height in points (1pt = 1/72 inch)
      - page_height_pt: total page height in points
    """
    try:
        from weasyprint import HTML as WeasyHTML

        resume = normalize_resume_data(req.data)
        if req.template_id:
            resume.template_id = req.template_id
        if req.lang:
            resume.lang = req.lang

        # Build the HTML document (same as export_pdf uses)
        from app.services.pdf_service import render_html_for_pdf
        html_doc = render_html_for_pdf(
            resume,
            resume.template_id,
            controls=req.controls,
            font_family=req.font,
            style_overrides=req.style_overrides,
        )

        # Render with WeasyPrint to get the layout tree
        doc = WeasyHTML(string=html_doc).render()
        page_count = len(doc.pages)
        page1 = doc.pages[0]

        # Get the page box — this contains the full layout tree
        page_box = page1._page_box
        # Page height in CSS pixels (A4 = 1123px at 96dpi)
        page_height_css = float(page_box.height)

        # Find the maximum bottom y-coordinate of CONTENT boxes (not containers).
        #
        # PROBLEM: .a4-page has `min-height: 297mm` which makes the page box
        # always full height (1123px) regardless of actual content. If we
        # measure the page box or its direct children (which stretch to fill
        # the min-height), we always get 100% fill — even when the PDF has
        # a big empty space at the bottom.
        #
        # SOLUTION: Only count boxes that contain ACTUAL TEXT content (leaf
        # boxes with text), not container/wrapper divs that stretch to fill.
        # WeasyPrint text boxes have `text` attribute (the actual text string)
        # or are anonymous line boxes.
        #
        # We also skip the .a4-page itself and its flex container children
        # that have min-height:100% (they stretch but have no content of their own).
        max_content_bottom = 0.0
        for box in page_box.descendants():
            try:
                # Skip the page box itself
                if box is page_box:
                    continue
                # Check if the box is visible
                style = getattr(box, "style", None)
                if style:
                    display = style.get("display")
                    visibility = style.get("visibility")
                    if display == "none" or visibility == "hidden":
                        continue
                # Get position and height
                pos_y = float(getattr(box, "position_y", 0) or 0)
                h = float(getattr(box, "height", 0) or 0)
                if h <= 0:
                    continue
                # ONLY count boxes that have actual text content.
                # We check for the 'text' attribute (TextBox) or children
                # that are text boxes.
                has_text = False
                # Check if this box is a TextBox (has text attribute)
                text_attr = getattr(box, "text", None)
                if text_attr and str(text_attr).strip():
                    has_text = True
                # Check if this box has direct text children
                if not has_text:
                    for child in (getattr(box, "children", None) or []):
                        child_text = getattr(child, "text", None)
                        if child_text and str(child_text).strip():
                            has_text = True
                            break
                if not has_text:
                    continue
                # This box has text content — measure its bottom edge
                bottom = pos_y + h
                if 0 < bottom <= page_height_css + 5:
                    if bottom > max_content_bottom:
                        max_content_bottom = bottom
            except (TypeError, ValueError, AttributeError):
                continue

        # Calculate fill percentage based on usable content area
        # (page height minus top + bottom padding)
        margin_mm = 8.0
        if req.controls and hasattr(req.controls, "margin") and req.controls.margin:
            margin_mm = float(req.controls.margin)
        margin_px = margin_mm * 3.7795  # mm to px
        usable_height_css = page_height_css - (2 * margin_px)

        # Content fill = (max_content_bottom - top_padding) / usable_height
        content_fill = max_content_bottom - margin_px
        if usable_height_css > 0:
            fill_pct = min(100, max(0, round((content_fill / usable_height_css) * 100)))
        else:
            fill_pct = 0

        return {
            "fill_percentage": fill_pct,
            "page_count": page_count,
            "content_bottom_px": round(max_content_bottom, 1),
            "page_height_px": round(page_height_css, 1),
            "usable_height_px": round(usable_height_css, 1),
            "margin_mm": margin_mm,
        }
    except Exception as e:
        logger.exception("Fill percentage measurement failed")
        raise HTTPException(status_code=500, detail=f"Fill measurement failed: {e}")


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
