"""Resume normalizer — the SINGLE normalization pipeline.

Raw dict (from AI or rule-based parser)
  → Pydantic validation
  → deterministic contact validation
  → deduplication
  → clean ResumeData

No other module performs normalization.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from app.models.resume import (
    AchievementItem,
    CertificationItem,
    CourseItem,
    EducationItem,
    ExperienceItem,
    LanguageItem,
    OtherItem,
    PersonalInfo,
    ProjectItem,
    ReferenceItem,
    ResumeData,
)
from app.utils.validation import (
    dedup_strings,
    detect_section,
    extract_email,
    extract_github,
    extract_linkedin,
    extract_phone,
    extract_website,
    is_contact_token,
)

logger = logging.getLogger("cvgen.normalizer")


def _ensure_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [value]
    return [value]


def _coerce_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _as_dict(value: Any) -> dict:
    """Coerce any value to a dict. Strings/None/etc become {}."""
    if isinstance(value, dict):
        return value
    return {}


def _as_list(value: Any) -> list:
    """Coerce any value to a list."""
    if isinstance(value, list):
        return value
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, dict):
        return [value]
    return []


def _normalize_personal(raw: Any, full_text: str = "") -> PersonalInfo:
    raw = _as_dict(raw)
    email = _coerce_str(raw.get("email")) or extract_email(full_text)
    phone = _coerce_str(raw.get("phone")) or extract_phone(full_text)
    linkedin = _coerce_str(raw.get("linkedin")) or extract_linkedin(full_text)
    github = _coerce_str(raw.get("github")) or extract_github(full_text)
    website = _coerce_str(raw.get("website")) or extract_website(full_text)

    name = _coerce_str(raw.get("name"))
    name_en = _coerce_str(raw.get("name_en"))
    name_ar = _coerce_str(raw.get("name_ar"))
    if not name and (name_en or name_ar):
        name = name_en or name_ar

    title = _coerce_str(raw.get("title"))
    title_en = _coerce_str(raw.get("title_en"))
    title_ar = _coerce_str(raw.get("title_ar"))

    return PersonalInfo(
        name=name,
        name_en=name_en,
        name_ar=name_ar,
        title=title,
        title_en=title_en,
        title_ar=title_ar,
        email=email,
        phone=phone,
        location=_coerce_str(raw.get("location")),
        linkedin=linkedin,
        website=website,
        github=github,
    )


def _normalize_experience(raw_list: list) -> list[ExperienceItem]:
    out: list[ExperienceItem] = []
    for raw in _ensure_list(raw_list):
        if not isinstance(raw, dict):
            continue
        # Skip items that are clearly not experiences (e.g. stray contact lines)
        title = _coerce_str(raw.get("title") or raw.get("title_en") or raw.get("title_ar"))
        company = _coerce_str(raw.get("company") or raw.get("company_en") or raw.get("company_ar"))
        bullets = [b for b in _ensure_list(raw.get("bullets")) if _coerce_str(b)]
        bullets_en = [b for b in _ensure_list(raw.get("bullets_en")) if _coerce_str(b)]
        bullets_ar = [b for b in _ensure_list(raw.get("bullets_ar")) if _coerce_str(b)]
        description = _coerce_str(raw.get("description"))
        # If all empty, skip
        if not any([title, company, description, bullets, bullets_en, bullets_ar]):
            continue
        # If it's actually a contact token, skip
        joined = " ".join([title, company, description])
        if is_contact_token(joined) and not any([bullets, bullets_en, bullets_ar]):
            continue
        out.append(ExperienceItem(
            title=title,
            title_en=_coerce_str(raw.get("title_en")),
            title_ar=_coerce_str(raw.get("title_ar")),
            company=company,
            company_en=_coerce_str(raw.get("company_en")),
            company_ar=_coerce_str(raw.get("company_ar")),
            location=_coerce_str(raw.get("location")),
            start_date=_coerce_str(raw.get("start_date")),
            end_date=_coerce_str(raw.get("end_date")),
            current=bool(raw.get("current", False)),
            description=description,
            bullets=bullets,
            bullets_en=bullets_en,
            bullets_ar=bullets_ar,
        ))
    return out


def _normalize_education(raw_list: list) -> list[EducationItem]:
    out: list[EducationItem] = []
    for raw in _ensure_list(raw_list):
        if not isinstance(raw, dict):
            continue
        degree = _coerce_str(raw.get("degree") or raw.get("degree_en") or raw.get("degree_ar"))
        institution = _coerce_str(raw.get("institution") or raw.get("institution_en") or raw.get("institution_ar"))
        if not any([degree, institution, _coerce_str(raw.get("year"))]):
            continue
        out.append(EducationItem(
            degree=degree,
            degree_en=_coerce_str(raw.get("degree_en")),
            degree_ar=_coerce_str(raw.get("degree_ar")),
            institution=institution,
            institution_en=_coerce_str(raw.get("institution_en")),
            institution_ar=_coerce_str(raw.get("institution_ar")),
            location=_coerce_str(raw.get("location")),
            start_date=_coerce_str(raw.get("start_date")),
            end_date=_coerce_str(raw.get("end_date")),
            year=_coerce_str(raw.get("year")),
            gpa=_coerce_str(raw.get("gpa")),
            description=_coerce_str(raw.get("description")),
        ))
    return out


def _normalize_skills(raw: Any) -> list[str]:
    items = _ensure_list(raw)
    out = []
    for it in items:
        if isinstance(it, str):
            out.append(it.strip())
        elif isinstance(it, dict):
            n = _coerce_str(it.get("name"))
            if n:
                out.append(n)
    return dedup_strings(out)


def _normalize_certifications(raw_list: list) -> list[CertificationItem]:
    out = []
    for raw in _ensure_list(raw_list):
        if isinstance(raw, str):
            if raw.strip():
                out.append(CertificationItem(name=raw.strip()))
            continue
        if not isinstance(raw, dict):
            continue
        name = _coerce_str(raw.get("name"))
        if not name:
            continue
        out.append(CertificationItem(
            name=name,
            issuer=_coerce_str(raw.get("issuer")),
            date=_coerce_str(raw.get("date")),
            url=_coerce_str(raw.get("url")),
        ))
    return out


def _normalize_languages(raw_list: list) -> list[LanguageItem]:
    out = []
    for raw in _ensure_list(raw_list):
        if isinstance(raw, str):
            if raw.strip():
                out.append(LanguageItem(name=raw.strip()))
            continue
        if not isinstance(raw, dict):
            continue
        name = _coerce_str(raw.get("name"))
        if not name:
            continue
        out.append(LanguageItem(name=name, level=_coerce_str(raw.get("level"))))
    return out


def _normalize_projects(raw_list: list) -> list[ProjectItem]:
    out = []
    for raw in _ensure_list(raw_list):
        if not isinstance(raw, dict):
            continue
        name = _coerce_str(raw.get("name"))
        if not name:
            continue
        out.append(ProjectItem(
            name=name,
            description=_coerce_str(raw.get("description")),
            url=_coerce_str(raw.get("url")),
            technologies=[_coerce_str(t) for t in _ensure_list(raw.get("technologies"))],
        ))
    return out


def _normalize_achievements(raw_list: list) -> list[AchievementItem]:
    out = []
    for raw in _ensure_list(raw_list):
        if isinstance(raw, str):
            if raw.strip():
                out.append(AchievementItem(title=raw.strip()))
            continue
        if not isinstance(raw, dict):
            continue
        title = _coerce_str(raw.get("title"))
        if not title:
            continue
        out.append(AchievementItem(
            title=title,
            description=_coerce_str(raw.get("description")),
            date=_coerce_str(raw.get("date")),
        ))
    return out


def _normalize_references(raw_list: list) -> list[ReferenceItem]:
    out = []
    for raw in _ensure_list(raw_list):
        if not isinstance(raw, dict):
            continue
        name = _coerce_str(raw.get("name"))
        if not name:
            continue
        out.append(ReferenceItem(
            name=name,
            position=_coerce_str(raw.get("position")),
            contact=_coerce_str(raw.get("contact")),
        ))
    return out


def _normalize_other(raw_list: list) -> list[OtherItem]:
    out = []
    for raw in _ensure_list(raw_list):
        if isinstance(raw, str):
            if raw.strip():
                out.append(OtherItem(label="Other", value=raw.strip()))
            continue
        if isinstance(raw, dict):
            label = _coerce_str(raw.get("label")) or "Other"
            value = _coerce_str(raw.get("value"))
            if value:
                out.append(OtherItem(label=label, value=value))
    return out


def _strip_contact_from_lists(resume: ResumeData) -> ResumeData:
    """Ensure emails/phones/URLs never appear in skill-like lists."""
    def clean(items: list[str]) -> list[str]:
        return [s for s in items if not is_contact_token(s)]

    resume.skills = clean(resume.skills)
    resume.technical_skills = clean(resume.technical_skills)
    resume.soft_skills = clean(resume.soft_skills)
    resume.courses = clean(resume.courses)
    resume.volunteering = clean(resume.volunteering)
    return resume


def _dedup_all(resume: ResumeData) -> ResumeData:
    resume.skills = dedup_strings(resume.skills)
    resume.technical_skills = dedup_strings(resume.technical_skills)
    resume.soft_skills = dedup_strings(resume.soft_skills)
    resume.courses = dedup_strings(resume.courses)
    resume.volunteering = dedup_strings(resume.volunteering)
    return resume


def normalize_resume_data(raw: dict, full_text: str = "") -> ResumeData:
    """The single normalization entry point.

    Accepts a raw dict (from AI parser or rule-based parser) and returns a
    validated, deduplicated, contact-cleaned ResumeData.
    """
    if not isinstance(raw, dict):
        raw = {}

    full_text = full_text or ""
    personal = _normalize_personal(raw.get("personal", {}), full_text)

    summary = raw.get("summary") or {}
    if isinstance(summary, str):
        summary = {"en": summary.strip()} if summary.strip() else {}
    elif not isinstance(summary, dict):
        summary = {}

    objective = raw.get("objective") or {}
    if isinstance(objective, str):
        objective = {"en": objective.strip()} if objective.strip() else {}
    elif not isinstance(objective, dict):
        objective = {}

    resume = ResumeData(
        personal=personal,
        summary=summary,
        objective=objective,
        experience=_normalize_experience(raw.get("experience")),
        education=_normalize_education(raw.get("education")),
        skills=_normalize_skills(raw.get("skills_en") or raw.get("skills")),
        skills_en=_normalize_skills(raw.get("skills_en") or raw.get("skills")),
        skills_ar=_normalize_skills(raw.get("skills_ar")),
        technical_skills=_normalize_skills(raw.get("technical_skills_en") or raw.get("technical_skills")),
        technical_skills_en=_normalize_skills(raw.get("technical_skills_en") or raw.get("technical_skills")),
        technical_skills_ar=_normalize_skills(raw.get("technical_skills_ar")),
        soft_skills=_normalize_skills(raw.get("soft_skills") or raw.get("skills_ar")),
        courses=_normalize_skills(raw.get("courses")),
        certifications=_normalize_certifications(raw.get("certifications")),
        languages=_normalize_languages(raw.get("languages")),
        projects=_normalize_projects(raw.get("projects")),
        volunteering=_normalize_skills(raw.get("volunteering")),
        achievements=_normalize_achievements(raw.get("achievements")),
        references=_normalize_references(raw.get("references")),
        other=_normalize_other(raw.get("other")),
        template_id=_coerce_str(raw.get("template_id")) or "official_bilingual_master",
        lang=_coerce_str(raw.get("lang")) or "en",
    )

    resume = _strip_contact_from_lists(resume)
    resume = _dedup_all(resume)
    resume = _sanitize_resume(resume)
    # NOTE: Bilingual translation sync (translating missing Arabic from English
    # via the cloud AI) is performed in app.services.resume_parser.parse_resume_ai
    # AFTER normalization. We do NOT copy English into Arabic here — that would
    # violate the strict 1:1 real-translation rule. If Arabic is missing, it
    # stays empty until the bilingual_sync service fills it with a real translation.
    return resume


def _sanitize_resume(resume: ResumeData) -> ResumeData:
    """Clean and sanitize the resume data before sending to frontend.

    - Remove extra spaces/newlines from names
    - Ensure no null values in arrays
    - Normalize dates to YYYY/MM format
    - Ensure balanced bullets_en/bullets_ar count
    """
    import re

    # Clean names
    if resume.personal.name:
        resume.personal.name = re.sub(r'\s+', ' ', resume.personal.name).strip()
    if resume.personal.name_en:
        resume.personal.name_en = re.sub(r'\s+', ' ', resume.personal.name_en).strip()
    if resume.personal.name_ar:
        resume.personal.name_ar = re.sub(r'\s+', ' ', resume.personal.name_ar).strip()

    # Clean title
    if resume.personal.title:
        resume.personal.title = re.sub(r'\s+', ' ', resume.personal.title).strip()
    if resume.personal.title_en:
        resume.personal.title_en = re.sub(r'\s+', ' ', resume.personal.title_en).strip()
    if resume.personal.title_ar:
        resume.personal.title_ar = re.sub(r'\s+', ' ', resume.personal.title_ar).strip()

    # Normalize dates in experience
    for exp in resume.experience:
        exp.start_date = _normalize_date(exp.start_date)
        exp.end_date = _normalize_date(exp.end_date)

    # Normalize dates in education
    for edu in resume.education:
        edu.start_date = _normalize_date(edu.start_date)
        edu.end_date = _normalize_date(edu.end_date)
        if edu.year:
            edu.year = _normalize_date(edu.year)

    # NOTE: We do NOT copy bullets_en into bullets_ar (or vice versa) here.
    # That would violate the strict 1:1 real-translation rule. Missing Arabic
    # bullets are translated by the bilingual_sync service (cloud AI) in
    # parse_resume_ai(). Empty arrays stay empty until real translations arrive.

    # Ensure skills are clean (no nulls, no empty strings)
    resume.skills = [s for s in resume.skills if s and s.strip()]
    resume.technical_skills = [s for s in resume.technical_skills if s and s.strip()]
    resume.soft_skills = [s for s in resume.soft_skills if s and s.strip()]
    resume.courses = [s for s in resume.courses if s and s.strip()]

    # If soft_skills is empty but skills has Arabic items, move them
    from app.utils.arabic import contains_arabic
    if not resume.soft_skills:
        ar_skills = [s for s in resume.skills if contains_arabic(s)]
        en_skills = [s for s in resume.skills if not contains_arabic(s)]
        if ar_skills:
            resume.soft_skills = ar_skills
            resume.skills = en_skills

    # Populate the explicit bilingual arrays from whatever the AI provided.
    # We DO NOT copy English into Arabic (or vice versa) — that is the job of
    # the bilingual_sync service, which calls the cloud AI for a REAL translation.
    # Here we only split the generic `skills`/`technical_skills` arrays by
    # language so the explicit _en/_ar fields reflect what was actually returned.
    if not resume.skills_en:
        resume.skills_en = [s for s in resume.skills if not contains_arabic(s)]
    if not resume.skills_ar:
        resume.skills_ar = [s for s in resume.skills if contains_arabic(s)]
    if not resume.technical_skills_en:
        resume.technical_skills_en = [s for s in resume.technical_skills if not contains_arabic(s)]
    if not resume.technical_skills_ar:
        resume.technical_skills_ar = [s for s in resume.technical_skills if contains_arabic(s)]

    return resume


def _enforce_bilingual_skill_match(resume: ResumeData) -> ResumeData:
    """DEPRECATED — kept only for backward compatibility.

    This function previously COPIED English into Arabic when Arabic was empty.
    That behavior violates the strict 1:1 real-translation rule and has been
    removed. Bilingual translation is now handled by app.ai.bilingual_sync.sync_bilingual(),
    which calls the cloud AI to produce REAL Arabic translations.

    This function is now a no-op. It does NOT copy anything.
    """
    return resume


def _normalize_date(date_str: str) -> str:
    """Normalize date to YYYY/MM format.

    Handles:
    - 'March 2024' → '2024/03'
    - '2024' → '2024'
    - 'Present' / 'Current' / 'حتى الآن' → 'Present'
    - 'Jan 2020' → '2020/01'
    """
    if not date_str or not date_str.strip():
        return ""
    s = date_str.strip()

    # Check for "present" variations
    if s.lower() in ("present", "current", "now", "حتى الآن", "الآن"):
        return "Present"

    # Already in YYYY/MM format
    if re.match(r'^\d{4}/\d{1,2}$', s):
        return s

    # Just a year
    if re.match(r'^\d{4}$', s):
        return s

    # Try to parse month name + year
    month_map = {
        'january': '01', 'jan': '01', 'فبراير': '02', 'february': '02', 'feb': '02',
        'march': '03', 'mar': '03', 'مارس': '03',
        'april': '04', 'apr': '04', 'أبريل': '04',
        'may': '05', 'مايو': '05',
        'june': '06', 'jun': '06', 'يونيو': '06',
        'july': '07', 'jul': '07', 'يوليو': '07',
        'august': '08', 'aug': '08', 'أغسطس': '08',
        'september': '09', 'sep': '09', 'sept': '09', 'سبتمبر': '09',
        'october': '10', 'oct': '10', 'أكتوبر': '10',
        'november': '11', 'nov': '11', 'نوفمبر': '11',
        'december': '12', 'dec': '12', 'ديسمبر': '12',
    }

    # Try "Month Year" format
    parts = s.replace('-', ' ').replace('/', ' ').split()
    for i, part in enumerate(parts):
        lower = part.lower()
        if lower in month_map and i + 1 < len(parts):
            year_match = re.search(r'\d{4}', parts[i + 1])
            if year_match:
                return f"{year_match.group()}/{month_map[lower]}"

    # Try "Year Month" format
    for i, part in enumerate(parts):
        lower = part.lower()
        if lower in month_map and i > 0:
            year_match = re.search(r'\d{4}', parts[i - 1])
            if year_match:
                return f"{year_match.group()}/{month_map[lower]}"

    # Try to extract just a year
    year_match = re.search(r'(19|20)\d{2}', s)
    if year_match:
        return year_match.group()

    return s
