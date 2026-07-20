"""PDF export service — WeasyPrint.

Uses the SAME template renderer as the live preview, so PDF visually matches.
Pipeline: ResumeData → template_service.render_template → HTML → CSS → WeasyPrint → PDF
"""
from __future__ import annotations

import logging
from pathlib import Path

from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

from app.core.config import settings
from app.models.resume import ResumeData
from app.services.resume_normalizer import normalize_resume_data
from app.services.template_service import render_template

logger = logging.getLogger("cvgen.pdf")


def _load_css() -> str:
    css_path = settings.static_dir / "css" / "templates.css"
    if css_path.exists():
        return css_path.read_text(encoding="utf-8")
    return ""


def render_html_for_pdf(resume: ResumeData, template_id: str | None = None) -> str:
    """Build the full HTML document (with embedded CSS) for a resume.

    CRITICAL: The <html> tag must ALWAYS be dir="ltr" for the official bilingual
    template. The template uses direction:ltr on .obm-columns to keep English
    on the left and Arabic on the right. If we set dir="rtl" on <html>, it
    flips the entire layout and swaps the columns.
    """
    tid = template_id or resume.template_id or "official_bilingual_master"
    body = render_template(tid, resume)
    css = _load_css()
    # ALWAYS use dir="ltr" for the official bilingual template
    # The Arabic column has its own dir="rtl" attribute internally
    html_doc = f"""<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
<meta charset="utf-8">
<title>Resume</title>
<style>
{css}
/* PDF page setup */
@page {{
  size: A4;
  margin: {settings.pdf_margin_top} {settings.pdf_margin_right} {settings.pdf_margin_bottom} {settings.pdf_margin_left};
}}
.cv-root {{ box-sizing: border-box; }}
.break-inside-avoid {{ break-inside: avoid; }}
</style>
</head>
<body>
{body}
</body>
</html>"""
    return html_doc


def export_pdf(resume_data: ResumeData | dict, template_id: str | None = None) -> bytes:
    """Generate a PDF from ResumeData (or a raw dict that gets normalized)."""
    if isinstance(resume_data, dict):
        resume = normalize_resume_data(resume_data)
    else:
        resume = resume_data
    if template_id:
        resume.template_id = template_id
    html_doc = render_html_for_pdf(resume, resume.template_id)
    font_config = FontConfiguration()
    pdf = HTML(string=html_doc).write_pdf(font_config=font_config)
    return pdf
