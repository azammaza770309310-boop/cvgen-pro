"""OFFICIAL MASTER BILINGUAL TEMPLATE — matches reference PDF exactly.

Layout: Two equal columns (EN left LTR, AR right RTL).
Header: Both names in one row, contact below in blue links.
Sections: 7 sections with black dividers.
"""
from __future__ import annotations

import html
from typing import List

from app.models.resume import ResumeData


def esc(s: str) -> str:
    return html.escape(s or "")


def _exp_item(exp, lang: str) -> str:
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

    parts = ['<div class="item">']
    # Title — Company (dates)
    header_line = title
    if company:
        header_line = f"{header_line} — {company}" if header_line else company
    if date_str:
        header_line = f"{header_line} ({date_str})" if header_line else f"({date_str})"
    if header_line:
        parts.append(f'<div class="editable item-title">{esc(header_line)}</div>')
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

    line = degree
    if institution:
        line = f"{line} — {institution}" if line else institution
    if year:
        line = f"{line} ({year})" if line else f"({year})"
    if gpa:
        line = f"{line} | GPA: {gpa}" if line else f"GPA: {gpa}"
    if not line:
        return ""
    return f'<div class="editable item">{esc(line)}</div>'


def _bullet_list(items: List[str]) -> str:
    if not items:
        return ""
    lis = "".join(f'<li class="editable">{esc(item)}</li>' for item in items if item)
    return f'<ul class="editable-list">{lis}</ul>' if lis else ""


def _section(title: str, content_html: str) -> str:
    if not content_html:
        return ""
    # Explicit full-width solid <hr> divider — renders consistently in both
    # browser preview and WeasyPrint PDF (replaces unreliable border-bottom on h2)
    return f'<div class="section"><h2 class="editable">{esc(title)}</h2><hr class="section-divider">{content_html}</div>'


# ---------------------------------------------------------------------------
# RENDERER
# ---------------------------------------------------------------------------

def render_official_bilingual_master(resume: ResumeData) -> str:
    parts = ['<div class="a4-page" id="resume-document">']

    # ===== HEADER: names in one row + contact below =====
    name_en = resume.personal.name_en or resume.personal.name or ""
    name_ar = resume.personal.name_ar or resume.personal.name or ""
    parts.append('<header class="resume-header">')
    parts.append('<div class="header-names">')
    if name_en:
        parts.append(f'<h1 class="editable header-name-en" data-field="name_en" dir="ltr">{esc(name_en)}</h1>')
    if name_ar:
        parts.append(f'<h1 class="editable header-name-ar" data-field="name_ar" dir="rtl">{esc(name_ar)}</h1>')
    parts.append('</div>')
    # Contact bar — English only, blue links
    contact_parts = []
    if resume.personal.email:
        contact_parts.append(f'<span class="contact-item">✉️ <a href="mailto:{esc(resume.personal.email)}" class="contact-link editable" data-field="email" dir="ltr">{esc(resume.personal.email)}</a></span>')
    if resume.personal.phone:
        contact_parts.append(f'<span class="contact-item">📞 <a href="tel:{esc(resume.personal.phone)}" class="contact-link editable" data-field="phone" dir="ltr">{esc(resume.personal.phone)}</a></span>')
    if resume.personal.location:
        contact_parts.append(f'<span class="contact-item">📍 <span class="editable" data-field="location">{esc(resume.personal.location)}</span></span>')
    if contact_parts:
        parts.append(f'<div class="contact-bar">{"  ".join(contact_parts)}</div>')
    parts.append('</header>')

    # ===== TWO EQUAL COLUMNS =====
    parts.append('<div class="columns-container">')

    # --- ENGLISH COLUMN (left, LTR) ---
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
    # Use explicit bilingual skill arrays (skills_en / skills_ar) populated by
    # the normalizer's 1:1 enforcement. Fall back to language filtering of the
    # generic `skills` array only if the explicit arrays are empty.
    en_skills = resume.skills_en or [s for s in resume.skills if not contains_arabic(s)]
    ar_skills = resume.skills_ar or [s for s in resume.skills if contains_arabic(s)]
    en_tech = resume.technical_skills_en or [s for s in resume.technical_skills if not contains_arabic(s)]
    # Arabic column shows ALL technical skills (tech terms are universal —
    # "Python", "JavaScript" etc. don't need translation), so the Arabic
    # TECHNICAL SKILLS section mirrors the English one instead of being empty.
    ar_tech = resume.technical_skills_ar or resume.technical_skills
    if en_skills:
        parts.append(_section("SKILLS", _bullet_list(en_skills)))
    if en_tech:
        parts.append(_section("TECHNICAL SKILLS", _bullet_list(en_tech)))
    if resume.languages:
        lang_items = [f"{l.name} ({l.level})" if l.level else l.name for l in resume.languages]
        parts.append(_section("LANGUAGES", _bullet_list(lang_items)))
    parts.append('</div>')

    # --- DIVIDER ---
    parts.append('<div class="central-divider"></div>')

    # --- ARABIC COLUMN (right, RTL) ---
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
    # Arabic skills column uses skills_ar (1:1 mirror of skills_en, enforced by normalizer).
    # Falls back to soft_skills (Arabic) + any Arabic items in generic skills.
    ar_all_skills = ar_skills or resume.skills_ar
    if not ar_all_skills and resume.soft_skills:
        ar_all_skills = [s for s in resume.soft_skills if contains_arabic(s)] or resume.soft_skills
    if ar_all_skills:
        parts.append(_section("المهارات", _bullet_list(ar_all_skills)))
    # Arabic technical skills mirrors English (tech terms are universal)
    ar_all_tech = ar_tech or resume.technical_skills_ar or resume.technical_skills
    if ar_all_tech:
        parts.append(_section("المهارات التقنية", _bullet_list(ar_all_tech)))
    if resume.languages:
        lang_items = [f"{l.name} ({l.level})" if l.level else l.name for l in resume.languages]
        parts.append(_section("اللغات", _bullet_list(lang_items)))
    parts.append('</div>')

    parts.append('</div>')
    parts.append('</div>')
    return "".join(parts)


# ===========================================================================
# TEMPLATE 2: English Single-Column
# ===========================================================================

def render_english_single_column(resume: ResumeData) -> str:
    parts = ['<div class="a4-page a4-single a4-en" id="resume-document">']
    name_en = resume.personal.name_en or resume.personal.name or ""
    parts.append('<header class="resume-header resume-header-center">')
    if name_en:
        parts.append(f'<h1 class="editable header-name-center" data-field="name_en" dir="ltr">{esc(name_en)}</h1>')
    contact_parts = []
    if resume.personal.email:
        contact_parts.append(f'<span class="contact-item">✉️ <a href="mailto:{esc(resume.personal.email)}" class="contact-link editable" data-field="email" dir="ltr">{esc(resume.personal.email)}</a></span>')
    if resume.personal.phone:
        contact_parts.append(f'<span class="contact-item">📞 <a href="tel:{esc(resume.personal.phone)}" class="contact-link editable" data-field="phone" dir="ltr">{esc(resume.personal.phone)}</a></span>')
    if resume.personal.location:
        contact_parts.append(f'<span class="contact-item">📍 <span class="editable" data-field="location">{esc(resume.personal.location)}</span></span>')
    if contact_parts:
        parts.append(f'<div class="contact-bar contact-bar-center">{"  ".join(contact_parts)}</div>')
    parts.append('</header>')
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
    from app.utils.arabic import contains_arabic as _has_ar
    en_skills = [s for s in resume.skills if not _has_ar(s)]
    if en_skills:
        parts.append(_section("SKILLS", _bullet_list(en_skills)))
    en_tech = [s for s in resume.technical_skills if not _has_ar(s)]
    if en_tech:
        parts.append(_section("TECHNICAL SKILLS", _bullet_list(en_tech)))
    if resume.languages:
        lang_items = [f"{l.name} ({l.level})" if l.level else l.name for l in resume.languages]
        parts.append(_section("LANGUAGES", _bullet_list(lang_items)))
    parts.append('</div>')
    parts.append('</div>')
    return "".join(parts)


# ===========================================================================
# TEMPLATE 3: Arabic Single-Column
# ===========================================================================

def render_arabic_single_column(resume: ResumeData) -> str:
    parts = ['<div class="a4-page a4-single a4-ar" id="resume-document" dir="rtl">']
    name_ar = resume.personal.name_ar or resume.personal.name or ""
    parts.append('<header class="resume-header resume-header-center">')
    if name_ar:
        parts.append(f'<h1 class="editable header-name-center" data-field="name_ar" dir="rtl">{esc(name_ar)}</h1>')
    contact_parts = []
    if resume.personal.email:
        contact_parts.append(f'<span class="contact-item">✉️ <a href="mailto:{esc(resume.personal.email)}" class="contact-link editable" data-field="email" dir="ltr">{esc(resume.personal.email)}</a></span>')
    if resume.personal.phone:
        contact_parts.append(f'<span class="contact-item">📞 <a href="tel:{esc(resume.personal.phone)}" class="contact-link editable" data-field="phone" dir="ltr">{esc(resume.personal.phone)}</a></span>')
    if resume.personal.location:
        contact_parts.append(f'<span class="contact-item">📍 <span class="editable" data-field="location">{esc(resume.personal.location)}</span></span>')
    if contact_parts:
        parts.append(f'<div class="contact-bar contact-bar-center">{"  ".join(contact_parts)}</div>')
    parts.append('</header>')
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
    from app.utils.arabic import contains_arabic as _has_ar
    ar_skills = [s for s in resume.skills if _has_ar(s)] or resume.skills
    if ar_skills:
        parts.append(_section("المهارات", _bullet_list(ar_skills)))
    ar_tech = [s for s in resume.technical_skills if _has_ar(s)] or resume.technical_skills
    if ar_tech:
        parts.append(_section("المهارات التقنية", _bullet_list(ar_tech)))
    if resume.languages:
        lang_items = [f"{l.name} ({l.level})" if l.level else l.name for l in resume.languages]
        parts.append(_section("اللغات", _bullet_list(lang_items)))
    parts.append('</div>')
    parts.append('</div>')
    return "".join(parts)
