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
# TEMPLATE 6: Professional Classic (direct HTML render)
# Single-column English with two-column skills, centered header
# All sections editable + email/phone as blue clickable links
# ===========================================================================

def render_professional_classic(resume: ResumeData) -> str:
    """Professional Classic — English-only, all sections editable, blue hyperlinks."""
    from app.utils.arabic import contains_arabic as _has_ar

    p = resume.personal
    name = p.name_en or p.name or ""
    email = p.email or ""
    phone = p.phone or ""
    location = p.location or ""
    objective = resume.summary_text("en") or resume.objective_text("en") or ""

    # Build contact line with BLUE clickable links for email + phone
    contact_parts = []
    if email:
        contact_parts.append(f'<a href="mailto:{esc(email)}" class="editable contact-link" data-field="email" dir="ltr" style="color:#2563eb;text-decoration:none;">{esc(email)}</a>')
    if phone:
        contact_parts.append(f'<a href="tel:{esc(phone)}" class="editable contact-link" data-field="phone" dir="ltr" style="color:#2563eb;text-decoration:none;">{esc(phone)}</a>')
    if location:
        contact_parts.append(f'<span class="editable" data-field="location" dir="auto">{esc(location)}</span>')
    contact_line = ' | '.join(contact_parts)

    # Education (each field editable)
    edu_html = ""
    for edu in resume.education:
        degree = edu.degree_en or edu.degree or ""
        institution = edu.institution_en or edu.institution or ""
        edu_html += f'<div style="margin-bottom:5px;"><strong class="editable" data-field="degree" dir="auto">{esc(degree)}</strong> - <span class="editable" data-field="institution" dir="auto">{esc(institution)}</span></div>'

    # Experience (each field editable, including bullets)
    exp_html = ""
    for exp in resume.experience:
        title = exp.title_en or exp.title or ""
        company = exp.company_en or exp.company or ""
        desc = exp.description or ""
        bullets = exp.bullets_en or exp.bullets or []
        exp_html += f'<div style="margin-bottom:10px;"><strong class="editable" data-field="title" dir="auto">{esc(title)}</strong>'
        if company:
            exp_html += f' - <span class="editable" data-field="company" dir="auto">{esc(company)}</span>'
        exp_html += '</div>'
        if desc:
            exp_html += f'<div class="editable" data-field="description" dir="auto" style="margin-bottom:4px;">{esc(desc)}</div>'
        if bullets:
            exp_html += '<ul style="margin:5px 0;padding-inline-start:20px;">'
            for b in bullets:
                exp_html += f'<li class="editable" data-field="bullet" dir="auto" style="unicode-bidi:plaintext;text-align:start;">{esc(b)}</li>'
            exp_html += '</ul>'

    # Courses (each editable)
    courses_html = ""
    if resume.courses:
        courses_html = '<ul style="margin:5px 0;padding-inline-start:20px;">'
        for c in resume.courses:
            if c:
                courses_html += f'<li class="editable" data-field="course" dir="auto" style="unicode-bidi:plaintext;text-align:start;">{esc(c)}</li>'
        courses_html += '</ul>'

    # Skills — ENGLISH ONLY (filter out Arabic), each editable
    skills = []
    for s in (resume.skills_en or []):
        if s and not _has_ar(s) and s not in skills:
            skills.append(s)
    for s in (resume.skills or []):
        if s and not _has_ar(s) and s not in skills:
            skills.append(s)
    for s in (resume.soft_skills or []):
        if s and not _has_ar(s) and s not in skills:
            skills.append(s)
    skills_html = ""
    if skills:
        skills_html = '<ul style="margin:5px 0;padding-inline-start:20px;">'
        for s in skills:
            skills_html += f'<li class="editable" data-field="skill" dir="auto" style="unicode-bidi:plaintext;text-align:start;">{esc(s)}</li>'
        skills_html += '</ul>'

    # Technical skills (universal), each editable
    tech_skills = []
    for s in (resume.technical_skills_en or []):
        if s and s not in tech_skills:
            tech_skills.append(s)
    for s in (resume.technical_skills or []):
        if s and s not in tech_skills:
            tech_skills.append(s)
    tech_html = ""
    if tech_skills:
        tech_html = '<ul style="margin:5px 0;padding-inline-start:20px;">'
        for s in tech_skills:
            tech_html += f'<li class="editable" data-field="technical_skill" dir="auto" style="unicode-bidi:plaintext;text-align:start;">{esc(s)}</li>'
        tech_html += '</ul>'

    # Languages (each editable)
    langs_html = ""
    if resume.languages:
        langs_html = '<ul style="margin:5px 0;padding-inline-start:20px;">'
        for lang in resume.languages:
            nm = lang.name_en or lang.name or ""
            lvl = lang.level or ""
            entry = f"{nm} ({lvl})" if lvl else nm
            langs_html += f'<li class="editable" data-field="language" dir="auto" style="unicode-bidi:plaintext;text-align:start;">{esc(entry)}</li>'
        langs_html += '</ul>'

    # Section title style (border-top, uppercase) — name font increased +3 to 31px
    st = 'style="font-size:16px;font-weight:bold;border-top:2px solid #000;margin-top:20px;padding-top:5px;margin-bottom:10px;text-transform:uppercase;text-align:start;"'
    ct = 'style="font-size:14px;line-height:1.6;text-align:start;"'

    return f'''<div class="a4-page" id="resume-document" dir="auto" style="font-family:'Noto Kufi Arabic','Noto Sans',Arial,sans-serif;background:#fff;padding:40px;color:#000;max-width:800px;margin:0 auto;box-sizing:border-box;">
    <h1 style="text-align:center;margin-bottom:5px;font-size:34px;text-transform:uppercase;" class="editable" data-field="name_en">{esc(name)}</h1>
    <div style="text-align:center;font-size:14px;color:#555;margin-bottom:25px;unicode-bidi:plaintext;">{contact_line}</div>

    <div {st}>CAREER OBJECTIVE</div>
    <div class="editable" data-field="summary_en" dir="auto" {ct}>{esc(objective)}</div>

    <div {st}>EDUCATION</div>
    <div {ct}>{edu_html}</div>

    <div {st}>EXPERIENCE</div>
    <div {ct}>{exp_html}</div>

    {"<div " + st + ">COURSES</div><div " + ct + ">" + courses_html + "</div>" if courses_html else ""}

    <div style="display:flex;justify-content:space-between;flex-wrap:wrap;margin-top:10px;">
        <div style="width:48%;">
            <div {st}>SKILLS</div>
            <div {ct}>{skills_html}</div>
        </div>
        {"<div style='width:48%;'><div " + st + ">TECHNICAL SKILLS</div><div " + ct + ">" + tech_html + "</div></div>" if tech_html else ""}
    </div>

    {"<div " + st + ">LANGUAGES</div><div " + ct + ">" + langs_html + "</div>" if langs_html else ""}
</div>'''


# ===========================================================================
# TEMPLATE 7: Arabic Classic (كلاسيكي عربي)
# Same clean layout as professional_classic but in Arabic (RTL):
# - dir="rtl", Arabic section titles, Arabic-only skills
# - All sections editable + blue email/phone hyperlinks
# - Two-column skills layout (المهارات + المهارات التقنية)
# ===========================================================================

def render_arabic_classic(resume: ResumeData) -> str:
    """Arabic Classic template — RTL, all sections editable, blue hyperlinks.
    Translates English content to Arabic when Arabic fields are empty."""
    from app.utils.arabic import contains_arabic as _has_ar

    # --- Translation maps (English → Arabic) ---
    SKILL_EN_AR = {
        "problem solving": "حل المشكلات", "teamwork": "العمل الجماعي",
        "communication": "التواصل الفعال", "time management": "إدارة الوقت",
        "attention to detail": "الاهتمام بالتفاصيل", "adaptability": "القدرة على التكيف",
        "continuous learning": "التعلم المستمر", "leadership": "القيادة",
        "creativity": "الإبداع", "critical thinking": "التفكير النقدي",
        "project management": "إدارة المشاريع", "decision making": "اتخاذ القرارات",
        "analytical skills": "المهارات التحليلية", "negotiation": "المفاوضة",
        "presentation skills": "مهارات العرض", "collaboration": "التعاون",
        "interpersonal skills": "المهارات الشخصية", "multitasking": "تعدد المهام",
        "stress management": "إدارة الضغط", "self-motivated": "ذاتي التحفيز",
        "hard working": "عمل جاد", "work under pressure": "العمل تحت الضغط",
        "ability to work under pressure": "القدرة على العمل تحت الضغط",
        # --- HR / Business / Admin skills ---
        "supplier coordination": "تنسيق الموردين",
        "social media management": "إدارة وسائل التواصل الاجتماعي",
        "communication & writing": "التواصل والكتابة",
        "organization & coordination": "التنظيم والتنسيق",
        "records management": "إدارة السجلات",
        "archiving": "الأرشفة",
        "cataloging & classification": "الفهرسة والتصنيف",
        "academic research": "البحث الأكاديمي",
        "proficiency in ms office suite": "إجادة حزمة مايكروسوفت أوفيس",
        "inventory management": "إدارة المخزون",
        "warehouse management": "إدارة المستودعات",
        "organization": "التنظيم",
        "supervision": "الإشراف",
        "team management": "إدارة الفرق",
        "communication & negotiation": "التواصل والتفاوض",
        "large-scale analysis": "التحليل على نطاق واسع",
        "hr consulting": "الاستشارات في الموارد البشرية",
        "procurement management": "إدارة المشتريات",
        "strategic planning": "التخطيط الاستراتيجي",
        "successful negotiation": "التفاوض الناجح",
        "decision making": "اتخاذ القرار",
        "customer service": "خدمة العملاء",
        "customer support": "دعم العملاء",
        "sales": "المبيعات",
        "marketing": "التسويق",
        "digital marketing": "التسويق الرقمي",
        "content writing": "كتابة المحتوى",
        "copywriting": "كتابة الإعلانات",
        "translation": "الترجمة",
        "data entry": "إدخال البيانات",
        "bookkeeping": "مسك الدفاتر",
        "accounting": "المحاسبة",
        "financial analysis": "التحليل المالي",
        "budgeting": "إعداد الميزانيات",
        "payroll": "الرواتب",
        "recruitment": "التوظيف",
        "training & development": "التدريب والتطوير",
        "employee relations": "علاقات الموظفين",
        "performance management": "إدارة الأداء",
        "compensation & benefits": "التعويضات والمزايا",
        "labor law": "قانون العمل",
        "contract management": "إدارة العقود",
        "vendor management": "إدارة الموردين",
        "supply chain": "سلسلة التوريد",
        "logistics": "اللوجستيات",
        "operations management": "إدارة العمليات",
        "quality management": "إدارة الجودة",
        "risk management": "إدارة المخاطر",
        "event planning": "تخطيط الفعاليات",
        "public relations": "العلاقات العامة",
        "research & analysis": "البحث والتحليل",
        "report writing": "كتابة التقارير",
        "filing & documentation": "الأرشفة والتوثيق",
        "office administration": "إدارة المكتب",
        "scheduling": "جدولة المواعيد",
        "meeting coordination": "تنسيق الاجتماعات",
        "phone etiquette": "آداب الهاتف",
        "email management": "إدارة البريد الإلكتروني",
        "time management": "إدارة الوقت",
        "conflict resolution": "حل النزاعات",
        "problem-solving": "حل المشكلات",
        "mentoring": "التوجيه",
        "coaching": "التدريب",
        "facilitation": "التيسير",
        "public speaking": "التحدث أمام الجمهور",
        "writing skills": "مهارات الكتابة",
        "editing": "التحرير",
        "proofreading": "التدقيق اللغوي",
        "typing": "الطباعة",
        "filing": "الأرشفة",
        "documentation": "التوثيق",
        "data analysis": "تحليل البيانات",
        "research skills": "مهارات البحث",
        "interviewing": "إجراء المقابلات",
        "onboarding": "التأهيل",
        "offboarding": "إنهاء الخدمة",
        "compliance": "الامتثال",
        "auditing": "التدقيق",
        "reporting": "إعداد التقارير",
        "forecasting": "التنبؤ",
        "strategic thinking": "التفكير الاستراتيجي",
        "change management": "إدارة التغيير",
        "process improvement": "تحسين العمليات",
        "business development": "تطوير الأعمال",
        "relationship building": "بناء العلاقات",
        "networking": "بناء الشبكات",
        "client management": "إدارة العملاء",
    }
    # Technical skills translations — comprehensive
    TECH_EN_AR = {
        "road design": "تصميم الطرق", "pavement engineering": "هندسة الرصف",
        "soil mechanics": "ميكانيكا التربة", "foundation engineering": "هندسة الأساسات",
        "construction quality control": "مراقبة جودة الإنشاء",
        "construction methods": "طرق الإنشاء", "construction practices": "ممارسات الإنشاء",
        "engineering drawings": "الرسومات الهندسية",
        "engineering drawings interpretation": "تفسير الرسومات الهندسية",
        "technical reports": "التقارير الفنية", "technical reports preparation": "إعداد التقارير الفنية",
        "quantity estimation": "تقدير الكميات", "quantity takeoff": "حساب الكميات",
        "project planning": "تخطيط المشاريع", "project coordination": "تنسيق المشاريع",
        "structural analysis": "التحليل الإنشائي", "structural design": "التصميم الإنشائي",
        "surveying": "المساحة", "land surveying": "مساحة الأراضي",
        "hydrology": "الهيدرولوجيا", "hydraulics": "الهيدروليكا",
        "environmental engineering": "الهندسة البيئية",
        "transportation engineering": "هندسة النقل",
        "geotechnical engineering": "الهندسة الجيوتقنية",
        "water resources": "موارد المياه", "water treatment": "معالجة المياه",
        "wastewater treatment": "معالجة مياه الصرف",
        "highway engineering": "هندسة الطرق السريعة",
        "traffic engineering": "هندسة المرور",
        "urban planning": "التخطيط الحضري",
        "building design": "تصميم المباني",
        "concrete design": "تصميم الخرسانة",
        "steel design": "تصميم المنشآت المعدنية",
        "cost estimation": "تقدير التكاليف",
        "risk assessment": "تقييم المخاطر",
        "safety management": "إدارة السلامة",
        "quality assurance": "ضمان الجودة",
        "microsoft office": "مايكروسوفت أوفيس",
        "microsoft word": "مايكروسوفت وورد",
        "microsoft excel": "مايكروسوفت إكسل",
        "microsoft powerpoint": "مايكروسوفت بوربوينت",
        "autocad": "أوتوكاد",
        "revit": "ريفيت",
        "sap2000": "SAP2000",
        "etabs": "ETABS",
        "primavera": "بريمافيرا",
        "ms project": "مايكروسوفت بروجكت",
        "gis": "نظم المعلومات الجغرافية",
        "python": "بايثون",
        "javascript": "جافا سكريبت",
        "react": "رياكت",
        "html": "HTML",
        "css": "CSS",
        "sql": "SQL",
        "database management": "إدارة قواعد البيانات",
        "web development": "تطوير الويب",
        "software development": "تطوير البرمجيات",
        "data analysis": "تحليل البيانات",
        "machine learning": "التعلم الآلي",
        "artificial intelligence": "الذكاء الاصطناعي",
        "cybersecurity": "الأمن السيبراني",
        "network security": "أمن الشبكات",
        "cloud computing": "الحوسبة السحابية",
        "devops": "ديف أوبس",
        "agile": "أجايل",
        "scrum": "سكرم",
    }
    LANG_NAME_AR = {
        "arabic": "العربية", "english": "الإنجليزية", "french": "الفرنسية",
        "german": "الألمانية", "spanish": "الإسبانية", "italian": "الإيطالية",
        "chinese": "الصينية", "japanese": "اليابانية", "korean": "الكورية",
        "russian": "الروسية", "turkish": "التركية", "hindi": "الهندية",
        "urdu": "الأردية", "persian": "الفارسية",
    }
    LEVEL_AR = {
        "native": "اللغة الأم", "fluent": "بطلاقة", "advanced": "متقدم",
        "intermediate": "متوسط", "beginner": "مبتدئ",
        "professional": "احترافي", "professional working proficiency": "إجادة عملية احترافية",
        "conversational": "محادثة", "basic": "أساسي",
    }
    LOCATION_AR = {
        "saudi arabia": "السعودية", "riyadh": "الرياض", "jeddah": "جدة",
        "mecca": "مكة", "medina": "المدينة", "taif": "الطائف",
        "dammam": "الدمام", "khobar": "الخبر", "tabuk": "تبوك",
        "abha": "أبها", "khamis mushait": "خميس مشيط",
        "united arab emirates": "الإمارات", "dubai": "دبي", "abu dhabi": "أبو ظبي",
        "kuwait": "الكويت", "qatar": "قطر", "doha": "الدوحة",
        "bahrain": "البحرين", "oman": "عمان", "egypt": "مصر", "cairo": "القاهرة",
        "jordan": "الأردن", "amman": "عمّان", "lebanon": "لبنان",
        "beirut": "بيروت", "iraq": "العراق", "baghdad": "بغداد",
    }

    def _translate_skill(s):
        """Translate an English skill (soft or technical) to Arabic."""
        if not s:
            return ""
        if _has_ar(s):
            return s
        lower = s.lower().strip()
        # Check soft skills map first
        if lower in SKILL_EN_AR:
            return SKILL_EN_AR[lower]
        # Check technical skills map
        if lower in TECH_EN_AR:
            return TECH_EN_AR[lower]
        # Try partial match for technical skills (e.g. "AutoCAD Civil 3D")
        for en, ar in TECH_EN_AR.items():
            if en in lower:
                return s.lower().replace(en, ar)
        return s  # No translation found

    def _translate_lang_name(name):
        """Translate language name to Arabic."""
        if not name:
            return ""
        if _has_ar(name):
            return name
        lower = name.lower().strip()
        return LANG_NAME_AR.get(lower, name)

    def _translate_level(level):
        """Translate proficiency level to Arabic."""
        if not level:
            return ""
        if _has_ar(level):
            return level
        lower = level.lower().strip()
        return LEVEL_AR.get(lower, level)

    def _translate_location(loc):
        """Translate common location names to Arabic."""
        if not loc:
            return ""
        if _has_ar(loc):
            return loc
        result = loc
        lower = loc.lower().strip()
        # Try full match first
        if lower in LOCATION_AR:
            return LOCATION_AR[lower]
        # Replace each known location in the string (handles "Riyadh, Saudi Arabia")
        for en, ar in sorted(LOCATION_AR.items(), key=lambda x: -len(x[0])):
            if en in result.lower():
                # Case-insensitive replace
                import re as _re
                result = _re.sub(_re.escape(en), ar, result, flags=_re.IGNORECASE)
        return result

    p = resume.personal
    # Name: prefer Arabic, fallback to English name (name might be transliterated)
    name = p.name_ar or p.name or p.name_en or ""
    email = p.email or ""
    phone = p.phone or ""
    location = _translate_location(p.location or "")
    # Objective: prefer Arabic summary, fallback to English.
    # If only English available, keep it (user can edit inline).
    objective = resume.summary_text("ar") or resume.summary_text("en") or resume.objective_text("ar") or resume.objective_text("en") or ""
    # Ensure objective is never empty — show placeholder if missing
    if not objective.strip():
        objective = "أدخل الهدف المهني هنا..."

    # Build contact line with BLUE clickable links
    contact_parts = []
    if email:
        contact_parts.append(f'<a href="mailto:{esc(email)}" class="editable contact-link" data-field="email" dir="ltr" style="color:#2563eb;text-decoration:none;">{esc(email)}</a>')
    if phone:
        contact_parts.append(f'<a href="tel:{esc(phone)}" class="editable contact-link" data-field="phone" dir="ltr" style="color:#2563eb;text-decoration:none;">{esc(phone)}</a>')
    if location:
        contact_parts.append(f'<span class="editable" data-field="location" dir="auto">{esc(location)}</span>')
    contact_line = ' | '.join(contact_parts)

    # Education (prefer Arabic, fallback to English — keep as-is if no translation)
    edu_html = ""
    for edu in resume.education:
        degree = edu.degree_ar or edu.degree_en or edu.degree or ""
        institution = edu.institution_ar or edu.institution_en or edu.institution or ""
        edu_html += f'<div style="margin-bottom:5px;"><strong class="editable" data-field="degree" dir="auto">{esc(degree)}</strong> - <span class="editable" data-field="institution" dir="auto">{esc(institution)}</span></div>'

    # Experience (prefer Arabic, fallback to English)
    exp_html = ""
    for exp in resume.experience:
        title = exp.title_ar or exp.title_en or exp.title or ""
        company = exp.company_ar or exp.company_en or exp.company or ""
        desc = exp.description or ""
        bullets = exp.bullets_ar or exp.bullets_en or exp.bullets or []
        exp_html += f'<div style="margin-bottom:10px;"><strong class="editable" data-field="title" dir="auto">{esc(title)}</strong>'
        if company:
            exp_html += f' - <span class="editable" data-field="company" dir="auto">{esc(company)}</span>'
        exp_html += '</div>'
        if desc:
            exp_html += f'<div class="editable" data-field="description" dir="auto" style="margin-bottom:4px;">{esc(desc)}</div>'
        if bullets:
            exp_html += '<ul style="margin:5px 0;padding-inline-start:20px;">'
            for b in bullets:
                exp_html += f'<li class="editable" data-field="bullet" dir="auto" style="unicode-bidi:plaintext;text-align:start;">{esc(b)}</li>'
            exp_html += '</ul>'

    # Courses (each editable)
    courses_html = ""
    if resume.courses:
        courses_html = '<ul style="margin:5px 0;padding-inline-start:20px;">'
        for c in resume.courses:
            if c:
                courses_html += f'<li class="editable" data-field="course" dir="auto" style="unicode-bidi:plaintext;text-align:start;">{esc(c)}</li>'
        courses_html += '</ul>'

    # Skills — Arabic ONLY. Gather from ALL sources (skills, skills_en, skills_ar, soft_skills).
    # The normalizer moves Arabic skills to skills_en, so we MUST check it.
    # Any skill that can't be translated to Arabic is EXCLUDED entirely.
    skills = []
    all_skill_sources = [
        resume.skills_ar or [],
        resume.skills or [],
        resume.skills_en or [],   # CRITICAL: normalizer puts Arabic skills here too!
        resume.soft_skills or [],
    ]
    for source in all_skill_sources:
        for s in source:
            if not s:
                continue
            translated = _translate_skill(s)
            # ONLY include if result is Arabic (either was Arabic or was translated)
            if translated and translated not in skills and _has_ar(translated):
                skills.append(translated)
            # If translation failed (still English) → EXCLUDE entirely
    skills_html = ""
    if skills:
        skills_html = '<ul style="margin:5px 0;padding-inline-start:20px;">'
        for s in skills:
            skills_html += f'<li class="editable" data-field="skill" dir="auto" style="unicode-bidi:plaintext;text-align:start;">{esc(s)}</li>'
        skills_html += '</ul>'

    # Technical skills — Arabic ONLY. Same rule: gather from ALL sources.
    tech_skills = []
    all_tech_sources = [
        resume.technical_skills_ar or [],
        resume.technical_skills or [],
        resume.technical_skills_en or [],   # CRITICAL: normalizer puts skills here too!
    ]
    for source in all_tech_sources:
        for s in source:
            if not s:
                continue
            translated = _translate_skill(s)
            if translated and translated not in tech_skills and _has_ar(translated):
                tech_skills.append(translated)
    tech_html = ""
    if tech_skills:
        tech_html = '<ul style="margin:5px 0;padding-inline-start:20px;">'
        for s in tech_skills:
            tech_html += f'<li class="editable" data-field="technical_skill" dir="auto" style="unicode-bidi:plaintext;text-align:start;">{esc(s)}</li>'
        tech_html += '</ul>'

    # Languages — translate names + levels to Arabic
    langs_html = ""
    if resume.languages:
        langs_html = '<ul style="margin:5px 0;padding-inline-start:20px;">'
        for lang in resume.languages:
            nm = lang.name_ar or _translate_lang_name(lang.name_en or lang.name)
            lvl = _translate_level(lang.level)
            entry = f"{nm} ({lvl})" if lvl else nm
            langs_html += f'<li class="editable" data-field="language" dir="auto" style="unicode-bidi:plaintext;text-align:start;">{esc(entry)}</li>'
        langs_html += '</ul>'

    # Section title style — name font increased +3 more to 34px
    st = 'style="font-size:16px;font-weight:bold;border-top:2px solid #000;margin-top:20px;padding-top:5px;margin-bottom:10px;text-align:start;"'
    ct = 'style="font-size:14px;line-height:1.6;text-align:start;"'

    return f'''<div class="a4-page" id="resume-document" dir="rtl" style="font-family:'Tajawal','Noto Kufi Arabic',Arial,sans-serif;background:#fff;padding:40px;color:#000;max-width:800px;margin:0 auto;box-sizing:border-box;">
    <h1 style="text-align:center;margin-bottom:5px;font-size:34px;" class="editable" data-field="name_ar">{esc(name)}</h1>
    <div style="text-align:center;font-size:14px;color:#555;margin-bottom:25px;unicode-bidi:plaintext;">{contact_line}</div>

    <div {st}>الهدف الوظيفي</div>
    <div class="editable" data-field="summary_ar" dir="auto" {ct}>{esc(objective)}</div>

    <div {st}>المؤهلات العلمية</div>
    <div {ct}>{edu_html}</div>

    <div {st}>الخبرات المهنية</div>
    <div {ct}>{exp_html}</div>

    {"<div " + st + ">الدورات</div><div " + ct + ">" + courses_html + "</div>" if courses_html else ""}

    <div style="display:flex;justify-content:space-between;flex-wrap:wrap;margin-top:10px;">
        <div style="width:48%;">
            <div {st}>المهارات</div>
            <div {ct}>{skills_html}</div>
        </div>
        {"<div style='width:48%;'><div " + st + ">المهارات التقنية</div><div " + ct + ">" + tech_html + "</div></div>" if tech_html else ""}
    </div>

    {"<div " + st + ">اللغات</div><div " + ct + ">" + langs_html + "</div>" if langs_html else ""}
</div>'''


# ===========================================================================
# TEMPLATE 8: Asymmetric Dark (تخطيط غير متماثل داكن)
# RTL asymmetric layout with dark sidebar on the right + pill-shaped contact bar
# Pixel-perfect implementation per technical specification
# ===========================================================================

def render_asymmetric_dark(resume: ResumeData) -> str:
    """Asymmetric Dark template — RTL, dark sidebar, pill contact, all editable."""
    from app.utils.arabic import contains_arabic as _has_ar

    # Translation maps (reuse from arabic_classic)
    SKILL_EN_AR = {
        "problem solving": "حل المشكلات", "teamwork": "العمل الجماعي",
        "communication": "التواصل الفعال", "time management": "إدارة الوقت",
        "attention to detail": "الاهتمام بالتفاصيل", "adaptability": "القدرة على التكيف",
        "continuous learning": "التعلم المستمر", "leadership": "القيادة",
        "creativity": "الإبداع", "critical thinking": "التفكير النقدي",
        "project management": "إدارة المشاريع", "decision making": "اتخاذ القرارات",
        "analytical skills": "المهارات التحليلية", "negotiation": "المفاوضة",
        "presentation skills": "مهارات العرض", "collaboration": "التعاون",
        "interpersonal skills": "المهارات الشخصية", "multitasking": "تعدد المهام",
        "stress management": "إدارة الضغط", "self-motivated": "ذاتي التحفيز",
        "hard working": "عمل جاد", "work under pressure": "العمل تحت الضغط",
        "ability to work under pressure": "القدرة على العمل تحت الضغط",
        "supplier coordination": "تنسيق الموردين", "social media management": "إدارة وسائل التواصل الاجتماعي",
        "communication & writing": "التواصل والكتابة", "organization & coordination": "التنظيم والتنسيق",
        "records management": "إدارة السجلات", "archiving": "الأرشفة",
        "cataloging & classification": "الفهرسة والتصنيف", "academic research": "البحث الأكاديمي",
        "proficiency in ms office suite": "إجادة حزمة مايكروسوفت أوفيس",
        "inventory management": "إدارة المخزون", "warehouse management": "إدارة المستودعات",
        "organization": "التنظيم", "supervision": "الإشراف", "team management": "إدارة الفرق",
        "communication & negotiation": "التواصل والتفاوض", "hr consulting": "الاستشارات في الموارد البشرية",
        "procurement management": "إدارة المشتريات", "strategic planning": "التخطيط الاستراتيجي",
        "successful negotiation": "التفاوض الناجح", "customer service": "خدمة العملاء",
        "customer support": "دعم العملاء", "sales": "المبيعات", "marketing": "التسويق",
        "digital marketing": "التسويق الرقمي", "content writing": "كتابة المحتوى",
        "data entry": "إدخال البيانات", "bookkeeping": "مسك الدفاتر", "accounting": "المحاسبة",
        "financial analysis": "التحليل المالي", "budgeting": "إعداد الميزانيات",
        "payroll": "الرواتب", "recruitment": "التوظيف", "training & development": "التدريب والتطوير",
        "employee relations": "علاقات الموظفين", "performance management": "إدارة الأداء",
        "contract management": "إدارة العقود", "supply chain": "سلسلة التوريد",
        "logistics": "اللوجستيات", "operations management": "إدارة العمليات",
        "quality management": "إدارة الجودة", "risk management": "إدارة المخاطر",
        "event planning": "تخطيط الفعاليات", "public relations": "العلاقات العامة",
        "report writing": "كتابة التقارير", "office administration": "إدارة المكتب",
        "scheduling": "جدولة المواعيد", "conflict resolution": "حل النزاعات",
        "mentoring": "التوجيه", "coaching": "التدريب", "public speaking": "التحدث أمام الجمهور",
        "writing skills": "مهارات الكتابة", "editing": "التحرير", "proofreading": "التدقيق اللغوي",
        "documentation": "التوثيق", "data analysis": "تحليل البيانات",
        "compliance": "الامتثال", "auditing": "التدقيق", "reporting": "إعداد التقارير",
        "strategic thinking": "التفكير الاستراتيجي", "change management": "إدارة التغيير",
        "process improvement": "تحسين العمليات", "business development": "تطوير الأعمال",
        "relationship building": "بناء العلاقات", "networking": "بناء الشبكات",
        "client management": "إدارة العملاء",
    }
    TECH_EN_AR = {
        "road design": "تصميم الطرق", "soil mechanics": "ميكانيكا التربة",
        "autocad": "أوتوكاد", "microsoft office": "مايكروسوفت أوفيس",
        "microsoft word": "مايكروسوفت وورد", "microsoft excel": "مايكروسوفت إكسل",
        "microsoft powerpoint": "مايكروسوفت بوربوينت", "python": "بايثون",
        "javascript": "جافا سكريبت", "react": "رياكت", "docker": "دوكر",
        "structural analysis": "التحليل الإنشائي", "surveying": "المساحة",
        "quantity estimation": "تقدير الكميات", "cybersecurity": "الأمن السيبراني",
        "gis": "نظم المعلومات الجغرافية", "revit": "ريفيت", "primavera": "بريمافيرا",
    }
    LANG_NAME_AR = {
        "arabic": "العربية", "english": "الإنجليزية", "french": "الفرنسية",
        "german": "الألمانية", "spanish": "الإسبانية",
    }
    LEVEL_AR = {
        "native": "اللغة الأم", "fluent": "بطلاقة", "advanced": "متقدم",
        "intermediate": "متوسط", "beginner": "مبتدئ", "professional": "احترافي",
        "professional working proficiency": "إجادة عملية احترافية",
    }

    def _tr(s):
        if not s: return ""
        if _has_ar(s): return s
        lower = s.lower().strip()
        if lower in SKILL_EN_AR: return SKILL_EN_AR[lower]
        if lower in TECH_EN_AR: return TECH_EN_AR[lower]
        return s

    p = resume.personal
    name = p.name_ar or p.name or ""
    email = p.email or ""
    phone = p.phone or ""
    location = p.location or ""
    if not _has_ar(location):
        for en, ar in {"saudi arabia":"السعودية","riyadh":"الرياض","jeddah":"جدة","taif":"الطائف","makkah":"مكة","medina":"المدينة","dammam":"الدمام"}.items():
            if en in location.lower():
                location = location.lower().replace(en, ar)
    objective = resume.summary_text("ar") or resume.summary_text("en") or resume.objective_text("ar") or resume.objective_text("en") or ""
    if not objective.strip():
        objective = " "  # Prevent empty rendering

    # --- Education (sidebar) — structured, not bullet points ---
    edu_items = ""
    for edu in resume.education:
        degree = edu.degree_ar or edu.degree_en or edu.degree or ""
        institution = edu.institution_ar or edu.institution_en or edu.institution or ""
        edu_items += '<div style="margin-bottom:10pt;">'
        edu_items += f'<div class="editable" data-field="degree" dir="auto" style="font-weight:700;font-size:10pt;color:#FFFFFF;line-height:1.4;">{esc(degree)}</div>'
        if institution:
            edu_items += f'<div class="editable" data-field="institution" dir="auto" style="font-weight:400;font-size:9pt;color:rgba(255,255,255,0.85);line-height:1.4;margin-top:2pt;">{esc(institution)}</div>'
        edu_items += '</div>'

    # --- Skills (sidebar) — Arabic only ---
    skill_items = ""
    skills = []
    for source in [resume.skills_ar or [], resume.skills or [], resume.skills_en or [], resume.soft_skills or []]:
        for s in source:
            t = _tr(s)
            if t and _has_ar(t) and t not in skills:
                skills.append(t)
    for s in skills:
        skill_items += f'<li class="editable" data-field="skill" dir="auto">{esc(s)}</li>'

    # --- Technical skills (sidebar) — Arabic only ---
    tech_items = ""
    tech_skills = []
    for source in [resume.technical_skills_ar or [], resume.technical_skills or [], resume.technical_skills_en or []]:
        for s in source:
            t = _tr(s)
            if t and _has_ar(t) and t not in tech_skills:
                tech_skills.append(t)
    for s in tech_skills:
        tech_items += f'<li class="editable" data-field="technical_skill" dir="auto">{esc(s)}</li>'

    # --- Experience (main content) — with increased spacing per hotfix ---
    exp_html = ""
    for exp in resume.experience:
        title = exp.title_ar or exp.title_en or exp.title or ""
        company = exp.company_ar or exp.company_en or exp.company or ""
        period = ""
        if exp.start_date and exp.end_date:
            period = f'<span dir="ltr">({esc(exp.start_date)} - {esc(exp.end_date)})</span>'
        elif exp.start_date and exp.current:
            period = f'<span dir="ltr">({esc(exp.start_date)} - حتى الآن)</span>'
        exp_html += f'<div style="margin-bottom:18pt;">'
        exp_html += f'<div style="font-weight:700;font-size:11pt;color:#2D3748;margin-bottom:6pt;"><span class="editable" data-field="title" dir="auto">{esc(title)}</span>'
        if company:
            exp_html += f' - <span class="editable" data-field="company" dir="auto">{esc(company)}</span>'
        if period:
            exp_html += f' {period}'
        exp_html += '</div>'
        desc = exp.description or ""
        if desc:
            exp_html += f'<div class="editable" data-field="description" dir="auto" style="font-size:9.5pt;color:#4A5568;line-height:1.6;margin-bottom:6pt;">{esc(desc)}</div>'
        bullets = exp.bullets_ar or exp.bullets_en or exp.bullets or []
        if bullets:
            exp_html += '<ul style="list-style-type:disc;padding-inline-start:14pt;margin:0;">'
            for b in bullets:
                exp_html += f'<li class="editable" data-field="bullet" dir="auto" style="font-size:9.5pt;color:#4A5568;line-height:1.6;margin-bottom:6pt;">{esc(b)}</li>'
            exp_html += '</ul>'
        exp_html += '</div>'

    # --- Contact pill items — single line, nowrap, BLUE clickable hyperlinks ---
    contact_items_html = ""
    if phone:
        contact_items_html += f'<a href="tel:{esc(phone)}" class="editable contact-link" data-field="phone" dir="ltr" style="display:flex;align-items:center;gap:4pt;font-size:9.5pt;color:#60a5fa;text-decoration:none;white-space:nowrap;"><span style="font-size:9pt;">📞</span>{esc(phone)}</a>'
    if email:
        contact_items_html += f'<a href="mailto:{esc(email)}" class="editable contact-link" data-field="email" dir="ltr" style="display:flex;align-items:center;gap:4pt;font-size:9.5pt;color:#60a5fa;text-decoration:none;white-space:nowrap;"><span style="font-size:9pt;">✉</span>{esc(email)}</a>'
    if location:
        contact_items_html += f'<span style="display:flex;align-items:center;gap:4pt;font-size:9.5pt;color:#FFFFFF;white-space:nowrap;"><span style="font-size:9pt;">📍</span><span class="editable" data-field="location" dir="auto">{esc(location)}</span></span>'

    # --- Languages (sidebar) ---
    lang_items = ""
    for lang in resume.languages:
        nm = lang.name_ar or LANG_NAME_AR.get((lang.name_en or lang.name or "").lower(), lang.name or "")
        lvl = LEVEL_AR.get((lang.level or "").lower(), lang.level or "")
        if _has_ar(lvl) == False and lvl:
            for en, ar in LEVEL_AR.items():
                if en in (lang.level or "").lower():
                    lvl = ar
                    break
        entry = f"{nm} ({lvl})" if lvl else nm
        lang_items += f'<li class="editable" data-field="language" dir="auto">{esc(entry)}</li>'

    # Pre-build conditional sections (avoid nested f-strings which break Python 3.11)
    tech_section_html = ""
    if tech_items:
        tech_section_html = (
            '<div style="font-weight:700;font-size:14pt;text-align:right;margin-top:12pt;margin-bottom:4pt;">المهارات التقنية</div>'
            '<div style="border-bottom:1pt solid rgba(255,255,255,0.4);margin-bottom:8pt;"></div>'
            '<ul style="list-style-type:disc;padding-inline-start:14pt;margin:0 0 18pt 0;color:#FFFFFF;">'
            + tech_items +
            '</ul>'
        )

    lang_section_html = ""
    if lang_items:
        lang_section_html = (
            '<div style="font-weight:700;font-size:14pt;text-align:right;margin-top:12pt;margin-bottom:4pt;">اللغات</div>'
            '<div style="border-bottom:1pt solid rgba(255,255,255,0.4);margin-bottom:8pt;"></div>'
            '<ul style="list-style-type:disc;padding-inline-start:14pt;margin:0;color:#FFFFFF;">'
            + lang_items +
            '</ul>'
        )

    return f'''<div class="a4-page" id="resume-document" dir="rtl" lang="ar" style="font-family:'Tajawal','Noto Kufi Arabic',Arial,sans-serif;background:#FFFFFF;color:#2D3748;padding:24pt;box-sizing:border-box;width:100%;max-width:210mm;min-height:297mm;margin:0 auto;-webkit-print-color-adjust:exact !important;print-color-adjust:exact !important;">

    <!-- ===== HEADER: Centered Name ===== -->
    <h1 class="editable" data-field="name_ar" style="text-align:center !important;font-size:32pt !important;font-weight:800 !important;color:#2D3748;width:100%;margin:0 0 16pt 0;">{esc(name)}</h1>

    <!-- ===== Contact Pill: Single line, nowrap ===== -->
    <div style="background-color:#2D3748;border-radius:20pt;padding:8pt 12pt;display:flex;flex-direction:row !important;flex-wrap:nowrap !important;justify-content:center;align-items:center;gap:16pt;-webkit-print-color-adjust:exact !important;print-color-adjust:exact !important;">
        {contact_items_html}
    </div>

    <!-- ===== MAIN BODY: Flexbox — dark sidebar on LEFT, white content on RIGHT ===== -->
    <div style="display:flex;flex-direction:row;width:100%;min-height:250mm;gap:16pt;margin-top:24pt;">

        <!-- ===== LEFT SIDEBAR (Dark) — 35%, one-sided radius (top-left), stretches to bottom ===== -->
        <div style="width:35%;min-height:100%;background-color:#2D3748;border-radius:12pt 0 0 0;padding:16pt;color:#FFFFFF;-webkit-print-color-adjust:exact !important;print-color-adjust:exact !important;">

            <!-- Education -->
            <div style="font-weight:700;font-size:14pt;text-align:right;margin-bottom:4pt;">المؤهلات العلمية</div>
            <div style="border-bottom:1pt solid rgba(255,255,255,0.4);margin-bottom:8pt;"></div>
            <div style="margin-bottom:18pt;">
                {edu_items}
            </div>

            <!-- Skills -->
            <div style="font-weight:700;font-size:14pt;text-align:right;margin-top:12pt;margin-bottom:4pt;">المهارات</div>
            <div style="border-bottom:1pt solid rgba(255,255,255,0.4);margin-bottom:8pt;"></div>
            <ul style="list-style-type:disc;padding-inline-start:14pt;margin:0 0 18pt 0;color:#FFFFFF;">
                {skill_items}
            </ul>

            <!-- Technical Skills -->
            {tech_section_html}

            <!-- Languages -->
            {lang_section_html}

        </div>

        <!-- ===== RIGHT MAIN CONTENT (White) — 65%, extends to bottom of page ===== -->
        <div style="width:65%;padding:0;color:#2D3748;min-height:100%;">

            <!-- Profile Summary -->
            <div style="font-weight:700;font-size:14pt;text-align:right;margin-bottom:4pt;">نبذة عني</div>
            <div style="border-bottom:1pt solid #2D3748;margin-bottom:8pt;"></div>
            <div class="editable" data-field="summary_ar" dir="auto" style="font-size:9.5pt;color:#4A5568;line-height:1.6;text-align:justify;margin-bottom:18pt;">{esc(objective)}</div>

            <!-- Professional Experience -->
            <div style="font-weight:700;font-size:14pt;text-align:right;margin-top:12pt;margin-bottom:4pt;">الخبرات المهنية</div>
            <div style="border-bottom:1pt solid #2D3748;margin-bottom:8pt;"></div>
            {exp_html}

        </div>
    </div>
</div>'''
