"""OFFICIAL MASTER TEMPLATE RENDERERS — 3 templates:
1. official_bilingual_master: Two-column (EN left, AR right) — existing
2. official_english_single: Single-column English-only — new
3. official_arabic_single: Single-column Arabic-only RTL — new

All templates are FIXED. Only data is dynamic.
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

    parts = ['<div class="item">']
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

    parts = ['<div class="item"><div class="item-header">']
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


def _build_contact_bar(resume: ResumeData) -> list[str]:
    """Build contact bar with clickable links in blue."""
    contact_parts = []
    if resume.personal.email:
        contact_parts.append(
            f'<span class="contact-item">✉️ <a href="mailto:{esc(resume.personal.email)}" '
            f'class="contact-link editable" data-field="email" dir="ltr">{esc(resume.personal.email)}</a></span>'
        )
    if resume.personal.phone:
        contact_parts.append(
            f'<span class="contact-item">📞 <a href="tel:{esc(resume.personal.phone)}" '
            f'class="contact-link editable" data-field="phone" dir="ltr">{esc(resume.personal.phone)}</a></span>'
        )
    if resume.personal.location:
        contact_parts.append(
            f'<span class="contact-item">📍 <span class="editable" data-field="location">{esc(resume.personal.location)}</span></span>'
        )
    return contact_parts


# ===========================================================================
# TEMPLATE 1: Bilingual Master (two columns — EN left, AR right)
# ===========================================================================

def render_official_bilingual_master(resume: ResumeData) -> str:
    parts = ['<div class="a4-page" id="resume-document">']

    # ===== HEADER: names centered + contact below in blue =====
    name_en = resume.personal.name_en or resume.personal.name or ""
    name_ar = resume.personal.name_ar or resume.personal.name or ""
    parts.append('<header class="resume-header">')
    parts.append('<div class="header-names">')
    if name_en:
        parts.append(f'<h1 class="editable header-name-en" data-field="name_en" dir="ltr">{esc(name_en)}</h1>')
    if name_ar:
        parts.append(f'<h1 class="editable header-name-ar" data-field="name_ar" dir="rtl">{esc(name_ar)}</h1>')
    parts.append('</div>')
    contact_parts = _build_contact_bar(resume)
    if contact_parts:
        parts.append(f'<div class="contact-bar">{"  ".join(contact_parts)}</div>')
    parts.append('</header>')

    # ===== TWO COLUMNS =====
    parts.append('<div class="columns-container">')

    # --- ENGLISH COLUMN ---
    parts.append('<div class="column col-en" dir="ltr">')
    sum_en = resume.summary_text("en")
    if sum_en:
        parts.append(_section("CAREER OBJECTIVE", f'<p class="editable" data-field="summary_en">{esc(sum_en)}</p>'))
    if resume.education:
        parts.append(_section("EDUCATION", "".join(_edu_item(ed, "en") for ed in resume.education)))
    if resume.experience:
        parts.append(_section("EXPERIENCE", "".join(_exp_item(e, "en") for e in resume.experience)))
    if resume.courses:
        parts.append(_section("COURSES", _bullet_list(resume.courses)))
    from app.utils.arabic import contains_arabic
    en_skills = [s for s in resume.skills if not contains_arabic(s)]
    ar_skills = [s for s in resume.skills if contains_arabic(s)]
    en_tech = [s for s in resume.technical_skills if not contains_arabic(s)]
    ar_tech = [s for s in resume.technical_skills if contains_arabic(s)]
    if en_skills:
        parts.append(_section("SKILLS", _bullet_list(en_skills)))
    if en_tech:
        parts.append(_section("TECHNICAL SKILLS", _bullet_list(en_tech)))
    if resume.certifications:
        cert_names = [c.name if hasattr(c, "name") else str(c) for c in resume.certifications]
        parts.append(_section("CERTIFICATIONS", _bullet_list(cert_names)))
    if resume.languages:
        lang_items = [f"{l.name} – {l.level}" if l.level else l.name for l in resume.languages]
        parts.append(_section("LANGUAGES", _bullet_list(lang_items)))
    parts.append('</div>')

    # --- DIVIDER ---
    parts.append('<div class="central-divider"></div>')

    # --- ARABIC COLUMN ---
    parts.append('<div class="column col-ar" dir="rtl">')
    sum_ar = resume.summary_text("ar")
    if sum_ar:
        parts.append(_section("الهدف الوظيفي", f'<p class="editable" data-field="summary_ar">{esc(sum_ar)}</p>'))
    if resume.education:
        parts.append(_section("التعليم", "".join(_edu_item(ed, "ar") for ed in resume.education)))
    if resume.experience:
        parts.append(_section("الخبرات المهنية", "".join(_exp_item(e, "ar") for e in resume.experience)))
    if resume.courses:
        parts.append(_section("الدورات", _bullet_list(resume.courses)))
    ar_all_skills = ar_skills + [s for s in resume.soft_skills if contains_arabic(s)]
    if ar_all_skills:
        parts.append(_section("المهارات", _bullet_list(ar_all_skills)))
    if ar_tech:
        parts.append(_section("المهارات التقنية", _bullet_list(ar_tech)))
    if resume.certifications:
        cert_names = [c.name if hasattr(c, "name") else str(c) for c in resume.certifications]
        parts.append(_section("الشهادات", _bullet_list(cert_names)))
    if resume.languages:
        lang_items = [f"{l.name} – {l.level}" if l.level else l.name for l in resume.languages]
        parts.append(_section("اللغات", _bullet_list(lang_items)))
    parts.append('</div>')

    parts.append('</div>')
    parts.append('</div>')
    return "".join(parts)


# ===========================================================================
# TEMPLATE 2: English Single-Column (like Ghazwa EN PDF)
# ===========================================================================

def render_english_single_column(resume: ResumeData) -> str:
    """Single-column English-only resume, centered header, blue contact links."""
    parts = ['<div class="a4-page a4-single a4-en" id="resume-document">']

    # ===== HEADER: centered name + contact below =====
    name_en = resume.personal.name_en or resume.personal.name or ""
    parts.append('<header class="resume-header resume-header-center">')
    if name_en:
        parts.append(f'<h1 class="editable header-name-center" data-field="name_en" dir="ltr">{esc(name_en)}</h1>')
    contact_parts = _build_contact_bar(resume)
    if contact_parts:
        parts.append(f'<div class="contact-bar contact-bar-center">{"  ".join(contact_parts)}</div>')
    parts.append('</header>')

    # ===== SINGLE COLUMN BODY =====
    parts.append('<div class="single-column" dir="ltr">')

    sum_en = resume.summary_text("en")
    if sum_en:
        parts.append(_section("CAREER OBJECTIVE", f'<p class="editable" data-field="summary_en">{esc(sum_en)}</p>'))
    if resume.education:
        parts.append(_section("EDUCATION", "".join(_edu_item(ed, "en") for ed in resume.education)))
    if resume.experience:
        parts.append(_section("EXPERIENCE", "".join(_exp_item(e, "en") for e in resume.experience)))
    if resume.courses:
        parts.append(_section("COURSES", _bullet_list(resume.courses)))
    en_skills = [s for s in resume.skills if not _has_arabic(s)]
    if en_skills:
        parts.append(_section("SKILLS", _bullet_list(en_skills)))
    en_tech = [s for s in resume.technical_skills if not _has_arabic(s)]
    if en_tech:
        parts.append(_section("TECHNICAL SKILLS", _bullet_list(en_tech)))
    if resume.certifications:
        cert_names = [c.name if hasattr(c, "name") else str(c) for c in resume.certifications]
        parts.append(_section("CERTIFICATIONS", _bullet_list(cert_names)))
    if resume.languages:
        lang_items = [f"{l.name} – {l.level}" if l.level else l.name for l in resume.languages]
        parts.append(_section("LANGUAGES", _bullet_list(lang_items)))

    parts.append('</div>')
    parts.append('</div>')
    return "".join(parts)


# ===========================================================================
# TEMPLATE 3: Arabic Single-Column (like Ghazwa AR PDF)
# ===========================================================================

def render_arabic_single_column(resume: ResumeData) -> str:
    """Single-column Arabic-only resume, RTL, centered header."""
    parts = ['<div class="a4-page a4-single a4-ar" id="resume-document" dir="rtl">']

    # ===== HEADER: centered Arabic name + contact below =====
    name_ar = resume.personal.name_ar or resume.personal.name or ""
    parts.append('<header class="resume-header resume-header-center">')
    if name_ar:
        parts.append(f'<h1 class="editable header-name-center" data-field="name_ar" dir="rtl">{esc(name_ar)}</h1>')
    contact_parts = _build_contact_bar(resume)
    if contact_parts:
        parts.append(f'<div class="contact-bar contact-bar-center">{"  ".join(contact_parts)}</div>')
    parts.append('</header>')

    # ===== SINGLE COLUMN BODY (RTL) =====
    parts.append('<div class="single-column" dir="rtl">')

    sum_ar = resume.summary_text("ar")
    if sum_ar:
        parts.append(_section("الهدف الوظيفي", f'<p class="editable" data-field="summary_ar">{esc(sum_ar)}</p>'))
    if resume.education:
        parts.append(_section("التعليم", "".join(_edu_item(ed, "ar") for ed in resume.education)))
    if resume.experience:
        parts.append(_section("الخبرات المهنية", "".join(_exp_item(e, "ar") for e in resume.experience)))
    if resume.courses:
        parts.append(_section("الدورات", _bullet_list(resume.courses)))
    ar_skills = [s for s in resume.skills if _has_arabic(s)] or resume.skills
    if ar_skills:
        parts.append(_section("المهارات", _bullet_list(ar_skills)))
    ar_tech = [s for s in resume.technical_skills if _has_arabic(s)] or resume.technical_skills
    if ar_tech:
        parts.append(_section("المهارات التقنية", _bullet_list(ar_tech)))
    if resume.certifications:
        cert_names = [c.name if hasattr(c, "name") else str(c) for c in resume.certifications]
        parts.append(_section("الشهادات", _bullet_list(cert_names)))
    if resume.languages:
        lang_items = [f"{l.name} – {l.level}" if l.level else l.name for l in resume.languages]
        parts.append(_section("اللغات", _bullet_list(lang_items)))

    parts.append('</div>')
    parts.append('</div>')
    return "".join(parts)


def _has_arabic(text: str) -> bool:
    """Check if text contains Arabic characters."""
    if not text:
        return False
    try:
        from app.utils.arabic import contains_arabic
        return contains_arabic(text)
    except Exception:
        return False
