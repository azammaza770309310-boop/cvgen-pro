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


def _build_design_vars_css(controls=None, font_family=None) -> str:
    """Build CSS variable overrides from design controls (font_size, etc.).

    This ensures the PDF matches what the user sees in the preview, where they
    may have adjusted the font size, line height, spacing, etc. via the steppers.
    Also applies the font family selected by the user.
    """
    overrides = []
    # Font family override (applied to body + all text)
    ff = font_family
    if not ff and controls and hasattr(controls, "fontFamily") and controls.fontFamily:
        ff = controls.fontFamily
    # Map the frontend control names to CSS variable names
    if controls:
        if hasattr(controls, "fontSize") and controls.fontSize:
            overrides.append(f"--cv-body-size: {controls.fontSize}pt")
        if hasattr(controls, "lineHeight") and controls.lineHeight:
            overrides.append(f"--cv-body-line-height: {controls.lineHeight}")
        if hasattr(controls, "sectionSpacing") and controls.sectionSpacing is not None:
            overrides.append(f"--cv-section-spacing: {controls.sectionSpacing}pt")
        if hasattr(controls, "columnDistance") and controls.columnDistance is not None:
            overrides.append(f"--cv-column-gap: {controls.columnDistance}pt")
        if hasattr(controls, "margin") and controls.margin:
            overrides.append(f"--cv-page-padding: {controls.margin}mm")
    if not overrides and not ff:
        return ""
    parts = []
    if overrides:
        parts.append(":root {\n  " + ";\n  ".join(overrides) + ";\n}")
    if ff:
        # Apply font family to ALL text elements + load from Google Fonts
        parts.append(f"""body, .a4-page, .cv-root, .section, .section-row, .section-body,
.section-headings, .section-heading-en, .section-heading-ar,
.body-en, .body-ar, .item, .item-title, .contact-bar, .contact-item,
.editable, p, li, h1, h2, h3, span, div {{
  font-family: '{ff}', Arial, sans-serif !important;
}}""")
    return "\n".join(parts) + "\n"


def render_html_for_pdf(resume: ResumeData, template_id: str | None = None, controls=None, font_family=None) -> str:
    """Build the full HTML document (with embedded CSS) for a resume.

    CRITICAL: The <html> tag must ALWAYS be dir="ltr" for the official bilingual
    template. The template uses direction:ltr on .obm-columns to keep English
    on the left and Arabic on the right. If we set dir="rtl" on <html>, it
    flips the entire layout and swaps the columns.

    The `controls` parameter (DesignControls) injects the user's design
    adjustments (font_size, line_height, spacing, etc.) as CSS variables so
    the PDF matches the preview exactly.
    The `font_family` parameter applies the user's selected font to all text.
    """
    tid = template_id or resume.template_id or "official_bilingual_master"
    body = render_template(tid, resume)
    css = _load_css()
    design_vars = _build_design_vars_css(controls, font_family)
    # Build Google Fonts link if a font is specified
    google_fonts_link = ""
    if font_family:
        # Common Arabic + Latin fonts available on Google Fonts
        google_fonts_link = f'<link href="https://fonts.googleapis.com/css2?family={font_family.replace(" ", "+")}:wght@400;500;600;700&display=swap" rel="stylesheet">'
    # ALWAYS use dir="ltr" for the official bilingual template
    # The Arabic column has its own dir="rtl" attribute internally
    html_doc = f"""<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
<meta charset="utf-8">
<title>Resume</title>
{google_fonts_link}
<style>
{css}
{design_vars}
/* PDF page setup — zero margins, CSS handles padding */
@page {{
  size: A4;
  margin: 0;
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


def export_pdf(resume_data: ResumeData | dict, template_id: str | None = None, controls=None, font_family=None) -> bytes:
    """Generate a PDF from ResumeData (or a raw dict that gets normalized).

    The `controls` parameter (DesignControls) injects the user's design
    adjustments so the PDF matches the preview.
    The `font_family` parameter applies the user's selected font.
    """
    if isinstance(resume_data, dict):
        resume = normalize_resume_data(resume_data)
    else:
        resume = resume_data
    if template_id:
        resume.template_id = template_id
    html_doc = render_html_for_pdf(resume, resume.template_id, controls=controls, font_family=font_family)
    font_config = FontConfiguration()
    pdf = HTML(string=html_doc).write_pdf(font_config=font_config)
    return pdf
