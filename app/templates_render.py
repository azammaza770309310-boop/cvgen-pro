"""OFFICIAL MASTER BILINGUAL TEMPLATE — matches reference PDF exactly.

Reference: CVGen Pro - مولّد السير الذاتية الاحترافي.pdf
See: official-template-measurements.md

Layout (row-based, matching the PDF):
  - Single A4 page. Header (name + contact) + full-width header divider.
  - 6 section ROWS. Each row: EN heading (left) + AR heading (right) on the
    same baseline, then a FULL-WIDTH section divider (spans both columns),
    then EN content (left) + AR content (right).
  - No vertical divider between columns — only a ~10mm gap.
  - 6 sections in official order:
      1. CAREER OBJECTIVE / الهدف المهني
      2. PROFESSIONAL EXPERIENCE / الخبرة العملية
      3. EDUCATION / المؤهلات العلمية
      4. SKILLS / المهارات
      5. COURSES & CERTIFICATIONS / الدورات والشهادات
      6. LANGUAGES / اللغات
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


def _section_row(title_en: str, title_ar: str, body_en: str, body_ar: str) -> str:
    """Render one section as a ROW matching the official PDF layout.

    EN heading (left) + AR heading (right) on the same baseline, then a
    full-width divider spanning both columns, then EN content (left) +
    AR content (right). This mirrors the reference PDF exactly.
    """
    return (
        '<div class="section-row">'
        '<div class="section-headings">'
        f'<h2 class="editable section-heading-en">{esc(title_en)}</h2>'
        f'<h2 class="editable section-heading-ar">{esc(title_ar)}</h2>'
        '</div>'
        '<hr class="section-divider">'
        '<div class="section-body">'
        f'<div class="body-en">{body_en}</div>'
        f'<div class="body-ar">{body_ar}</div>'
        '</div>'
        '</div>'
    )


# ---------------------------------------------------------------------------
# RENDERER
# ---------------------------------------------------------------------------

def render_official_bilingual_master(resume: ResumeData) -> str:
    """Render the resume matching the official reference PDF (row-based layout).

    See official-template-measurements.md for the exact specs this implements.
    """
    from app.utils.arabic import contains_arabic
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
    # Contact bar — NOT blue (reference PDF uses dark slate #364153)
    contact_parts = []
    if resume.personal.email:
        contact_parts.append(f'<span class="contact-item"><svg class="contact-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#364153" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 5L2 7"/></svg> <a href="mailto:{esc(resume.personal.email)}" class="contact-link editable" data-field="email" dir="ltr">{esc(resume.personal.email)}</a></span>')
    if resume.personal.phone:
        contact_parts.append(f'<span class="contact-item"><svg class="contact-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#364153" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg> <a href="tel:{esc(resume.personal.phone)}" class="contact-link editable" data-field="phone" dir="ltr">{esc(resume.personal.phone)}</a></span>')
    if resume.personal.location:
        contact_parts.append(f'<span class="contact-item"><svg class="contact-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#364153" stroke-width="2"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg> <span class="editable" data-field="location">{esc(resume.personal.location)}</span></span>')
    if contact_parts:
        parts.append(f'<div class="contact-bar">{"  ".join(contact_parts)}</div>')
    parts.append('</header>')

    # ===== HEADER DIVIDER (full width, solid black) =====
    parts.append('<hr class="header-divider">')

    # ===== SECTION ROWS (official order from the reference PDF) =====
    # 1. CAREER OBJECTIVE / الهدف المهني
    sum_en = resume.summary_text("en")
    sum_ar = resume.summary_text("ar")
    if sum_en or sum_ar:
        body_en = f'<p class="editable" data-field="summary_en">{esc(sum_en)}</p>' if sum_en else ""
        body_ar = f'<p class="editable" data-field="summary_ar">{esc(sum_ar)}</p>' if sum_ar else ""
        parts.append(_section_row("CAREER OBJECTIVE", "الهدف المهني", body_en, body_ar))

    # 2. PROFESSIONAL EXPERIENCE / الخبرة العملية
    if resume.experience:
        body_en = "".join(_exp_item(e, "en") for e in resume.experience)
        body_ar = "".join(_exp_item(e, "ar") for e in resume.experience)
        if body_en or body_ar:
            parts.append(_section_row("PROFESSIONAL EXPERIENCE", "الخبرة العملية", body_en, body_ar))

    # 3. EDUCATION / المؤهلات العلمية
    if resume.education:
        body_en = "".join(_edu_item(ed, "en") for ed in resume.education)
        body_ar = "".join(_edu_item(ed, "ar") for ed in resume.education)
        if body_en or body_ar:
            parts.append(_section_row("EDUCATION", "المؤهلات العلمية", body_en, body_ar))

    # 4. SKILLS / المهارات
    # Merge generic skills + technical_skills into one SKILLS section (matching
    # the reference PDF which has a single SKILLS section, no separate technical).
    en_skills = resume.skills_en or [s for s in resume.skills if not contains_arabic(s)]
    en_tech = resume.technical_skills_en or [s for s in resume.technical_skills if not contains_arabic(s)]
    ar_skills = resume.skills_ar or [s for s in resume.skills if contains_arabic(s)]
    ar_tech = resume.technical_skills_ar or [s for s in resume.technical_skills if contains_arabic(s)]
    en_all = en_skills + en_tech
    ar_all = ar_skills + ar_tech
    if en_all or ar_all:
        body_en = _bullet_list(en_all)
        body_ar = _bullet_list(ar_all)
        parts.append(_section_row("SKILLS", "المهارات", body_en, body_ar))

    # 5. COURSES & CERTIFICATIONS / الدورات والشهادات
    if resume.courses or resume.certifications:
        en_items = list(resume.courses)
        ar_items = list(resume.courses)  # courses are language-neutral titles
        for cert in resume.certifications:
            en_items.append(cert.name)
            ar_items.append(cert.name)
        body_en = _bullet_list(en_items)
        body_ar = _bullet_list(ar_items)
        if body_en or body_ar:
            parts.append(_section_row("COURSES & CERTIFICATIONS", "الدورات والشهادات", body_en, body_ar))

    # 6. LANGUAGES / اللغات
    if resume.languages:
        lang_items_en = [f"{l.name} ({l.level})" if l.level else l.name for l in resume.languages]
        # For the Arabic column, translate the language name if an Arabic name
        # is available; otherwise keep it (language names are often universal).
        lang_items_ar = []
        for l in resume.languages:
            nm = l.name_ar or l.name
            lang_items_ar.append(f"{nm} ({l.level})" if l.level else nm)
        body_en = _bullet_list(lang_items_en)
        body_ar = _bullet_list(lang_items_ar)
        if body_en or body_ar:
            parts.append(_section_row("LANGUAGES", "اللغات", body_en, body_ar))

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
        contact_parts.append(f'<span class="contact-item"><svg class="contact-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#364153" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 5L2 7"/></svg> <a href="mailto:{esc(resume.personal.email)}" class="contact-link editable" data-field="email" dir="ltr">{esc(resume.personal.email)}</a></span>')
    if resume.personal.phone:
        contact_parts.append(f'<span class="contact-item"><svg class="contact-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#364153" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg> <a href="tel:{esc(resume.personal.phone)}" class="contact-link editable" data-field="phone" dir="ltr">{esc(resume.personal.phone)}</a></span>')
    if resume.personal.location:
        contact_parts.append(f'<span class="contact-item"><svg class="contact-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#364153" stroke-width="2"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg> <span class="editable" data-field="location">{esc(resume.personal.location)}</span></span>')
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
        contact_parts.append(f'<span class="contact-item"><svg class="contact-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#364153" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 5L2 7"/></svg> <a href="mailto:{esc(resume.personal.email)}" class="contact-link editable" data-field="email" dir="ltr">{esc(resume.personal.email)}</a></span>')
    if resume.personal.phone:
        contact_parts.append(f'<span class="contact-item"><svg class="contact-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#364153" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg> <a href="tel:{esc(resume.personal.phone)}" class="contact-link editable" data-field="phone" dir="ltr">{esc(resume.personal.phone)}</a></span>')
    if resume.personal.location:
        contact_parts.append(f'<span class="contact-item"><svg class="contact-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#364153" stroke-width="2"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg> <span class="editable" data-field="location">{esc(resume.personal.location)}</span></span>')
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


# ===========================================================================
# TEMPLATE 4: Executive Arabic (executive_ar)
# Clean RTL executive layout with Tajawal font.
# Implements the EXACT HTML structure provided by the user:
#   - Centered name (26px, #111) + centered contact line (14px, #444, pipe-separated)
#   - HR (2px solid #222)
#   - Fixed section order: الهدف الوظيفي → التعليم → الخبرات المهنية → المهارات والدورات
#   - Education: list-style:none, padding-right:0
#   - Experience/Skills: list-style:square, padding-right:20px
# ===========================================================================

def render_executive_ar(resume: ResumeData) -> str:
    """Executive Arabic template — RTL, Tajawal font, formal clean layout."""
    name = resume.personal.name_ar or resume.personal.name_en or resume.personal.name or ""
    email = resume.personal.email or ""
    phone = resume.personal.phone or ""
    location = resume.personal.location or ""
    summary = resume.summary_text("ar") or resume.summary_text("en") or ""

    # Build contact line: email | phone | location (pipe-separated)
    contact_parts = []
    if email:
        contact_parts.append(f'<span class="editable" data-field="email" dir="ltr">{esc(email)}</span>')
    if phone:
        contact_parts.append(f'<span class="editable" data-field="phone" dir="ltr">{esc(phone)}</span>')
    if location:
        contact_parts.append(f'<span class="editable" data-field="location">{esc(location)}</span>')
    contact_line = " | ".join(contact_parts)

    # Education items (list-style:none, padding-right:0)
    edu_items = ""
    if resume.education:
        for edu in resume.education:
            degree = edu.degree_ar or edu.degree_en or edu.degree or ""
            institution = edu.institution_ar or edu.institution_en or edu.institution or ""
            edu_items += f'<li style="margin-bottom: 5px;"><strong class="editable" data-field="degree">{esc(degree)}</strong> - <span class="editable" data-field="institution">{esc(institution)}</span></li>'

    # Experience items (list-style:square, padding-right:20px)
    exp_items = ""
    if resume.experience:
        for exp in resume.experience:
            title = exp.title_ar or exp.title_en or exp.title or ""
            description = exp.description or ""
            if not description and exp.bullets_ar:
                description = " ".join(exp.bullets_ar)
            elif not description and exp.bullets_en:
                description = " ".join(exp.bullets_en)
            elif not description and exp.bullets:
                description = " ".join(exp.bullets)
            exp_items += f'<li style="margin-bottom: 10px;"><strong class="editable" data-field="title">{esc(title)}</strong><br><span class="editable" data-field="description">{esc(description)}</span></li>'

    # Skills & Courses (combined, list-style:square, padding-right:20px)
    skill_items = ""
    skills_and_courses = []
    for s in resume.skills:
        if s:
            skills_and_courses.append(s)
    for c in resume.courses:
        if c:
            skills_and_courses.append(c)
    if skills_and_courses:
        for sk in skills_and_courses:
            skill_items += f'<li class="editable">{esc(sk)}</li>'

    return f'''<div dir="rtl" style="font-family: 'Tajawal', sans-serif; text-align: right; color: #000; padding: 30px; line-height: 1.7;" class="a4-page" id="resume-document">
    <h1 style="text-align: center; color: #111; margin-bottom: 5px; font-size: 26px;" class="editable" data-field="name_ar">{esc(name)}</h1>
    <p style="text-align: center; font-size: 14px; color: #444; margin-top: 0;">{contact_line}</p>
    <hr style="border: 0; border-top: 2px solid #222; margin: 15px 0;">

    <h3 style="color: #222; font-size: 18px; margin-bottom: 5px;">الهدف الوظيفي</h3>
    <p style="font-size: 14px; margin-top: 0;" class="editable" data-field="summary_ar">{esc(summary)}</p>

    <h3 style="color: #222; font-size: 18px; margin-bottom: 5px;">التعليم</h3>
    <ul style="font-size: 14px; list-style-type: none; padding-right: 0; margin-top: 0;">
        {edu_items}
    </ul>

    <h3 style="color: #222; font-size: 18px; margin-bottom: 5px;">الخبرات المهنية</h3>
    <ul style="font-size: 14px; list-style-type: square; padding-right: 20px; margin-top: 0;">
        {exp_items}
    </ul>

    <h3 style="color: #222; font-size: 18px; margin-bottom: 5px;">المهارات والدورات</h3>
    <ul style="font-size: 14px; list-style-type: square; padding-right: 20px; margin-top: 0;">
        {skill_items}
    </ul>
</div>'''


# ===========================================================================
# TEMPLATE 5: Executive English (executive_en)
# Clean LTR executive layout with Helvetica font.
# Implements the EXACT HTML structure provided by the user.
# ===========================================================================

def render_executive_en(resume: ResumeData) -> str:
    """Executive English template — LTR, Helvetica font, formal clean layout."""
    name = resume.personal.name_en or resume.personal.name or ""
    email = resume.personal.email or ""
    phone = resume.personal.phone or ""
    location = resume.personal.location or ""
    summary = resume.summary_text("en") or ""

    # Build contact line: email | phone | location (pipe-separated)
    contact_parts = []
    if email:
        contact_parts.append(f'<span class="editable" data-field="email" dir="ltr">{esc(email)}</span>')
    if phone:
        contact_parts.append(f'<span class="editable" data-field="phone" dir="ltr">{esc(phone)}</span>')
    if location:
        contact_parts.append(f'<span class="editable" data-field="location">{esc(location)}</span>')
    contact_line = " | ".join(contact_parts)

    # Education items (list-style:none, padding-left:0)
    edu_items = ""
    if resume.education:
        for edu in resume.education:
            degree = edu.degree_en or edu.degree or ""
            institution = edu.institution_en or edu.institution or ""
            edu_items += f'<li style="margin-bottom: 5px;"><strong class="editable" data-field="degree">{esc(degree)}</strong> - <span class="editable" data-field="institution">{esc(institution)}</span></li>'

    # Experience items (list-style:square, padding-left:20px)
    exp_items = ""
    if resume.experience:
        for exp in resume.experience:
            title = exp.title_en or exp.title or ""
            description = exp.description or ""
            if not description and exp.bullets_en:
                description = " ".join(exp.bullets_en)
            elif not description and exp.bullets:
                description = " ".join(exp.bullets)
            exp_items += f'<li style="margin-bottom: 10px;"><strong class="editable" data-field="title">{esc(title)}</strong><br><span class="editable" data-field="description">{esc(description)}</span></li>'

    # Skills & Courses (combined, list-style:square, padding-left:20px)
    skill_items = ""
    skills_and_courses = []
    for s in resume.skills:
        if s:
            skills_and_courses.append(s)
    for c in resume.courses:
        if c:
            skills_and_courses.append(c)
    if skills_and_courses:
        for sk in skills_and_courses:
            skill_items += f'<li class="editable">{esc(sk)}</li>'

    return f'''<div dir="ltr" style="font-family: 'Helvetica', 'Arial', sans-serif; text-align: left; color: #000; padding: 30px; line-height: 1.7;" class="a4-page" id="resume-document">
    <h1 style="text-align: center; color: #111; margin-bottom: 5px; font-size: 26px;" class="editable" data-field="name_en">{esc(name)}</h1>
    <p style="text-align: center; font-size: 14px; color: #444; margin-top: 0;">{contact_line}</p>
    <hr style="border: 0; border-top: 2px solid #222; margin: 15px 0;">

    <h3 style="color: #222; font-size: 18px; margin-bottom: 5px;">CAREER OBJECTIVE</h3>
    <p style="font-size: 14px; margin-top: 0;" class="editable" data-field="summary_en">{esc(summary)}</p>

    <h3 style="color: #222; font-size: 18px; margin-bottom: 5px;">EDUCATION</h3>
    <ul style="font-size: 14px; list-style-type: none; padding-left: 0; margin-top: 0;">
        {edu_items}
    </ul>

    <h3 style="color: #222; font-size: 18px; margin-bottom: 5px;">EXPERIENCE</h3>
    <ul style="font-size: 14px; list-style-type: square; padding-left: 20px; margin-top: 0;">
        {exp_items}
    </ul>

    <h3 style="color: #222; font-size: 18px; margin-bottom: 5px;">SKILLS &amp; COURSES</h3>
    <ul style="font-size: 14px; list-style-type: square; padding-left: 20px; margin-top: 0;">
        {skill_items}
    </ul>
</div>'''
