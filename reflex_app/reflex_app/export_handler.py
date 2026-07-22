"""PDF/DOCX export handler — native Reflex integration (no FastAPI needed).

Imports WeasyPrint + python-docx logic directly from app.services.* (which
are FastAPI-independent). The Reflex state calls these functions to generate
file bytes, then triggers rx.download() to send them to the browser.

Single Source of Truth: the export logic lives in app/services/ and is shared
by both backends. No duplication.
"""
from __future__ import annotations

import base64
import logging

logger = logging.getLogger("cvgen.reflex.export")


def _normalize_resume_data(data: dict):
    """Normalize the raw data dict into a ResumeData model."""
    from app.services.resume_normalizer import normalize_resume_data
    return normalize_resume_data(data)


def export_pdf(data: dict, template_id: str = "official_bilingual_master", controls: dict | None = None) -> bytes:
    """Generate a PDF from resume data using WeasyPrint.

    Args:
        data: raw resume dict (personal, summary, experience, etc.)
        template_id: template to use
        controls: design controls (fontSize, lineHeight, etc.) for preview parity

    Returns:
        PDF bytes.
    """
    from app.services.pdf_service import export_pdf as _export_pdf
    from app.schemas.export import DesignControls

    resume = _normalize_resume_data(data)
    if template_id:
        resume.template_id = template_id

    design_controls = None
    if controls:
        design_controls = DesignControls(**controls)

    return _export_pdf(resume, template_id, controls=design_controls)


def export_docx(data: dict, template_id: str = "official_bilingual_master") -> bytes:
    """Generate a DOCX from resume data using python-docx."""
    from app.services.docx_service import export_docx as _export_docx

    resume = _normalize_resume_data(data)
    if template_id:
        resume.template_id = template_id
    return _export_docx(resume)


def render_template_html(data: dict, template_id: str = "official_bilingual_master") -> str:
    """Render the resume as HTML (for preview or debugging)."""
    from app.services.template_service import render_template

    resume = _normalize_resume_data(data)
    if template_id:
        resume.template_id = template_id
    return render_template(template_id, resume)


def to_data_url(file_bytes: bytes, filename: str) -> dict:
    """Convert file bytes to a download payload for rx.download().

    Returns a dict with 'data' (base64) and 'filename'.
    """
    b64 = base64.b64encode(file_bytes).decode()
    return {"data": b64, "filename": filename}


def get_page_count(data: dict, template_id: str = "official_bilingual_master", controls: dict | None = None) -> int:
    """Return the TRUE page count by rendering the PDF and counting pages."""
    import io
    import pypdf
    from app.schemas.export import DesignControls
    from app.services.pdf_service import export_pdf as _export_pdf

    pdf_bytes = export_pdf(data, template_id, controls)
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    return len(reader.pages)


# ---------------------------------------------------------------------------
# Templates — list, count, render (delegates to app.services.template_service)
# ---------------------------------------------------------------------------

def list_templates() -> list[dict]:
    """Return all available templates with metadata."""
    from app.services.template_service import list_templates as _list
    return _list()


def get_template_count() -> int:
    """Return the dynamic template count."""
    from app.services.template_service import get_template_count as _count
    return _count()


def list_categories() -> list[dict]:
    """Return template categories."""
    from app.services.template_service import list_categories as _cats
    return _cats()


def normalize_resume(data: dict) -> dict:
    """Normalize an already-structured dict into clean ResumeData.

    Delegates to app.services.resume_normalizer.normalize_resume_data.
    """
    from app.services.resume_normalizer import normalize_resume_data
    resume = normalize_resume_data(data)
    return resume.model_dump()


def get_sample_resume(lang: str = "en") -> dict:
    """Return a sample resume for the requested language (en/ar/bilingual)."""
    from app.models.resume import sample_resume
    resume = sample_resume(lang if lang in ("en", "ar", "bilingual") else "en")
    return resume.model_dump()
