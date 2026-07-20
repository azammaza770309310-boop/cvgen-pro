"""HTML renderer for the OFFICIAL MASTER TEMPLATE.

This is the SINGLE source of truth for the resume's visual design.
The template is FIXED — only the data is dynamic.

Architecture:
  User Raw CV → Cloud AI → Structured JSON → THIS RENDERER → Fixed Template + New Data

Layout (matches original PDF exactly):
  ┌─────────────────────────────────────────────┐
  │  Name (EN, left)        Name (AR, right)    │  ← Header
  ├─────────────────────────────────────────────┤
  │  email · phone · location (gray bar)         │  ← Contact bar
  ├─────────────────────────────────────────────┤
  │  CAREER OBJECTIVE    │    الهدف الوظيفي      │  ← Section heading + divider
  │  English summary     │    الملخص العربي      │  ← Two-column body
  ├─────────────────────────────────────────────┤
  │  EDUCATION           │    التعليم            │
  │  English edu         │    التعليم العربي     │
  ├─────────────────────────────────────────────┤
  │  EXPERIENCE          │    الخبرات المهنية    │
  │  English exp         │    الخبرات العربية    │
  └─────────────────────────────────────────────┘
"""
from __future__ import annotations

import html
from typing import List

from app.models.resume import ResumeData


def esc(s: str) -> str:
    return html.escape(s or "")


def _contact_ltr(value: str) -> str:
    """Contact value wrapped in dir=ltr to prevent RTL reversal."""
    if not value:
        return ""
    return f'<span dir="ltr">{esc(value)}</span>'


def _section_heading(en: str, ar: str) -> str:
    """Fixed bilingual section heading: English left + Arabic right + divider below."""
    return (
        f'<div class="obm-section-heading">'
        f'<span class="obm-h-en" dir="ltr">{esc(en)}</span>'
        f'<span class="obm-h-ar" dir="rtl">{esc(ar)}</span>'
        f'</div>'
    )


def _two_col_section(heading_en: str, heading_ar: str, en_html: str, ar_html: str) -> str:
    """Fixed two-column section: heading row + two columns of content."""
    if not en_html and not ar_html:
        return ""
    return (
        f'<div class="obm-section">'
        f'{_section_heading(heading_en, heading_ar)}'
        f'<div class="obm-section-body">'
        f'<div class="obm-col-en" dir="ltr">{en_html}</div>'
        f'<div class="obm-col-ar" dir="rtl">{ar_html}</div>'
        f'</div></div>'
    )


def _exp_item_html(exp, lang: str) -> str:
    """Fixed experience item: title — company (dates) + bullets."""
    if lang == "en":
        title = exp.title_en or exp.title or ""
        company = exp.company_en or exp.company or ""
        bullets = exp.bullets_en or exp.bullets or []
    else:
        title = exp.title_ar or exp.title or ""
        company = exp.company_ar or exp.company or ""
        bullets = exp.bullets_ar or exp.bullets or []

    date_parts = []
    if exp.start_date:
        date_parts.append(exp.start_date)
    if exp.end_date:
        date_parts.append(exp.end_date)
    elif exp.current:
        date_parts.append("Present" if lang == "en" else "حتى الآن")
    date_str = " - ".join(date_parts) if date_parts else ""

    header = title
    if company:
        header = f"{header} — {company}" if header else company
    if date_str:
        header = f"{header} ({date_str})" if header else f"({date_str})"

    bullets_html = ""
    if bullets:
        items = "".join(f"<li>{esc(b)}</li>" for b in bullets if b)
        bullets_html = f'<ul class="obm-bullets">{items}</ul>' if items else ""

    if not header and not bullets_html:
        return ""
    return f'<div class="obm-item"><div class="obm-item-header">{esc(header)}</div>{bullets_html}</div>'


def _edu_item_html(ed, lang: str) -> str:
    """Fixed education item: degree — institution (year) | GPA."""
    if lang == "en":
        degree = ed.degree_en or ed.degree or ""
        institution = ed.institution_en or ed.institution or ""
    else:
        degree = ed.degree_ar or ed.degree or ""
        institution = ed.institution_ar or ed.institution or ""

    year = ed.year or ed.end_date or ""
    gpa = ed.gpa or ""

    line = degree
    if institution:
        line = f"{line} — {institution}" if line else institution
    if year:
        line = f"{line} ({year})" if line else f"({year})"
    if gpa:
        line = f"{line} | GPA: {gpa}" if line else f"GPA: {gpa}"

    if not line:
        return ""
    return f'<div class="obm-item">{esc(line)}</div>'


def _bullet_list_html(items: List[str]) -> str:
    """Fixed bullet list with '–' prefix."""
    if not items:
        return ""
    lis = "".join(f"<li>{esc(item)}</li>" for item in items if item)
    return f'<ul class="obm-bullets">{lis}</ul>' if lis else ""


# ---------------------------------------------------------------------------
# THE OFFICIAL MASTER TEMPLATE RENDERER
# ---------------------------------------------------------------------------

def render_official_bilingual_master(resume: ResumeData) -> str:
    """Render the official master template with dynamic data.

    The template structure is FIXED. Only the data slots are filled.
    Cloud AI provides the data; this renderer provides the design.
    """
    parts = ['<div class="cv-root obm-master" data-lang="bilingual">']

    # ===== HEADER: Name (EN left + AR right) =====
    name_en = resume.personal.name_en or resume.personal.name or ""
    name_ar = resume.personal.name_ar or resume.personal.name or ""
    parts.append('<div class="obm-header">')
    if name_en:
        parts.append(f'<div class="obm-name-en" dir="ltr">{esc(name_en)}</div>')
    if name_ar:
        parts.append(f'<div class="obm-name-ar" dir="rtl">{esc(name_ar)}</div>')
    parts.append("</div>")

    # ===== CONTACT BAR (gray background, full width) =====
    contact_parts = []
    if resume.personal.email:
        contact_parts.append(_contact_ltr(resume.personal.email))
    if resume.personal.phone:
        contact_parts.append(_contact_ltr(resume.personal.phone))
    if resume.personal.location:
        contact_parts.append(esc(resume.personal.location))
    if resume.personal.linkedin:
        contact_parts.append(_contact_ltr(resume.personal.linkedin))
    if resume.personal.website:
        contact_parts.append(_contact_ltr(resume.personal.website))
    if contact_parts:
        parts.append(f'<div class="obm-contact-bar">{" · ".join(contact_parts)}</div>')

    # ===== SECTIONS (each is a two-column row) =====

    # --- CAREER OBJECTIVE / الهدف الوظيفي ---
    sum_en = resume.summary_text("en")
    sum_ar = resume.summary_text("ar")
    en_html = f'<p>{esc(sum_en)}</p>' if sum_en else ""
    ar_html = f'<p>{esc(sum_ar)}</p>' if sum_ar else ""
    parts.append(_two_col_section("CAREER OBJECTIVE", "الهدف الوظيفي", en_html, ar_html))

    # --- EDUCATION / التعليم ---
    if resume.education:
        en_html = "".join(_edu_item_html(ed, "en") for ed in resume.education)
        ar_html = "".join(_edu_item_html(ed, "ar") for ed in resume.education)
        parts.append(_two_col_section("EDUCATION", "التعليم", en_html, ar_html))

    # --- EXPERIENCE / الخبرات المهنية ---
    if resume.experience:
        en_html = "".join(_exp_item_html(e, "en") for e in resume.experience)
        ar_html = "".join(_exp_item_html(e, "ar") for e in resume.experience)
        parts.append(_two_col_section("EXPERIENCE", "الخبرات المهنية", en_html, ar_html))

    # --- COURSES / الدورات ---
    if resume.courses:
        en_html = _bullet_list_html(resume.courses)
        ar_html = _bullet_list_html(resume.courses)
        parts.append(_two_col_section("COURSES", "الدورات", en_html, ar_html))

    # --- SKILLS / المهارات ---
    all_skills = resume.skills + resume.soft_skills
    if all_skills:
        en_html = _bullet_list_html(all_skills)
        ar_html = _bullet_list_html(all_skills)
        parts.append(_two_col_section("SKILLS", "المهارات", en_html, ar_html))

    # --- TECHNICAL SKILLS / المهارات التقنية ---
    if resume.technical_skills:
        en_html = _bullet_list_html(resume.technical_skills)
        ar_html = _bullet_list_html(resume.technical_skills)
        parts.append(_two_col_section("TECHNICAL SKILLS", "المهارات التقنية", en_html, ar_html))

    # --- CERTIFICATIONS / الشهادات ---
    if resume.certifications:
        cert_names = [c.name if hasattr(c, "name") else str(c) for c in resume.certifications]
        en_html = _bullet_list_html(cert_names)
        ar_html = _bullet_list_html(cert_names)
        parts.append(_two_col_section("CERTIFICATIONS", "الشهادات", en_html, ar_html))

    # --- LANGUAGES / اللغات ---
    if resume.languages:
        lang_items = []
        for l in resume.languages:
            label = l.name
            if l.level:
                label += f" ({l.level})"
            lang_items.append(label)
        en_html = _bullet_list_html(lang_items)
        ar_html = _bullet_list_html(lang_items)
        parts.append(_two_col_section("LANGUAGES", "اللغات", en_html, ar_html))

    parts.append("</div>")  # cv-root
    return "".join(parts)
