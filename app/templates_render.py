"""HTML renderers for all registered resume templates.

Each renderer receives a ResumeData and returns an HTML string (the resume body,
wrapped in a root .cv-root div with a per-template class). CSS for all templates
lives in static/css/templates.css and is shared between preview and PDF.

The number of templates is determined dynamically by the registry — never
hardcoded here.
"""
from __future__ import annotations

import html
from typing import List

from app.models.resume import ResumeData
from app.utils.arabic import contains_arabic


def esc(s: str) -> str:
    return html.escape(s or "")


def contact_val(value: str, lang: str = "en") -> str:
    """Escape a contact value. In RTL/Arabic columns, wrap with dir=ltr so
    emails, phones, and URLs render correctly."""
    if not value:
        return ""
    escaped = esc(value)
    if lang == "ar":
        return f'<span dir="ltr">{escaped}</span>'
    return escaped


def is_contact_value(value: str) -> bool:
    """Heuristic: emails, phones, URLs should be LTR-protected in RTL columns."""
    if not value:
        return False
    v = value.strip()
    if "@" in v and "." in v:
        return True
    if v.startswith(("http://", "https://", "www.")):
        return True
    if "linkedin.com" in v.lower() or "github.com" in v.lower():
        return True
    # phone-like: digits, +, spaces, dashes, parens
    digits = sum(c.isdigit() for c in v)
    if digits >= 7 and len(v) - digits <= 6:
        return True
    return False


def smart_val(value: str, lang: str = "en") -> str:
    """Escape + auto-wrap contact values with dir=ltr in Arabic columns."""
    if not value:
        return ""
    if lang == "ar" and is_contact_value(value):
        return contact_val(value, "ar")
    return esc(value)


def bullets_for(exp, lang: str) -> List[str]:
    if lang == "ar":
        return exp.bullets_ar or exp.bullets
    if lang == "en":
        return exp.bullets_en or exp.bullets
    return exp.bullets


def title_for(exp, lang: str) -> str:
    if lang == "ar":
        return exp.title_ar or exp.title
    if lang == "en":
        return exp.title_en or exp.title
    return exp.title


def company_for(exp, lang: str) -> str:
    if lang == "ar":
        return exp.company_ar or exp.company
    if lang == "en":
        return exp.company_en or exp.company
    return exp.company


def degree_for(ed, lang: str) -> str:
    if lang == "ar":
        return ed.degree_ar or ed.degree
    if lang == "en":
        return ed.degree_en or ed.degree
    return ed.degree


def institution_for(ed, lang: str) -> str:
    if lang == "ar":
        return ed.institution_ar or ed.institution
    if lang == "en":
        return ed.institution_en or ed.institution
    return ed.institution


def name_for(resume: ResumeData, lang: str) -> str:
    if lang == "ar":
        return resume.personal.name_ar or resume.personal.name or resume.personal.name_en
    if lang == "en":
        return resume.personal.name_en or resume.personal.name or resume.personal.name_ar
    return resume.personal.name or resume.personal.name_en or resume.personal.name_ar


def title_pos_for(resume: ResumeData, lang: str) -> str:
    if lang == "ar":
        return resume.personal.title_ar or resume.personal.title
    if lang == "en":
        return resume.personal.title_en or resume.personal.title
    return resume.personal.title


def date_range(exp) -> str:
    parts = []
    if exp.start_date:
        parts.append(exp.start_date)
    if exp.end_date:
        parts.append("Present" if exp.current and exp.end_date.lower() in ("present", "now", "current", "حتى الآن", "الآن") else exp.end_date)
    elif exp.current:
        parts.append("Present")
    return " – ".join(parts) if parts else ""


def contact_line(resume: ResumeData, lang: str = "en") -> str:
    parts = []
    if resume.personal.email:
        parts.append(resume.personal.email)
    if resume.personal.phone:
        parts.append(resume.personal.phone)
    if resume.personal.location:
        parts.append(resume.personal.location)
    if resume.personal.linkedin:
        parts.append(resume.personal.linkedin)
    if resume.personal.website:
        parts.append(resume.personal.website)
    return " · ".join(parts)


def render_bullets(items: List[str]) -> str:
    if not items:
        return ""
    lis = "".join(f"<li>{esc(b)}</li>" for b in items if b)
    return f"<ul class='cv-bullets'>{lis}</ul>" if lis else ""


def skills_block(skills: List[str], label_en: str, label_ar: str = "", lang: str = "en") -> str:
    if not skills:
        return ""
    label = label_ar if lang == "ar" else label_en
    items = "".join(f"<span class='cv-skill-chip'>{esc(s)}</span>" for s in skills)
    return f"<div class='cv-section'><h3 class='cv-h'>{esc(label)}</h3><div class='cv-skills'>{items}</div></div>"


# ===========================================================================
# 1. ATS Classic
# ===========================================================================

def render_ats_classic(resume: ResumeData) -> str:
    lang = resume.lang or "en"
    name = name_for(resume, lang)
    title = title_pos_for(resume, lang)
    contact = contact_line(resume, lang)
    parts = [f"<div class='cv-root cv-ats-classic' data-lang='{lang}'>"]
    parts.append(f"<header class='cv-header'><h1 class='cv-name'>{esc(name)}</h1>")
    if title:
        parts.append(f"<div class='cv-title'>{esc(title)}</div>")
    if contact:
        parts.append(f"<div class='cv-contact'>{esc(contact)}</div>")
    parts.append("</header>")

    summary = resume.summary_text(lang)
    if summary:
        parts.append(f"<section class='cv-section'><h2 class='cv-h2'>{esc('ملخص' if lang=='ar' else 'Summary')}</h2><p>{esc(summary)}</p></section>")

    if resume.experience:
        parts.append(f"<section class='cv-section'><h2 class='cv-h2'>{esc('الخبرات' if lang=='ar' else 'Experience')}</h2>")
        for e in resume.experience:
            parts.append("<div class='cv-item break-inside-avoid'>")
            t = title_for(e, lang)
            c = company_for(e, lang)
            d = date_range(e)
            if t:
                parts.append(f"<div class='cv-item-title'>{esc(t)}</div>")
            if c or d:
                parts.append(f"<div class='cv-item-sub'>{esc(c)}{(' · '+d) if d else ''}</div>")
            if e.description:
                parts.append(f"<p>{esc(e.description)}</p>")
            parts.append(render_bullets(bullets_for(e, lang)))
            parts.append("</div>")
        parts.append("</section>")

    if resume.education:
        parts.append(f"<section class='cv-section'><h2 class='cv-h2'>{esc('التعليم' if lang=='ar' else 'Education')}</h2>")
        for ed in resume.education:
            parts.append("<div class='cv-item break-inside-avoid'>")
            deg = degree_for(ed, lang)
            inst = institution_for(ed, lang)
            if deg:
                parts.append(f"<div class='cv-item-title'>{esc(deg)}</div>")
            if inst or ed.year:
                parts.append(f"<div class='cv-item-sub'>{esc(inst)}{(' · '+ed.year) if ed.year else ''}</div>")
            parts.append("</div>")
        parts.append("</section>")

    all_skills = resume.skills + resume.technical_skills + resume.soft_skills
    if all_skills:
        parts.append(skills_block(all_skills, "Skills", "المهارات", lang))
    if resume.courses:
        parts.append(skills_block(resume.courses, "Courses", "الدورات", lang))
    if resume.certifications:
        certs = [c.name for c in resume.certifications]
        parts.append(skills_block(certs, "Certifications", "الشهادات", lang))
    if resume.languages:
        langs = [f"{l.name} ({l.level})" if l.level else l.name for l in resume.languages]
        parts.append(skills_block(langs, "Languages", "اللغات", lang))

    parts.append("</div>")
    return "".join(parts)


# ===========================================================================
# 2. Minimal Black (timeline + 30/70 split)
# ===========================================================================

def render_minimal_black(resume: ResumeData) -> str:
    lang = resume.lang or "en"
    name = name_for(resume, lang)
    title = title_pos_for(resume, lang)
    contact = contact_line(resume, lang)
    is_ar = lang == "ar"
    parts = [f"<div class='cv-root cv-minimal-black' data-lang='{lang}'>"]
    parts.append("<div class='cv-mb-grid'>")
    # left sidebar
    parts.append("<aside class='cv-mb-side'>")
    parts.append(f"<h1 class='cv-name'>{esc(name)}</h1>")
    if title:
        parts.append(f"<div class='cv-title'>{esc(title)}</div>")
    parts.append("<div class='cv-mb-contact'>")
    for f in (resume.personal.email, resume.personal.phone, resume.personal.location, resume.personal.linkedin, resume.personal.website):
        if f:
            parts.append(f"<div>{esc(f)}</div>")
    parts.append("</div>")
    all_skills = resume.skills + resume.technical_skills + resume.soft_skills
    if all_skills:
        parts.append(f"<h3 class='cv-h'>{esc('المهارات' if is_ar else 'Skills')}</h3><ul class='cv-mb-list'>{ ''.join(f'<li>{esc(s)}</li>' for s in all_skills) }</ul>")
    if resume.languages:
        lang_items = []
        for l in resume.languages:
            display = l.name + (" (" + l.level + ")" if l.level else "")
            lang_items.append("<li>" + esc(display) + "</li>")
        parts.append(f"<h3 class='cv-h'>{esc('اللغات' if is_ar else 'Languages')}</h3><ul class='cv-mb-list'>{ ''.join(lang_items) }</ul>")
    if resume.courses:
        parts.append(f"<h3 class='cv-h'>{esc('الدورات' if is_ar else 'Courses')}</h3><ul class='cv-mb-list'>{ ''.join(f'<li>{esc(c)}</li>' for c in resume.courses) }</ul>")
    parts.append("</aside>")
    # main
    parts.append("<main class='cv-mb-main'>")
    summary = resume.summary_text(lang)
    if summary:
        parts.append(f"<section class='cv-section'><h2 class='cv-h2'>{esc('ملخص' if is_ar else 'Profile')}</h2><p>{esc(summary)}</p></section>")
    if resume.experience:
        parts.append(f"<section class='cv-section'><h2 class='cv-h2'>{esc('الخبرات' if is_ar else 'Experience')}</h2><div class='cv-timeline'>")
        for e in resume.experience:
            parts.append("<div class='cv-tl-item break-inside-avoid'>")
            d = date_range(e)
            if d:
                parts.append(f"<div class='cv-tl-date'>{esc(d)}</div>")
            parts.append("<div class='cv-tl-body'>")
            t = title_for(e, lang); c = company_for(e, lang)
            if t:
                parts.append(f"<div class='cv-item-title'>{esc(t)}</div>")
            if c:
                parts.append(f"<div class='cv-item-sub'>{esc(c)}</div>")
            parts.append(render_bullets(bullets_for(e, lang)))
            parts.append("</div></div>")
        parts.append("</div></section>")
    if resume.education:
        parts.append(f"<section class='cv-section'><h2 class='cv-h2'>{esc('التعليم' if is_ar else 'Education')}</h2>")
        for ed in resume.education:
            parts.append("<div class='cv-item break-inside-avoid'>")
            parts.append(f"<div class='cv-item-title'>{esc(degree_for(ed, lang))}</div>")
            parts.append(f"<div class='cv-item-sub'>{esc(institution_for(ed, lang))}{(' · '+ed.year) if ed.year else ''}</div>")
            parts.append("</div>")
        parts.append("</section>")
    parts.append("</main>")
    parts.append("</div></div>")
    return "".join(parts)


# ===========================================================================
# 3. Modern Sidebar (dark sidebar + photo)
# ===========================================================================

def render_modern_sidebar(resume: ResumeData) -> str:
    lang = resume.lang or "en"
    name = name_for(resume, lang)
    title = title_pos_for(resume, lang)
    is_ar = lang == "ar"
    parts = [f"<div class='cv-root cv-modern-sidebar' data-lang='{lang}'>"]
    parts.append("<div class='cv-ms-grid'>")
    # sidebar
    parts.append("<aside class='cv-ms-side'>")
    initials = "".join([w[0] for w in (name.split()[:2]) if w])[:2].upper() or "CV"
    parts.append(f"<div class='cv-ms-photo'>{esc(initials)}</div>")
    parts.append(f"<h1 class='cv-ms-name'>{esc(name)}</h1>")
    if title:
        parts.append(f"<div class='cv-ms-title'>{esc(title)}</div>")
    parts.append("<div class='cv-ms-contact'>")
    for label, val in (("EMAIL", resume.personal.email), ("PHONE", resume.personal.phone), ("LOCATION", resume.personal.location), ("LINKEDIN", resume.personal.linkedin), ("WEB", resume.personal.website)):
        if val:
            parts.append(f"<div class='cv-ms-citem'><span class='cv-ms-clabel'>{label}</span><span>{esc(val)}</span></div>")
    parts.append("</div>")
    all_skills = resume.skills + resume.technical_skills + resume.soft_skills
    if all_skills:
        parts.append(f"<h3 class='cv-ms-h'>{esc('SKILLS' if not is_ar else 'المهارات')}</h3><div class='cv-ms-skills'>{ ''.join(f'<span>{esc(s)}</span>' for s in all_skills) }</div>")
    if resume.languages:
        parts.append(f"<h3 class='cv-ms-h'>{esc('LANGUAGES' if not is_ar else 'اللغات')}</h3><div class='cv-ms-skills'>{ ''.join(f'<span>{esc(l.name)}</span>' for l in resume.languages) }</div>")
    if resume.courses:
        parts.append(f"<h3 class='cv-ms-h'>{esc('COURSES' if not is_ar else 'الدورات')}</h3><div class='cv-ms-skills'>{ ''.join(f'<span>{esc(c)}</span>' for c in resume.courses) }</div>")
    parts.append("</aside>")
    # main
    parts.append("<main class='cv-ms-main'>")
    summary = resume.summary_text(lang)
    if summary:
        parts.append(f"<section class='cv-section'><h2 class='cv-ms-h2'>{esc('PROFILE' if not is_ar else 'ملخص')}</h2><p>{esc(summary)}</p></section>")
    if resume.experience:
        parts.append(f"<section class='cv-section'><h2 class='cv-ms-h2'>{esc('EXPERIENCE' if not is_ar else 'الخبرات')}</h2>")
        for e in resume.experience:
            parts.append("<div class='cv-item break-inside-avoid'>")
            parts.append(f"<div class='cv-item-title'>{esc(title_for(e, lang))}</div>")
            parts.append(f"<div class='cv-item-sub'>{esc(company_for(e, lang))}{(' · '+date_range(e)) if date_range(e) else ''}</div>")
            parts.append(render_bullets(bullets_for(e, lang)))
            parts.append("</div>")
        parts.append("</section>")
    if resume.education:
        parts.append(f"<section class='cv-section'><h2 class='cv-ms-h2'>{esc('EDUCATION' if not is_ar else 'التعليم')}</h2>")
        for ed in resume.education:
            parts.append("<div class='cv-item break-inside-avoid'>")
            parts.append(f"<div class='cv-item-title'>{esc(degree_for(ed, lang))}</div>")
            parts.append(f"<div class='cv-item-sub'>{esc(institution_for(ed, lang))}{(' · '+ed.year) if ed.year else ''}</div>")
            parts.append("</div>")
        parts.append("</section>")
    parts.append("</main></div></div>")
    return "".join(parts)


# ===========================================================================
# 4. Corporate Slate (navy header + slate sidebar)
# ===========================================================================

def render_corporate_slate(resume: ResumeData) -> str:
    lang = resume.lang or "en"
    name = name_for(resume, lang)
    title = title_pos_for(resume, lang)
    is_ar = lang == "ar"
    parts = [f"<div class='cv-root cv-corporate-slate' data-lang='{lang}'>"]
    parts.append(f"<header class='cv-cs-header'><h1 class='cv-name'>{esc(name)}</h1>{('<div class=cv-title>'+esc(title)+'</div>') if title else ''}</header>")
    parts.append("<div class='cv-cs-grid'>")
    parts.append("<aside class='cv-cs-side'>")
    parts.append(f"<h3 class='cv-cs-h'>{esc('CONTACT' if not is_ar else 'تواصل')}</h3>")
    for v in (resume.personal.email, resume.personal.phone, resume.personal.location, resume.personal.linkedin, resume.personal.website):
        if v:
            parts.append(f"<div class='cv-cs-citem'>{esc(v)}</div>")
    all_skills = resume.skills + resume.technical_skills + resume.soft_skills
    if all_skills:
        parts.append(f"<h3 class='cv-cs-h'>{esc('SKILLS' if not is_ar else 'المهارات')}</h3><ul class='cv-cs-list'>{ ''.join(f'<li>{esc(s)}</li>' for s in all_skills) }</ul>")
    if resume.languages:
        parts.append(f"<h3 class='cv-cs-h'>{esc('LANGUAGES' if not is_ar else 'اللغات')}</h3><ul class='cv-cs-list'>{ ''.join(f'<li>{esc(l.name)}</li>' for l in resume.languages) }</ul>")
    parts.append("</aside>")
    parts.append("<main class='cv-cs-main'>")
    summary = resume.summary_text(lang)
    if summary:
        parts.append(f"<section class='cv-section'><h2 class='cv-h2'>{esc('Profile' if not is_ar else 'ملخص')}</h2><p>{esc(summary)}</p></section>")
    if resume.experience:
        parts.append(f"<section class='cv-section'><h2 class='cv-h2'>{esc('Experience' if not is_ar else 'الخبرات')}</h2>")
        for e in resume.experience:
            parts.append("<div class='cv-item break-inside-avoid'>")
            parts.append(f"<div class='cv-item-title'>{esc(title_for(e, lang))}</div>")
            parts.append(f"<div class='cv-item-sub'>{esc(company_for(e, lang))}{(' · '+date_range(e)) if date_range(e) else ''}</div>")
            parts.append(render_bullets(bullets_for(e, lang)))
            parts.append("</div>")
        parts.append("</section>")
    if resume.education:
        parts.append(f"<section class='cv-section'><h2 class='cv-h2'>{esc('Education' if not is_ar else 'التعليم')}</h2>")
        for ed in resume.education:
            parts.append("<div class='cv-item break-inside-avoid'>")
            parts.append(f"<div class='cv-item-title'>{esc(degree_for(ed, lang))}</div>")
            parts.append(f"<div class='cv-item-sub'>{esc(institution_for(ed, lang))}{(' · '+ed.year) if ed.year else ''}</div>")
            parts.append("</div>")
        parts.append("</section>")
    parts.append("</main></div></div>")
    return "".join(parts)


# ===========================================================================
# 5. Botanical Beige
# ===========================================================================

def render_botanical_beige(resume: ResumeData) -> str:
    lang = resume.lang or "en"
    name = name_for(resume, lang)
    title = title_pos_for(resume, lang)
    is_ar = lang == "ar"
    initials = "".join([w[0] for w in (name.split()[:2]) if w])[:2].upper() or "CV"
    parts = [f"<div class='cv-root cv-botanical-beige' data-lang='{lang}'>"]
    parts.append("<header class='cv-bb-header'>")
    parts.append(f"<div class='cv-bb-circle'>{esc(initials)}</div>")
    parts.append("<div class='cv-bb-headtext'>")
    parts.append(f"<h1 class='cv-name'>{esc(name)}</h1>")
    if title:
        parts.append(f"<div class='cv-title'>{esc(title)}</div>")
    contact = contact_line(resume, lang)
    if contact:
        parts.append(f"<div class='cv-contact'>{esc(contact)}</div>")
    parts.append("</div></header>")
    summary = resume.summary_text(lang)
    if summary:
        parts.append(f"<section class='cv-section'><h2 class='cv-bb-h2'>{esc('Profile' if not is_ar else 'نبذة')}</h2><p>{esc(summary)}</p></section>")
    if resume.experience:
        parts.append(f"<section class='cv-section'><h2 class='cv-bb-h2'>{esc('Experience' if not is_ar else 'الخبرات')}</h2>")
        for e in resume.experience:
            parts.append("<div class='cv-item break-inside-avoid'>")
            parts.append(f"<div class='cv-item-title'>{esc(title_for(e, lang))}</div>")
            parts.append(f"<div class='cv-item-sub'>{esc(company_for(e, lang))}{(' · '+date_range(e)) if date_range(e) else ''}</div>")
            parts.append(render_bullets(bullets_for(e, lang)))
            parts.append("</div>")
        parts.append("</section>")
    if resume.education:
        parts.append(f"<section class='cv-section'><h2 class='cv-bb-h2'>{esc('Education' if not is_ar else 'التعليم')}</h2>")
        for ed in resume.education:
            parts.append("<div class='cv-item break-inside-avoid'>")
            parts.append(f"<div class='cv-item-title'>{esc(degree_for(ed, lang))}</div>")
            parts.append(f"<div class='cv-item-sub'>{esc(institution_for(ed, lang))}{(' · '+ed.year) if ed.year else ''}</div>")
            parts.append("</div>")
        parts.append("</section>")
    all_skills = resume.skills + resume.technical_skills + resume.soft_skills
    if all_skills:
        parts.append(skills_block(all_skills, "Skills", "المهارات", lang))
    if resume.languages:
        parts.append(skills_block([f"{l.name} ({l.level})" if l.level else l.name for l in resume.languages], "Languages", "اللغات", lang))
    parts.append("</div>")
    return "".join(parts)


# ===========================================================================
# 6. Lavender Minimal
# ===========================================================================

def render_lavender_minimal(resume: ResumeData) -> str:
    lang = resume.lang or "en"
    name = name_for(resume, lang)
    title = title_pos_for(resume, lang)
    is_ar = lang == "ar"
    parts = [f"<div class='cv-root cv-lavender-minimal' data-lang='{lang}'>"]
    parts.append(f"<header class='cv-lv-header'><h1 class='cv-name'>{esc(name)}</h1>{('<div class=cv-title>'+esc(title)+'</div>') if title else ''}")
    contact = contact_line(resume, lang)
    if contact:
        parts.append(f"<div class='cv-contact'>{esc(contact)}</div>")
    parts.append("</header>")
    summary = resume.summary_text(lang)
    if summary:
        parts.append(f"<section class='cv-section'><h2 class='cv-lv-h2'>{esc('Profile' if not is_ar else 'نبذة')}</h2><p>{esc(summary)}</p></section>")
    if resume.experience:
        parts.append(f"<section class='cv-section'><h2 class='cv-lv-h2'>{esc('Experience' if not is_ar else 'الخبرات')}</h2>")
        for e in resume.experience:
            parts.append("<div class='cv-item break-inside-avoid'>")
            parts.append(f"<div class='cv-item-title'>{esc(title_for(e, lang))}</div>")
            parts.append(f"<div class='cv-item-sub'>{esc(company_for(e, lang))}{(' · '+date_range(e)) if date_range(e) else ''}</div>")
            parts.append(render_bullets(bullets_for(e, lang)))
            parts.append("</div>")
        parts.append("</section>")
    if resume.education:
        parts.append(f"<section class='cv-section'><h2 class='cv-lv-h2'>{esc('Education' if not is_ar else 'التعليم')}</h2>")
        for ed in resume.education:
            parts.append("<div class='cv-item break-inside-avoid'>")
            parts.append(f"<div class='cv-item-title'>{esc(degree_for(ed, lang))}</div>")
            parts.append(f"<div class='cv-item-sub'>{esc(institution_for(ed, lang))}{(' · '+ed.year) if ed.year else ''}</div>")
            parts.append("</div>")
        parts.append("</section>")
    all_skills = resume.skills + resume.technical_skills + resume.soft_skills
    if all_skills:
        parts.append(skills_block(all_skills, "Skills", "المهارات", lang))
    if resume.languages:
        parts.append(skills_block([l.name for l in resume.languages], "Languages", "اللغات", lang))
    parts.append("</div>")
    return "".join(parts)


# ===========================================================================
# Helpers for bilingual 50/50 templates
# ===========================================================================

def _bilingual_column(resume: ResumeData, lang: str, css_class: str) -> str:
    is_ar = lang == "ar"
    name = name_for(resume, lang)
    title = title_pos_for(resume, lang)
    direction = "rtl" if is_ar else "ltr"
    parts = [f"<div class='{css_class}' dir='{direction}'>"]
    parts.append(f"<h1 class='cv-name'>{esc(name)}</h1>")
    if title:
        parts.append(f"<div class='cv-title'>{esc(title)}</div>")
    # Contact values: in Arabic column, wrap emails/phones/URLs with dir=ltr
    contact_parts = []
    for v in (resume.personal.email, resume.personal.phone, resume.personal.location):
        if v:
            contact_parts.append(smart_val(v, lang))
    if contact_parts:
        parts.append(f"<div class='cv-contact'>{' · '.join(contact_parts)}</div>")
    summary = resume.summary_text(lang)
    if summary:
        parts.append(f"<section class='cv-section'><h2 class='cv-h2'>{esc('ملخص' if is_ar else 'Summary')}</h2><p>{esc(summary)}</p></section>")
    if resume.experience:
        parts.append(f"<section class='cv-section'><h2 class='cv-h2'>{esc('الخبرات' if is_ar else 'Experience')}</h2>")
        for e in resume.experience:
            parts.append("<div class='cv-item break-inside-avoid'>")
            parts.append(f"<div class='cv-item-title'>{esc(title_for(e, lang))}</div>")
            # date_range is contact-like (numbers) → protect in Arabic
            dr = date_range(e)
            sub = esc(company_for(e, lang)) + (smart_val(' · ' + dr, lang) if dr else '')
            parts.append(f"<div class='cv-item-sub'>{sub}</div>")
            parts.append(render_bullets(bullets_for(e, lang)))
            parts.append("</div>")
        parts.append("</section>")
    if resume.education:
        parts.append(f"<section class='cv-section'><h2 class='cv-h2'>{esc('التعليم' if is_ar else 'Education')}</h2>")
        for ed in resume.education:
            parts.append("<div class='cv-item break-inside-avoid'>")
            parts.append(f"<div class='cv-item-title'>{esc(degree_for(ed, lang))}</div>")
            yr = ed.year
            sub = esc(institution_for(ed, lang)) + (smart_val(' · ' + yr, lang) if yr else '')
            parts.append(f"<div class='cv-item-sub'>{sub}</div>")
            parts.append("</div>")
        parts.append("</section>")
    all_skills = resume.skills + resume.technical_skills + resume.soft_skills
    if all_skills:
        parts.append(skills_block(all_skills, "Skills", "المهارات", lang))
    if resume.languages:
        parts.append(skills_block([l.name for l in resume.languages], "Languages", "اللغات", lang))
    parts.append("</div>")
    return "".join(parts)


# ===========================================================================
# 7. Bilingual Teal-Gold
# ===========================================================================

def render_bilingual_teal_gold(resume: ResumeData) -> str:
    parts = [f"<div class='cv-root cv-bilingual-teal-gold' data-lang='bilingual'>"]
    parts.append("<div class='cv-btg-grid'>")
    parts.append(_bilingual_column(resume, "en", "cv-btg-en"))
    parts.append(_bilingual_column(resume, "ar", "cv-btg-ar"))
    parts.append("</div></div>")
    return "".join(parts)


# ===========================================================================
# 8. Bilingual Navy
# ===========================================================================

def render_bilingual_navy(resume: ResumeData) -> str:
    parts = [f"<div class='cv-root cv-bilingual-navy' data-lang='bilingual'>"]
    parts.append("<div class='cv-bn-grid'>")
    parts.append(_bilingual_column(resume, "ar", "cv-bn-ar"))
    parts.append(_bilingual_column(resume, "en", "cv-bn-en"))
    parts.append("</div></div>")
    return "".join(parts)


# ===========================================================================
# 9. Bilingual Peach
# ===========================================================================

def render_bilingual_peach(resume: ResumeData) -> str:
    parts = [f"<div class='cv-root cv-bilingual-peach' data-lang='bilingual'>"]
    parts.append("<div class='cv-bp-grid'>")
    parts.append(_bilingual_column(resume, "en", "cv-bp-en"))
    parts.append(_bilingual_column(resume, "ar", "cv-bp-ar"))
    parts.append("</div></div>")
    return "".join(parts)


# ===========================================================================
# 10. International Bilingual (single column, stacked EN/AR)
# ===========================================================================

def render_international_bilingual(resume: ResumeData) -> str:
    name_en = resume.personal.name_en or resume.personal.name
    name_ar = resume.personal.name_ar or resume.personal.name
    title_en = resume.personal.title_en or resume.personal.title
    title_ar = resume.personal.title_ar or resume.personal.title
    parts = [f"<div class='cv-root cv-international-bilingual' data-lang='bilingual'>"]
    parts.append("<header class='cv-ib-header'>")
    if name_en:
        parts.append(f"<h1 class='cv-ib-name-en'>{esc(name_en)}</h1>")
    if name_ar:
        parts.append(f"<h1 class='cv-ib-name-ar' dir='rtl'>{esc(name_ar)}</h1>")
    if title_en or title_ar:
        parts.append("<div class='cv-ib-titles'>")
        if title_en:
            parts.append(f"<span class='cv-ib-t-en'>{esc(title_en)}</span>")
        if title_ar:
            parts.append(f"<span class='cv-ib-t-ar' dir='rtl'>{esc(title_ar)}</span>")
        parts.append("</div>")
    contact = contact_line(resume, "en")
    if contact:
        parts.append(f"<div class='cv-contact'>{esc(contact)}</div>")
    parts.append("</header>")

    def stacked_section(label_en, label_ar, content_en, content_ar):
        out = []
        if content_en or content_ar:
            out.append("<section class='cv-ib-section break-inside-avoid'>")
            out.append(f"<div class='cv-ib-label'><span dir='ltr'>{esc(label_en)}</span><span dir='rtl'>{esc(label_ar)}</span></div>")
            out.append("<div class='cv-ib-cols'>")
            out.append(f"<div class='cv-ib-en' dir='ltr'>{content_en}</div>")
            out.append(f"<div class='cv-ib-ar' dir='rtl'>{content_ar}</div>")
            out.append("</div></section>")
        return "".join(out)

    s_en = resume.summary_text("en"); s_ar = resume.summary_text("ar")
    if s_en or s_ar:
        parts.append(stacked_section("Summary", "ملخص", f"<p>{esc(s_en)}</p>", f"<p>{esc(s_ar)}</p>"))

    if resume.experience:
        exp_en = "".join(
            f"<div class='cv-item'><div class='cv-item-title'>{esc(title_for(e,'en'))}</div>"
            f"<div class='cv-item-sub'>{esc(company_for(e,'en'))}{(' · '+date_range(e)) if date_range(e) else ''}</div>"
            f"{render_bullets(bullets_for(e,'en'))}</div>" for e in resume.experience
        )
        exp_ar = "".join(
            f"<div class='cv-item'><div class='cv-item-title'>{esc(title_for(e,'ar'))}</div>"
            f"<div class='cv-item-sub'>{esc(company_for(e,'ar'))}{(' · '+date_range(e)) if date_range(e) else ''}</div>"
            f"{render_bullets(bullets_for(e,'ar'))}</div>" for e in resume.experience
        )
        parts.append(stacked_section("Experience", "الخبرات", exp_en, exp_ar))

    if resume.education:
        edu_en = "".join(f"<div class='cv-item'><div class='cv-item-title'>{esc(degree_for(ed,'en'))}</div><div class='cv-item-sub'>{esc(institution_for(ed,'en'))}</div></div>" for ed in resume.education)
        edu_ar = "".join(f"<div class='cv-item'><div class='cv-item-title'>{esc(degree_for(ed,'ar'))}</div><div class='cv-item-sub'>{esc(institution_for(ed,'ar'))}</div></div>" for ed in resume.education)
        parts.append(stacked_section("Education", "التعليم", edu_en, edu_ar))

    all_skills = resume.skills + resume.technical_skills + resume.soft_skills
    if all_skills:
        sk = "".join(f"<span class='cv-skill-chip'>{esc(s)}</span>" for s in all_skills)
        parts.append(stacked_section("Skills", "المهارات", f"<div class='cv-skills'>{sk}</div>", f"<div class='cv-skills'>{sk}</div>"))

    if resume.languages:
        langs = "".join(f"<span class='cv-skill-chip'>{esc(l.name)}</span>" for l in resume.languages)
        parts.append(stacked_section("Languages", "اللغات", f"<div class='cv-skills'>{langs}</div>", f"<div class='cv-skills'>{langs}</div>"))

    parts.append("</div>")
    return "".join(parts)


# ===========================================================================
# 11. Bilingual ATS Classic — يطابق السير الذاتية الأصلية المرفقة
# عمود واحد، أسود/أبيض، عناوين ثنائية اللغة، نص ثنائي
# ===========================================================================

def _bilingual_heading(en: str, ar: str) -> str:
    """عنوان ثنائي اللغة: إنجليزي يسار + عربي يمين، مع خط فاصل أسفله."""
    return (
        f"<div class='cv-bac-heading'>"
        f"<span class='cv-bac-h-en' dir='ltr'>{esc(en)}</span>"
        f"<span class='cv-bac-h-ar' dir='rtl'>{esc(ar)}</span>"
        f"</div>"
    )


def _bilingual_paragraph(en: str, ar: str) -> str:
    """فقرة ثنائية اللغة: إنجليزي فوق + عربي تحت."""
    out = ""
    if en:
        out += f"<p class='cv-bac-p-en' dir='ltr'>{esc(en)}</p>"
    if ar:
        out += f"<p class='cv-bac-p-ar' dir='rtl'>{esc(ar)}</p>"
    return out


def render_bilingual_ats_classic(resume: ResumeData) -> str:
    """قالب يطابق السير الذاتية الأصلية — بسيط، أسود/أبيض، ثنائي اللغة."""
    parts = ["<div class='cv-root cv-bilingual-ats-classic' data-lang='bilingual'>"]

    # --- الهيدر: اسم إنجليزي يسار + اسم عربي يمين ---
    name_en = resume.personal.name_en or resume.personal.name or ""
    name_ar = resume.personal.name_ar or resume.personal.name or ""
    parts.append("<div class='cv-bac-header'>")
    if name_en:
        parts.append(f"<div class='cv-bac-name-en' dir='ltr'>{esc(name_en)}</div>")
    if name_ar:
        parts.append(f"<div class='cv-bac-name-ar' dir='rtl'>{esc(name_ar)}</div>")
    parts.append("</div>")

    # --- شريط معلومات الاتصال (خلفية رمادية فاتحة) ---
    contact_parts = []
    if resume.personal.email:
        contact_parts.append(f"<span dir='ltr'>{esc(resume.personal.email)}</span>")
    if resume.personal.phone:
        contact_parts.append(f"<span dir='ltr'>{esc(resume.personal.phone)}</span>")
    if resume.personal.location:
        contact_parts.append(esc(resume.personal.location))
    if resume.personal.linkedin:
        contact_parts.append(f"<span dir='ltr'>{esc(resume.personal.linkedin)}</span>")
    if contact_parts:
        parts.append(f"<div class='cv-bac-contact-bar'>{' · '.join(contact_parts)}</div>")

    # --- الهدف الوظيفي / الملخص ---
    sum_en = resume.summary_text("en")
    sum_ar = resume.summary_text("ar")
    if sum_en or sum_ar:
        parts.append("<div class='cv-bac-section'>")
        parts.append(_bilingual_heading("CAREER OBJECTIVE", "الهدف الوظيفي"))
        parts.append(_bilingual_paragraph(sum_en, sum_ar))
        parts.append("</div>")

    # --- التعليم ---
    if resume.education:
        parts.append("<div class='cv-bac-section'>")
        parts.append(_bilingual_heading("EDUCATION", "التعليم"))
        for ed in resume.education:
            parts.append("<div class='cv-bac-item'>")
            deg_en = degree_for(ed, "en")
            deg_ar = degree_for(ed, "ar")
            inst_en = institution_for(ed, "en")
            inst_ar = institution_for(ed, "ar")
            # English line
            if deg_en or inst_en:
                line_en = deg_en
                if inst_en:
                    line_en = (line_en + " — " + inst_en) if line_en else inst_en
                if ed.year:
                    line_en += f" ({ed.year})"
                parts.append(f"<div class='cv-bac-item-en' dir='ltr'>{esc(line_en)}</div>")
            # Arabic line
            if deg_ar or inst_ar:
                line_ar = deg_ar
                if inst_ar:
                    line_ar = (line_ar + " — " + inst_ar) if line_ar else inst_ar
                parts.append(f"<div class='cv-bac-item-ar' dir='rtl'>{esc(line_ar)}</div>")
            parts.append("</div>")
        parts.append("</div>")

    # --- الخبرات ---
    if resume.experience:
        parts.append("<div class='cv-bac-section'>")
        parts.append(_bilingual_heading("EXPERIENCE", "الخبرات المهنية"))
        for e in resume.experience:
            parts.append("<div class='cv-bac-item'>")
            # English: title — company (dates)
            t_en = title_for(e, "en")
            c_en = company_for(e, "en")
            dr = date_range(e)
            if t_en or c_en:
                line = t_en
                if c_en:
                    line = (line + " — " + c_en) if line else c_en
                if dr:
                    line += f" ({dr})"
                parts.append(f"<div class='cv-bac-item-en' dir='ltr'>{esc(line)}</div>")
            # Arabic: title — company
            t_ar = title_for(e, "ar")
            c_ar = company_for(e, "ar")
            if t_ar or c_ar:
                line_ar = t_ar
                if c_ar:
                    line_ar = (line_ar + " — " + c_ar) if line_ar else c_ar
                parts.append(f"<div class='cv-bac-item-ar' dir='rtl'>{esc(line_ar)}</div>")
            # Bullets (English then Arabic)
            b_en = bullets_for(e, "en")
            b_ar = bullets_for(e, "ar")
            if b_en:
                items = "".join(f"<li dir='ltr'>{esc(b)}</li>" for b in b_en if b)
                parts.append(f"<ul class='cv-bac-bullets'>{items}</ul>")
            if b_ar:
                items = "".join(f"<li dir='rtl'>{esc(b)}</li>" for b in b_ar if b)
                parts.append(f"<ul class='cv-bac-bullets'>{items}</ul>")
            parts.append("</div>")
        parts.append("</div>")

    # --- الدورات ---
    if resume.courses:
        parts.append("<div class='cv-bac-section'>")
        parts.append(_bilingual_heading("COURSES", "الدورات"))
        for c in resume.courses:
            parts.append(f"<div class='cv-bac-list-item'>• {esc(c)}</div>")
        parts.append("</div>")

    # --- المهارات ---
    all_skills = resume.skills + resume.technical_skills + resume.soft_skills
    if all_skills:
        parts.append("<div class='cv-bac-section'>")
        parts.append(_bilingual_heading("SKILLS", "المهارات"))
        # عرض في عمودين
        items = "".join(f"<div class='cv-bac-skill'>{esc(s)}</div>" for s in all_skills)
        parts.append(f"<div class='cv-bac-skills-grid'>{items}</div>")
        parts.append("</div>")

    # --- المهارات التقنية ---
    if resume.technical_skills and resume.technical_skills != resume.skills:
        parts.append("<div class='cv-bac-section'>")
        parts.append(_bilingual_heading("TECHNICAL SKILLS", "المهارات التقنية"))
        items = "".join(f"<div class='cv-bac-skill'>{esc(s)}</div>" for s in resume.technical_skills)
        parts.append(f"<div class='cv-bac-skills-grid'>{items}</div>")
        parts.append("</div>")

    # --- اللغات ---
    if resume.languages:
        parts.append("<div class='cv-bac-section'>")
        parts.append(_bilingual_heading("LANGUAGES", "اللغات"))
        for l in resume.languages:
            label = l.name
            if l.level:
                label += f" ({l.level})"
            parts.append(f"<div class='cv-bac-list-item'>• {esc(label)}</div>")
        parts.append("</div>")

    parts.append("</div>")
    return "".join(parts)
