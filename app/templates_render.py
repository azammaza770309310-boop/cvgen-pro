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
    # CRITICAL: Strictly separate languages by language.
    # English column: ONLY English names + English levels
    # Arabic column: ONLY Arabic names + Arabic levels
    if resume.languages:
        # English level translations
        LEVEL_EN = {
            "native": "Native", "fluent": "Fluent", "advanced": "Advanced",
            "intermediate": "Intermediate", "beginner": "Beginner",
            "مبتدئ": "Beginner", "متوسط": "Intermediate", "متقدم": "Advanced",
            "بطلاقة": "Fluent", "اللغة الأم": "Native", "بطلاقة تامة": "Native",
        }
        # Arabic level translations
        LEVEL_AR = {
            "native": "اللغة الأم", "fluent": "بطلاقة", "advanced": "متقدم",
            "intermediate": "متوسط", "beginner": "مبتدئ",
            "Native": "اللغة الأم", "Fluent": "بطلاقة", "Advanced": "متقدم",
            "Intermediate": "متوسط", "Beginner": "مبتدئ",
        }
        # Arabic name translations for common languages
        LANG_NAME_AR = {
            "arabic": "العربية", "english": "الإنجليزية", "french": "الفرنسية",
            "german": "الألمانية", "spanish": "الإسبانية", "italian": "الإيطالية",
            "chinese": "الصينية", "japanese": "اليابانية", "korean": "الكورية",
            "russian": "الروسية", "turkish": "التركية", "hindi": "الهندية",
            "العربية": "العربية", "الإنجليزية": "الإنجليزية",
        }
        # English name translations for common languages
        LANG_NAME_EN = {
            "العربية": "Arabic", "الإنجليزية": "English", "الفرنسية": "French",
            "الألمانية": "German", "الإسبانية": "Spanish",
            "arabic": "Arabic", "english": "English", "french": "French",
            "german": "German", "spanish": "Spanish",
        }

        lang_items_en = []
        lang_items_ar = []
        for l in resume.languages:
            # --- English column: ONLY English ---
            # Use name_en if available, else translate from Arabic, else use name
            nm_en = l.name_en
            if not nm_en:
                # If name is Arabic, translate it; if English, keep it
                if contains_arabic(l.name):
                    nm_en = LANG_NAME_EN.get(l.name.lower(), LANG_NAME_EN.get(l.name, l.name))
                else:
                    nm_en = l.name
            # English level
            lvl_en = ""
            if l.level:
                lvl_lower = l.level.lower().strip()
                lvl_en = LEVEL_EN.get(lvl_lower, LEVEL_EN.get(l.level, l.level))
                # If the level is Arabic, translate to English
                if contains_arabic(lvl_en):
                    lvl_en = LEVEL_EN.get(lvl_en, l.level)
            lang_items_en.append(f"{nm_en} ({lvl_en})" if lvl_en else nm_en)

            # --- Arabic column: ONLY Arabic ---
            # Use name_ar if available, else translate from English, else use name
            nm_ar = l.name_ar
            if not nm_ar:
                if contains_arabic(l.name):
                    nm_ar = l.name  # Already Arabic
                else:
                    nm_ar = LANG_NAME_AR.get(l.name.lower(), LANG_NAME_AR.get(l.name, l.name))
            # Arabic level
            lvl_ar = ""
            if l.level:
                lvl_lower = l.level.lower().strip()
                lvl_ar = LEVEL_AR.get(lvl_lower, LEVEL_AR.get(l.level, l.level))
                # If the level is English, translate to Arabic
                if not contains_arabic(lvl_ar) and lvl_lower in LEVEL_AR:
                    lvl_ar = LEVEL_AR[lvl_lower]
            lang_items_ar.append(f"{nm_ar} ({lvl_ar})" if lvl_ar else nm_ar)

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
    # Gather English skills from ALL sources — filter OUT Arabic
    en_skills = []
    for s in (resume.skills_en or []):
        if s and not _has_ar(s) and s not in en_skills:
            en_skills.append(s)
    for s in (resume.skills or []):
        if s and not _has_ar(s) and s not in en_skills:
            en_skills.append(s)
    for s in (resume.soft_skills or []):
        if s and not _has_ar(s) and s not in en_skills:
            en_skills.append(s)
    if en_skills:
        parts.append(_section("SKILLS", _bullet_list(en_skills)))
    # Technical skills (universal — include regardless of language)
    en_tech = []
    for s in (resume.technical_skills_en or []):
        if s and s not in en_tech:
            en_tech.append(s)
    for s in (resume.technical_skills or []):
        if s and s not in en_tech:
            en_tech.append(s)
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
    # Gather Arabic skills from ALL sources (skills, skills_ar, technical_skills_ar)
    ar_skills = []
    for s in (resume.skills_ar or []):
        if s and s not in ar_skills:
            ar_skills.append(s)
    for s in (resume.skills or []):
        if s and _has_ar(s) and s not in ar_skills:
            ar_skills.append(s)
    for s in (resume.soft_skills or []):
        if s and _has_ar(s) and s not in ar_skills:
            ar_skills.append(s)
    # If no Arabic skills found, show all skills (fallback)
    if not ar_skills:
        ar_skills = [s for s in resume.skills if s]
    if ar_skills:
        parts.append(_section("المهارات", _bullet_list(ar_skills)))
    # Technical skills (universal — include regardless of language)
    ar_tech = []
    for s in (resume.technical_skills_ar or []):
        if s and s not in ar_tech:
            ar_tech.append(s)
    for s in (resume.technical_skills or []):
        if s and s not in ar_tech:
            ar_tech.append(s)
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

    # Skills & Courses (combined) — gather from ALL sources
    skill_items = ""
    skills_and_courses = []
    for source in [resume.skills, resume.skills_ar, resume.technical_skills, resume.technical_skills_ar, resume.soft_skills]:
        for s in (source or []):
            if s and s not in skills_and_courses:
                skills_and_courses.append(s)
    for c in resume.courses:
        if c and c not in skills_and_courses:
            skills_and_courses.append(c)
    if skills_and_courses:
        for sk in skills_and_courses:
            skill_items += f'<li class="editable" dir="auto" style="unicode-bidi: plaintext;">{esc(sk)}</li>'

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

    # Skills & Courses (combined) — gather from ALL sources
    skill_items = ""
    skills_and_courses = []
    for source in [resume.skills, resume.skills_en, resume.technical_skills, resume.technical_skills_en, resume.soft_skills]:
        for s in (source or []):
            if s and s not in skills_and_courses:
                skills_and_courses.append(s)
    for c in resume.courses:
        if c and c not in skills_and_courses:
            skills_and_courses.append(c)
    if skills_and_courses:
        for sk in skills_and_courses:
            skill_items += f'<li class="editable" dir="auto" style="unicode-bidi: plaintext;">{esc(sk)}</li>'

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


# ===========================================================================
# TEMPLATE 6: Professional Classic (Jinja2 HTML template)
# Single-column English with two-column skills, centered header
# ===========================================================================

def render_professional_classic(resume: ResumeData) -> str:
    """Professional Classic template — clean single-column with two-column skills."""
    from jinja2 import Template
    from pathlib import Path

    template_path = Path(__file__).parent / "templates" / "professional_classic.html"
    if not template_path.exists():
        return render_english_single_column(resume)  # fallback

    template_content = template_path.read_text(encoding="utf-8")
    template = Template(template_content)

    p = resume.personal
    name = p.name_en or p.name or ""
    email = p.email or ""
    phone = p.phone or ""
    location = p.location or ""
    objective = resume.summary_text("en") or resume.objective_text("en") or ""

    # Education
    education = []
    for edu in resume.education:
        education.append({
            "degree": edu.degree_en or edu.degree or "",
            "institution": edu.institution_en or edu.institution or "",
        })

    # Experience
    experience = []
    for exp in resume.experience:
        bullets = exp.bullets_en or exp.bullets or []
        experience.append({
            "title": exp.title_en or exp.title or "",
            "company": exp.company_en or exp.company or "",
            "description": exp.description or "",
            "bullets": bullets,
        })

    # Skills — gather from ALL sources (skills, skills_en, skills_ar, soft_skills)
    skills = []
    for source in [resume.skills, resume.skills_en, resume.skills_ar, resume.soft_skills]:
        for s in (source or []):
            if s and s not in skills:
                skills.append(s)
    # Technical skills (separate column) — gather from all sources
    technical_skills = []
    for source in [resume.technical_skills, resume.technical_skills_en, resume.technical_skills_ar]:
        for s in (source or []):
            if s and s not in technical_skills:
                technical_skills.append(s)

    # Courses
    courses = [c for c in resume.courses if c] if resume.courses else []

    # Languages
    languages = []
    for lang in resume.languages:
        nm = lang.name_en or lang.name or ""
        lvl = lang.level or ""
        entry = f"{nm} ({lvl})" if lvl else nm
        if entry:
            languages.append(entry)

    html = template.render(
        name=name,
        email=email,
        phone=phone,
        location=location,
        objective=objective,
        education=education,
        experience=experience,
        skills=skills,
        technical_skills=technical_skills,
        courses=courses,
        languages=languages,
    )
    return html
