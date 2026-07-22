"""CVGen Pro — Reflex Resume Preview Component.

SINGLE SOURCE OF TRUTH: This component renders the EXACT SAME HTML as the
PDF export. It uses rx.html(ResumeState.preview_html) where preview_html is
a computed var that calls app.templates_render.render_official_bilingual_master()
— the same function used by the PDF exporter.

The old rx component functions (bullet_item, experience_item, section_row,
resume_header, etc.) have been REMOVED. They were a separate rendering code
path that caused preview/PDF drift. Now there is ONE renderer, ONE CSS file,
ONE result.

Reference: CVGen Pro - مولّد السير الذاتية الاحترافي.pdf
See: official-template-measurements.md
"""
from __future__ import annotations

import reflex as rx
from reflex_app.reflex_app.state import ResumeState


# ---------------------------------------------------------------------------
# Main Resume Preview (A4 Canvas) — renders shared HTML via rx.html()
# ---------------------------------------------------------------------------

def resume_preview_bilingual() -> rx.Component:
    """A4 resume preview — uses the SAME rendering source as the PDF export.

    CRITICAL for preview=PDF parity: this component renders the HTML produced
    by app.templates_render.render_official_bilingual_master() via rx.html().
    This guarantees the browser preview and the exported PDF use the EXACT
    SAME HTML + CSS source — no divergence possible.

    The CSS (templates.css) is injected into the page by index() in __init__.py
    via rx.style(_load_template_css()). Without that, the preview would be
    unstyled.

    Section order (official, from the reference PDF):
      1. CAREER OBJECTIVE / الهدف المهني
      2. PROFESSIONAL EXPERIENCE / الخبرة العملية
      3. EDUCATION / المؤهلات العلمية
      4. SKILLS / المهارات
      5. COURSES & CERTIFICATIONS / الدورات والشهادات
      6. LANGUAGES / اللغات
    """
    return rx.center(
        rx.box(
            # Render the SAME HTML that the PDF export uses.
            # ResumeState.preview_html is a computed var that calls
            # app.templates_render.render_official_bilingual_master().
            # This guarantees preview = PDF (same HTML + same CSS).
            rx.html(ResumeState.preview_html),
            # A4 canvas styling (the .a4-page class in templates.css
            # handles the internal padding/layout; this wrapper just
            # provides the shadow + centering).
            background_color="white",
            box_shadow="lg",
            margin_x="auto",
            max_width="210mm",
            width="100%",
            min_height="297mm",
        ),
        width="100%",
        padding="20px",
        background_color="#2a2a2a",
    )
