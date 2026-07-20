"""Chromium-based PDF export via Playwright — uses the same rendering engine
as the browser preview, guaranteeing exact visual + page-count parity.

This is the PREFERRED PDF pipeline when pixel-perfect preview parity is required.
The WeasyPrint pipeline remains as a fallback for environments without Chromium.
"""
from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

from app.models.resume import ResumeData
from app.services.resume_normalizer import normalize_resume_data
from app.services.template_service import render_template

logger = logging.getLogger("cvgen.chromium_pdf")

# CSS for the Chromium PDF context (same as preview + @page rules)
_CHROMIUM_CSS = """
@page { size: A4; margin: 10mm; }
.cv-root { box-sizing: border-box; }
.break-inside-avoid { break-inside: avoid; }
"""


def _load_template_css() -> str:
    css_path = Path(__file__).resolve().parent.parent / "static" / "css" / "templates.css"
    if css_path.exists():
        return css_path.read_text(encoding="utf-8")
    return ""


def render_html_for_chromium_pdf(resume: ResumeData, template_id: str | None = None) -> str:
    """Build the full HTML document for Chromium print-to-PDF.

    CRITICAL: <html> must ALWAYS be dir="ltr" for the official bilingual template.
    """
    tid = template_id or resume.template_id or "official_bilingual_master"
    body = render_template(tid, resume)
    css = _load_template_css()
    return f"""<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
<meta charset="utf-8">
<title>Resume</title>
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&family=Cairo:wght@400;600;700&family=Amiri:wght@400;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
{css}
{_CHROMIUM_CSS}
</style>
</head>
<body>
{body}
</body>
</html>"""


def export_pdf_chromium(resume_data: ResumeData | dict, template_id: str | None = None) -> bytes:
    """Generate a PDF using Chromium's print-to-PDF — exact parity with browser preview.

    Falls back to WeasyPrint if Playwright/Chromium is not available.
    """
    if isinstance(resume_data, dict):
        resume = normalize_resume_data(resume_data)
    else:
        resume = resume_data
    if template_id:
        resume.template_id = template_id

    html_doc = render_html_for_chromium_pdf(resume, resume.template_id)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("Playwright not available — falling back to WeasyPrint")
        from app.services.pdf_service import export_pdf
        return export_pdf(resume, template_id)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html_doc, wait_until="networkidle")
            page.evaluate("document.fonts.ready")
            # Exact config from spec: preferCSSPageSize + zero margins
            pdf_bytes = page.pdf(
                format="A4",
                print_background=True,
                prefer_css_page_size=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                display_header_footer=False,
            )
            browser.close()
        return pdf_bytes
    except Exception as e:
        logger.warning("Chromium PDF failed (%s) — falling back to WeasyPrint", e)
        from app.services.pdf_service import export_pdf
        return export_pdf(resume, template_id)
