"""OFFICIAL MASTER TEMPLATE RENDERER — matches the provided specification.

Layout: centered header + TWO SEPARATE COLUMNS (English left, Arabic right).
Each column has its own sections independently. Template is FIXED, data is dynamic.
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
        parts.append(f'<span class="item-title">{esc(position)}</span>')
    if company:
        parts.append(f'<span class="item-subtitle">{esc(company)}</span>')
    if date_str:
        parts.append(f'<span class="item-date">{esc(date_str)}</span>')
    parts.append('</div>')
    if bullets:
        items = "".join(f"<li>{esc(b)}</li>" for b in bullets if b)
        if items:
            parts.append(f'<ul class="item-achievements">{items}</ul>')
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
        parts.append(f'<span class="item-title">{esc(degree)}</span>')
    if institution:
        parts.append(f'<span class="item-subtitle">{esc(institution)}</span>')
    if year:
        parts.append(f'<span class="item-date">{esc(year)}</span>')
    if gpa:
        parts.append(f'<span class="item-date">GPA: {esc(gpa)}</span>')
    parts.append('</div></div>')
    return "".join(parts)


def _bullet_list(items: List[str]) -> str:
    if not items:
        return ""
    lis = "".join(f"<li>{esc(item)}</li>" for item in items if item)
    return f'<ul class="list">{lis}</ul>' if lis else ""


# ---------------------------------------------------------------------------
# RENDERER
# ---------------------------------------------------------------------------

def render_official_bilingual_master(resume: ResumeData) -> str:
    parts = ['<div class="cv-root obm-master" data-lang="bilingual">']

    # ===== HEADER (centered) =====
    name_en = resume.personal.name_en or resume.personal.name or ""
    name_ar = resume.personal.name_ar or resume.personal.name or ""
    parts.append('<div class="obm-header">')
    if name_en:
        parts.append(f'<div class="obm-name-en" dir="ltr">{esc(name_en)}</div>')
    if name_ar:
        parts.append(f'<div class="obm-name-ar" dir="rtl">{esc(name_ar)}</div>')
    contact_parts = []
    if resume.personal.email:
        contact_parts.append(_contact_ltr(resume.personal.email))
    if resume.personal.phone:
        contact_parts.append(_contact_ltr(resume.personal.phone))
    if resume.personal.location:
        contact_parts.append(esc(resume.personal.location))
    if resume.personal.linkedin:
        contact_parts.append(_contact_ltr(resume.personal.linkedin))
    if contact_parts:
        parts.append(f'<div class="obm-contact-bar">{" | ".join(contact_parts)}</div>')
    parts.append('</div>')

    # ===== TWO SEPARATE COLUMNS =====
    parts.append('<div class="obm-columns">')

    # --- ENGLISH COLUMN (left) ---
    parts.append('<div class="obm-column obm-english" dir="ltr">')
    sum_en = resume.summary_text("en")
    if sum_en:
        parts.append(f'<section class="section"><h2 class="section-title">CAREER OBJECTIVE</h2><p class="section-content">{esc(sum_en)}</p></section>')
    if resume.experience:
        parts.append('<section class="section"><h2 class="section-title">EXPERIENCE</h2>')
        for e in resume.experience:
            parts.append(_exp_item(e, "en"))
        parts.append('</section>')
    if resume.education:
        parts.append('<section class="section"><h2 class="section-title">EDUCATION</h2>')
        for ed in resume.education:
            parts.append(_edu_item(ed, "en"))
        parts.append('</section>')
    if resume.courses:
        parts.append(f'<section class="section"><h2 class="section-title">COURSES</h2>{_bullet_list(resume.courses)}</section>')
    all_skills = resume.skills + resume.soft_skills
    if all_skills:
        parts.append(f'<section class="section"><h2 class="section-title">SKILLS</h2>{_bullet_list(all_skills)}</section>')
    if resume.technical_skills:
        parts.append(f'<section class="section"><h2 class="section-title">TECHNICAL SKILLS</h2>{_bullet_list(resume.technical_skills)}</section>')
    if resume.certifications:
        cert_names = [c.name if hasattr(c, "name") else str(c) for c in resume.certifications]
        parts.append(f'<section class="section"><h2 class="section-title">CERTIFICATIONS</h2>{_bullet_list(cert_names)}</section>')
    if resume.languages:
        lang_items = [f"{l.name} – {l.level}" if l.level else l.name for l in resume.languages]
        parts.append(f'<section class="section"><h2 class="section-title">LANGUAGES</h2>{_bullet_list(lang_items)}</section>')
    parts.append('</div>')

    # --- ARABIC COLUMN (right) ---
    parts.append('<div class="obm-column obm-arabic" dir="rtl">')
    sum_ar = resume.summary_text("ar")
    if sum_ar:
        parts.append(f'<section class="section"><h2 class="section-title">الهدف الوظيفي</h2><p class="section-content">{esc(sum_ar)}</p></section>')
    if resume.experience:
        parts.append('<section class="section"><h2 class="section-title">الخبرات المهنية</h2>')
        for e in resume.experience:
            parts.append(_exp_item(e, "ar"))
        parts.append('</section>')
    if resume.education:
        parts.append('<section class="section"><h2 class="section-title">التعليم</h2>')
        for ed in resume.education:
            parts.append(_edu_item(ed, "ar"))
        parts.append('</section>')
    if resume.courses:
        parts.append(f'<section class="section"><h2 class="section-title">الدورات</h2>{_bullet_list(resume.courses)}</section>')
    if all_skills:
        parts.append(f'<section class="section"><h2 class="section-title">المهارات</h2>{_bullet_list(all_skills)}</section>')
    if resume.technical_skills:
        parts.append(f'<section class="section"><h2 class="section-title">المهارات التقنية</h2>{_bullet_list(resume.technical_skills)}</section>')
    if resume.certifications:
        cert_names = [c.name if hasattr(c, "name") else str(c) for c in resume.certifications]
        parts.append(f'<section class="section"><h2 class="section-title">الشهادات</h2>{_bullet_list(cert_names)}</section>')
    if resume.languages:
        lang_items = [f"{l.name} – {l.level}" if l.level else l.name for l in resume.languages]
        parts.append(f'<section class="section"><h2 class="section-title">اللغات</h2>{_bullet_list(lang_items)}</section>')
    parts.append('</div>')

    parts.append('</div>')  # columns
    parts.append('</div>')  # cv-root
    return "".join(parts)
