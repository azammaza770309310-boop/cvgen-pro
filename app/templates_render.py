"""OFFICIAL MASTER TEMPLATE RENDERER — exact implementation from provided spec.

Layout (strict):
  ┌──────────────────────────────────────────┐
  │  Header EN (left)  │  Header AR (right)  │  ← 50/50, border-bottom
  ├──────────────────────────────────────────┤
  │  ENGLISH COLUMN    │    ARABIC COLUMN    │  ← 50/50, central divider
  │  CAREER OBJECTIVE  │    الهدف الوظيفي    │
  │  EDUCATION         │    التعليم          │
  │  EXPERIENCE        │    الخبرات المهنية  │
  │  COURSES           │    الدورات          │
  │  SKILLS            │    المهارات         │
  │  TECHNICAL SKILLS  │    المهارات التقنية │
  │  LANGUAGES         │    اللغات           │
  └──────────────────────────────────────────┘

Strict isolation: English column dir="ltr", Arabic column dir="rtl".
Central vertical divider between them.
"""
from __future__ import annotations

import html
from typing import List

from app.models.resume import ResumeData


def esc(s: str) -> str:
    return html.escape(s or "")


def _contact_ltr(value: str) -> str:
    if not value:
        return ""
    return f'<span dir="ltr">{esc(value)}</span>'


def _exp_item(exp, lang: str) -> str:
    if lang == "en":
        position = exp.title_en or exp.title or ""
        company = exp.company_en or exp.company or ""
        bullets = exp.bullets_en or exp.bullets or []
    else:
        position = exp.title_ar or exp.title or ""
        company = exp.company_ar or exp.company or ""
        bullets = exp.bullets_ar or exp.bullets or []

    date_parts = []
    if exp.start_date:
        date_parts.append(exp.start_date)
    if exp.end_date:
        date_parts.append(exp.end_date)
    elif exp.current:
        date_parts.append("Present" if lang == "en" else "حتى الآن")
    date_str = " – ".join(date_parts) if date_parts else ""

    parts = ['<div class="list-item">']
    parts.append('<div class="item-header">')
    if position:
        parts.append(f'<span class="editable item-title">{esc(position)}</span>')
    if date_str:
        parts.append(f'<span class="editable item-date">{esc(date_str)}</span>')
    parts.append('</div>')
    if company:
        parts.append(f'<div class="editable item-subtitle">{esc(company)}</div>')
    if bullets:
        items = "".join(f'<li class="editable">{esc(b)}</li>' for b in bullets if b)
        if items:
            parts.append(f'<ul class="editable-list">{items}</ul>')
    parts.append('</div>')
    return "".join(parts)


def _edu_item(ed, lang: str) -> str:
    if lang == "en":
        degree = ed.degree_en or ed.degree or ""
        institution = ed.institution_en or ed.institution or ""
    else:
        degree = ed.degree_ar or ed.degree or ""
        institution = ed.institution_ar or ed.institution or ""
    year = ed.year or ed.end_date or ""
    gpa = ed.gpa or ""

    parts = ['<div class="list-item"><div class="item-header">']
    if degree:
        parts.append(f'<span class="editable item-title">{esc(degree)}</span>')
    if year:
        parts.append(f'<span class="editable item-date">{esc(year)}</span>')
    parts.append('</div>')
    if institution:
        parts.append(f'<div class="editable item-subtitle">{esc(institution)}</div>')
    if gpa:
        parts.append(f'<div class="editable item-subtitle">GPA: {esc(gpa)}</div>')
    parts.append('</div>')
    return "".join(parts)


def _bullet_list(items: List[str]) -> str:
    if not items:
        return ""
    lis = "".join(f'<li class="editable">{esc(item)}</li>' for item in items if item)
    return f'<ul class="editable-list">{lis}</ul>' if lis else ""


def _section(title: str, content_html: str) -> str:
    if not content_html:
        return ""
    return f'<div class="section"><h2>{esc(title)}</h2>{content_html}</div>'


# ---------------------------------------------------------------------------
# RENDERER — exact DOM from provided spec
# ---------------------------------------------------------------------------

def render_official_bilingual_master(resume: ResumeData) -> str:
    parts = ['<div class="a4-page" id="resume-document">']

    # ===== HEADER: names in one row + single contact bar =====
    name_en = resume.personal.name_en or resume.personal.name or ""
    name_ar = resume.personal.name_ar or resume.personal.name or ""
    parts.append('<header class="resume-header">')
    # Row 1: EN name (left) + AR name (right)
    parts.append('<div class="header-names">')
    if name_en:
        parts.append(f'<h1 class="editable header-name-en" data-field="name_en" dir="ltr">{esc(name_en)}</h1>')
    if name_ar:
        parts.append(f'<h1 class="editable header-name-ar" data-field="name_ar" dir="rtl">{esc(name_ar)}</h1>')
    parts.append('</div>')
    # Row 2: single contact bar with icons (no duplication)
    contact_parts = []
    if resume.personal.email:
        contact_parts.append(f'<span class="contact-item">✉️ <span class="editable" data-field="email" dir="ltr">{esc(resume.personal.email)}</span></span>')
    if resume.personal.phone:
        contact_parts.append(f'<span class="contact-item">📞 <span class="editable" data-field="phone" dir="ltr">{esc(resume.personal.phone)}</span></span>')
    if resume.personal.location:
        contact_parts.append(f'<span class="contact-item">📍 <span class="editable" data-field="location">{esc(resume.personal.location)}</span></span>')
    if contact_parts:
        parts.append(f'<div class="contact-bar">{"  ".join(contact_parts)}</div>')
    parts.append('</header>')

    # ===== COLUMNS CONTAINER =====
    parts.append('<div class="columns-container">')

    # --- ENGLISH COLUMN (strict LTR) ---
    parts.append('<div class="column col-en" dir="ltr">')

    sum_en = resume.summary_text("en")
    if sum_en:
        parts.append(_section("CAREER OBJECTIVE", f'<p class="editable" data-field="summary_en">{esc(sum_en)}</p>'))

    if resume.education:
        edu_html = "".join(_edu_item(ed, "en") for ed in resume.education)
        parts.append(_section("EDUCATION", edu_html))

    if resume.experience:
        exp_html = "".join(_exp_item(e, "en") for e in resume.experience)
        parts.append(_section("EXPERIENCE", exp_html))

    if resume.courses:
        parts.append(_section("COURSES", _bullet_list(resume.courses)))

    # Skills: English column shows only English skills (skills list as-is)
    if resume.skills:
        parts.append(_section("SKILLS", _bullet_list(resume.skills)))

    # Technical skills: English column only
    if resume.technical_skills:
        parts.append(_section("TECHNICAL SKILLS", _bullet_list(resume.technical_skills)))

    if resume.certifications:
        cert_names = [c.name if hasattr(c, "name") else str(c) for c in resume.certifications]
        parts.append(_section("CERTIFICATIONS", _bullet_list(cert_names)))

    if resume.languages:
        lang_items = [f"{l.name} – {l.level}" if l.level else l.name for l in resume.languages]
        parts.append(_section("LANGUAGES", _bullet_list(lang_items)))

    parts.append('</div>')  # end col-en

    # --- CENTRAL DIVIDER ---
    parts.append('<div class="central-divider"></div>')

    # --- ARABIC COLUMN (strict RTL) ---
    parts.append('<div class="column col-ar" dir="rtl">')

    sum_ar = resume.summary_text("ar")
    if sum_ar:
        parts.append(_section("الهدف الوظيفي", f'<p class="editable" data-field="summary_ar">{esc(sum_ar)}</p>'))

    if resume.education:
        edu_html = "".join(_edu_item(ed, "ar") for ed in resume.education)
        parts.append(_section("التعليم", edu_html))

    if resume.experience:
        exp_html = "".join(_exp_item(e, "ar") for e in resume.experience)
        parts.append(_section("الخبرات المهنية", exp_html))

    if resume.courses:
        parts.append(_section("الدورات", _bullet_list(resume.courses)))

    # Skills: Arabic column shows soft skills (Arabic-named) only
    if resume.soft_skills:
        parts.append(_section("المهارات", _bullet_list(resume.soft_skills)))
    elif resume.skills:
        parts.append(_section("المهارات", _bullet_list(resume.skills)))

    if resume.technical_skills:
        parts.append(_section("المهارات التقنية", _bullet_list(resume.technical_skills)))

    if resume.certifications:
        cert_names = [c.name if hasattr(c, "name") else str(c) for c in resume.certifications]
        parts.append(_section("الشهادات", _bullet_list(cert_names)))

    if resume.languages:
        lang_items = [f"{l.name} – {l.level}" if l.level else l.name for l in resume.languages]
        parts.append(_section("اللغات", _bullet_list(lang_items)))

    parts.append('</div>')  # end col-ar

    parts.append('</div>')  # end columns-container
    parts.append('</div>')  # end a4-page
    return "".join(parts)
