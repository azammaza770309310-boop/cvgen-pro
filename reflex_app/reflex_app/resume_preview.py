"""CVGen Pro — Reflex Resume Preview Component (matches official PDF template).

Reference: CVGen Pro - مولّد السير الذاتية الاحترافي.pdf
See: official-template-measurements.md

Layout (row-based, matching the PDF):
  - Single A4 page. Header (name + contact) + full-width header divider.
  - 6 section ROWS. Each row: EN heading (left) + AR heading (right) on the
    same baseline, then a FULL-WIDTH section divider, then EN content (left)
    + AR content (right).
  - No vertical divider between columns — only a ~10mm gap.

Static font sizes (measured from PDF, scaled to A4, ISOLATED from global
font_size control):
  - Name:        20pt  (PDF 7.9pt × 2.47)
  - Contact:      9pt  (PDF 3.5pt × 2.47)
  - Heading:    11.5pt  (PDF 4.6pt × 2.47)
  - Body:        11pt   (PDF 4.4pt × 2.47)  ← scales with global font_size
  - Dates:        9pt   (PDF 3.7pt × 2.47)

Colors (from PDF):
  #000000 — name, headings, dividers, item titles
  #1E2939 — body text
  #364153 — secondary (institution, contact, location)
  #4A5565 — dates
"""
from __future__ import annotations

import reflex as rx
from reflex_app.reflex_app.state import (
    ResumeState,
    ExperienceData,
    EducationData,
    LanguageData,
    BulletData,
)


# ---------------------------------------------------------------------------
# Static font-size constants (measured from the official PDF, isolated from
# ResumeState.font_size so the header never changes when the user adjusts the
# global font-size control).
# ---------------------------------------------------------------------------
_NAME_SIZE = "20pt"
_CONTACT_SIZE = "9pt"
_HEADING_SIZE = "11.5pt"
_DATE_SIZE = "9pt"

# Body font sizes scale with the global font_size control via computed vars
# (ResumeState.body_font_size_px / body_font_size_small_px). The header does NOT.


# ---------------------------------------------------------------------------
# Sub-components
# ---------------------------------------------------------------------------

def bullet_item(bullet: BulletData) -> rx.Component:
    return rx.list_item(
        bullet.text,
        font_size=ResumeState.body_font_size_px,
        color="#1E2939",
        margin_bottom="2px",
    )


def experience_item(exp: ExperienceData) -> rx.Component:
    return rx.box(
        rx.text(
            exp.title_en,
            font_weight="bold",
            font_size=ResumeState.body_font_size_px,
            color="#000000",
            as_="span",
        ),
        rx.text(
            f" — {exp.company_en} ({exp.start_date} - {exp.end_date})",
            font_size=ResumeState.body_font_size_small_px,
            color="#364153",
            as_="span",
        ),
        rx.unordered_list(
            rx.foreach(exp.bullets_en, bullet_item),
            padding_left="15px",
            margin_top="2px",
            list_style_type="none",
        ),
        margin_bottom="8px",
    )


def experience_item_ar(exp: ExperienceData) -> rx.Component:
    """Arabic-side experience item (RTL)."""
    return rx.box(
        rx.text(
            exp.title_ar,
            font_weight="bold",
            font_size=ResumeState.body_font_size_px,
            color="#000000",
            as_="span",
            dir="rtl",
        ),
        rx.text(
            f" — {exp.company_ar}",
            font_size=ResumeState.body_font_size_small_px,
            color="#364153",
            as_="span",
            dir="rtl",
        ),
        rx.unordered_list(
            rx.foreach(exp.bullets_ar, bullet_item),
            padding_right="15px",
            padding_left="0",
            margin_top="2px",
            list_style_type="none",
            dir="rtl",
        ),
        margin_bottom="8px",
    )


def education_item(edu: EducationData) -> rx.Component:
    return rx.box(
        rx.text(edu.degree_en, font_weight="bold", font_size=ResumeState.body_font_size_px, color="#000000"),
        rx.text(edu.institution_en, font_size=ResumeState.body_font_size_small_px, color="#364153"),
        rx.cond(
            edu.year != "",
            rx.text(edu.year, font_size=_DATE_SIZE, color="#4A5565"),
        ),
        margin_bottom="6px",
    )


def education_item_ar(edu: EducationData) -> rx.Component:
    return rx.box(
        rx.text(edu.degree_ar, font_weight="bold", font_size=ResumeState.body_font_size_px, color="#000000", dir="rtl"),
        rx.text(edu.institution_ar, font_size=ResumeState.body_font_size_small_px, color="#364153", dir="rtl"),
        rx.cond(
            edu.year != "",
            rx.text(edu.year, font_size=_DATE_SIZE, color="#4A5565"),
        ),
        margin_bottom="6px",
    )


def skill_item(skill: str) -> rx.Component:
    return rx.list_item(skill, font_size=ResumeState.body_font_size_px, color="#1E2939", margin_bottom="2px")


def language_item(lang: LanguageData) -> rx.Component:
    nm = lang.name
    return rx.list_item(
        nm,
        rx.cond(
            lang.level != "",
            rx.text(f" ({lang.level})", font_size=ResumeState.body_font_size_small_px, color="#364153", as_="span"),
        ),
        font_size=ResumeState.body_font_size_px,
        color="#1E2939",
        margin_bottom="2px",
    )


# ---------------------------------------------------------------------------
# Section ROW (matches official PDF: EN heading | AR heading, full-width divider,
# then EN body | AR body)
# ---------------------------------------------------------------------------

def section_row(title_en: str, title_ar: str, body_en: rx.Component, body_ar: rx.Component) -> rx.Component:
    """Render one section as a ROW matching the official PDF layout.

    EN heading (left) + AR heading (right) on the same baseline, then a
    full-width divider spanning both columns, then EN content (left) +
    AR content (right).
    """
    return rx.box(
        # Paired headings on the same row
        rx.grid(
            rx.heading(
                title_en,
                size="5",
                font_size=_HEADING_SIZE,
                font_weight="bold",
                color="#000000",
                text_transform="uppercase",
                text_align="left",
            ),
            rx.heading(
                title_ar,
                size="5",
                font_size=_HEADING_SIZE,
                font_weight="bold",
                color="#000000",
                text_align="right",
                dir="rtl",
            ),
            grid_template_columns="1fr 1fr",
            gap="10mm",
            align_items="baseline",
        ),
        # Full-width solid divider spanning both columns
        rx.divider(
            width="100%",
            border_color="#000000",
            border_width="1.5px",
            margin_y="2px",
        ),
        # Paired body: EN (left, LTR) + AR (right, RTL)
        rx.grid(
            rx.box(body_en, text_align="left", dir="ltr"),
            rx.box(body_ar, text_align="right", dir="rtl"),
            grid_template_columns="1fr 1fr",
            gap="10mm",
        ),
        margin_bottom="10px",
    )


# ---------------------------------------------------------------------------
# Header (centered with rx.vstack) — STATIC fonts, isolated from global font_size
# ---------------------------------------------------------------------------

def resume_header() -> rx.Component:
    """Resume header with STATIC font sizes (measured from official PDF).

    Name = 20pt, contact = 9pt. These are NOT bound to ResumeState.font_size —
    only the resume body text scales with the global control.
    """
    return rx.vstack(
        # Names row — STATIC 20pt (isolated from global font_size)
        rx.grid(
            rx.heading(
                ResumeState.name_en,
                size="6",
                font_size=_NAME_SIZE,
                font_weight="bold",
                color="#000000",
                text_transform="uppercase",
                as_="h1",
                text_align="left",
            ),
            rx.heading(
                ResumeState.name_ar,
                size="6",
                font_size=_NAME_SIZE,
                font_weight="bold",
                color="#000000",
                as_="h1",
                text_align="right",
                dir="rtl",
            ),
            grid_template_columns="1fr 1fr",
            gap="10mm",
            align_items="center",
            width="100%",
        ),
        # Contact bar — STATIC 9pt (isolated from global font_size).
        # Contact links are NOT blue (official PDF uses dark slate #364153).
        rx.hstack(
            rx.cond(
                ResumeState.email != "",
                rx.link(
                    f"✉️ {ResumeState.email}",
                    href=f"mailto:{ResumeState.email}",
                    color="#364153",
                    text_decoration="none",
                    font_size=_CONTACT_SIZE,
                ),
            ),
            rx.cond(
                ResumeState.phone != "",
                rx.link(
                    f"📞 {ResumeState.phone}",
                    href=f"tel:{ResumeState.phone}",
                    color="#364153",
                    text_decoration="none",
                    font_size=_CONTACT_SIZE,
                ),
            ),
            rx.cond(
                ResumeState.location != "",
                rx.text(
                    f"📍 {ResumeState.location}",
                    font_size=_CONTACT_SIZE,
                    color="#364153",
                ),
            ),
            spacing="4",
            justify="center",
            align_items="center",
        ),
        # Full-width solid header divider (replaces container border_bottom)
        rx.divider(
            width="100%",
            border_color="#000000",
            border_width="1.5px",
        ),
        align_items="center",
        width="100%",
        padding="0 0 10px 0",
        margin_bottom="10px",
    )


# ---------------------------------------------------------------------------
# Main Resume Preview (A4 Canvas) — row-based layout matching official PDF
# ---------------------------------------------------------------------------

def resume_preview_bilingual() -> rx.Component:
    """A4 resume preview — uses the SAME rendering source as the PDF export.

    CRITICAL for preview=PDF parity: this component renders the HTML produced
    by app.templates_render.render_official_bilingual_master() via rx.html().
    This guarantees the browser preview and the exported PDF use the EXACT
    SAME HTML + CSS source — no divergence possible.

    The previous version built the HTML via rx.* components (section_row,
    resume_header, etc.) which was a SEPARATE code path from the PDF
    renderer. That caused visual drift between preview and PDF. This
    version eliminates the drift by using the single shared renderer.

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
