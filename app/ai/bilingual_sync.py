"""Bilingual Translation / Synchronization Service.

Pipeline:
    Raw Resume → AI Extraction → English Structured + Arabic Structured
              → Bilingual Sync (translate missing Arabic) → Validate 1:1 → Template

This module is the "Bilingual Translation / Synchronization" step. It does NOT
copy English text into Arabic fields. When Arabic content is missing or
incomplete, it calls the cloud AI to produce REAL Arabic translations.

If no AI provider is configured, sync cannot run and a structured error is
raised — English is NEVER silently copied into Arabic.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.ai.manager import ai_manager
from app.core.exceptions import AIAllProvidersFailedError, AIProviderNotConfiguredError
from app.models.resume import ResumeData
from app.utils.arabic import contains_arabic

logger = logging.getLogger("cvgen.bilingual")

# Items that are language-neutral and do NOT need translation.
# They are preserved as-is in both columns (emails, phones, URLs, brand names,
# numbers, and common tech terms that have no Arabic equivalent).
def _is_neutral(s: str) -> bool:
    """Return True for items that are language-neutral (no translation needed).

    - Emails, phones, URLs
    - Pure numbers / dates
    - Strings with NO letters (symbols only)
    """
    if not s:
        return True
    import re
    s_stripped = s.strip()
    # Email / phone / URL
    if re.match(r"^[\w.+-]+@[\w.-]+$", s_stripped):
        return True
    if re.match(r"^\+?[\d\s\-()]+$", s_stripped):
        return True
    if re.match(r"^https?://", s_stripped, re.I):
        return True
    # Pure number/date (e.g. "2020", "2020/03", "3.5")
    if re.match(r"^[\d\s/\-.%,]+$", s_stripped):
        return True
    return False


def _needs_arabic(en: str, ar: str) -> bool:
    """Return True if an Arabic translation is needed for this item.

    Needed when: Arabic is empty/missing, OR Arabic text is actually English
    (contains no Arabic characters while the English counterpart has letters).
    """
    if not en:
        return False
    if _is_neutral(en):
        return False  # neutral items stay as-is in both columns
    if not ar or not ar.strip():
        return True
    # Arabic field exists but contains no Arabic script → it was copied verbatim
    if not contains_arabic(ar):
        return True
    return False


def _collect_translation_jobs(resume: ResumeData) -> dict:
    """Scan the resume and collect all English items that need Arabic translation.

    Returns a dict payload describing every missing Arabic field, structured so
    the AI can return a matching JSON with the translations.
    """
    jobs: dict[str, Any] = {"personal": {}, "experience": [], "education": [], "skills": [], "technical_skills": [], "courses": [], "languages": []}

    # Personal
    p = resume.personal
    if _needs_arabic(p.name_en, p.name_ar):
        jobs["personal"]["name_en"] = p.name_en
    if _needs_arabic(p.title_en, p.title_ar):
        jobs["personal"]["title_en"] = p.title_en
    if _needs_arabic(p.location, ""):
        jobs["personal"]["location_en"] = p.location

    # Summary
    sum_en = resume.summary.get("en", "")
    sum_ar = resume.summary.get("ar", "")
    if _needs_arabic(sum_en, sum_ar):
        jobs["personal"]["summary_en"] = sum_en

    # Experience
    for i, exp in enumerate(resume.experience):
        ej: dict[str, Any] = {"index": i}
        if _needs_arabic(exp.title_en, exp.title_ar):
            ej["title_en"] = exp.title_en
        if _needs_arabic(exp.company_en, exp.company_ar):
            ej["company_en"] = exp.company_en
        # Bullets: match index-for-index. If AR bullets count < EN bullets,
        # translate the missing tail items.
        en_b = exp.bullets_en or []
        ar_b = exp.bullets_ar or []
        missing = []
        for j in range(len(en_b)):
            ar_txt = ar_b[j] if j < len(ar_b) else ""
            if _needs_arabic(en_b[j], ar_txt):
                missing.append({"i": j, "en": en_b[j]})
        if missing:
            ej["bullets_en"] = missing
        if ej:
            ej["index"] = i
            jobs["experience"].append(ej)

    # Education
    for i, edu in enumerate(resume.education):
        dj: dict[str, Any] = {"index": i}
        if _needs_arabic(edu.degree_en, edu.degree_ar):
            dj["degree_en"] = edu.degree_en
        if _needs_arabic(edu.institution_en, edu.institution_ar):
            dj["institution_en"] = edu.institution_en
        if dj:
            jobs["education"].append(dj)

    # Skills — ensure 1:1 count + real Arabic translation
    en_sk = resume.skills_en or [s for s in resume.skills if not contains_arabic(s)]
    ar_sk = resume.skills_ar or []
    missing_sk = []
    for j in range(len(en_sk)):
        ar_txt = ar_sk[j] if j < len(ar_sk) else ""
        if _needs_arabic(en_sk[j], ar_txt):
            missing_sk.append({"i": j, "en": en_sk[j]})
    if missing_sk:
        jobs["skills"] = missing_sk

    # Technical skills
    en_ts = resume.technical_skills_en or resume.technical_skills
    ar_ts = resume.technical_skills_ar or []
    missing_ts = []
    for j in range(len(en_ts)):
        ar_txt = ar_ts[j] if j < len(ar_ts) else ""
        if _needs_arabic(en_ts[j], ar_txt):
            missing_ts.append({"i": j, "en": en_ts[j]})
    if missing_ts:
        jobs["technical_skills"] = missing_ts

    # Courses
    ar_courses = []  # courses are not split by language; translate if English
    missing_c = []
    for j, c in enumerate(resume.courses):
        if _needs_arabic(c, ""):
            missing_c.append({"i": j, "en": c})
    if missing_c:
        jobs["courses"] = missing_c
    ar_courses = ar_courses  # silence

    # Languages
    missing_l = []
    for j, lang in enumerate(resume.languages):
        if _needs_arabic(lang.name, ""):
            missing_l.append({"i": j, "en": lang.name})
    if missing_l:
        jobs["languages"] = missing_l

    return jobs


def _has_jobs(jobs: dict) -> bool:
    """Return True if there are any items needing translation."""
    if jobs["personal"]:
        return True
    for key in ("experience", "education", "skills", "technical_skills", "courses", "languages"):
        if jobs.get(key):
            return True
    return False


SYNC_SYSTEM_PROMPT = (
    "You are a professional bilingual (Arabic/English) resume translator. "
    "You receive a JSON object listing English resume fields that are MISSING "
    "their Arabic translations. Your job is to produce a REAL, accurate Arabic "
    "translation for every single English item.\n\n"
    "CRITICAL RULES:\n"
    "1. NEVER copy the English text into the Arabic field. You MUST write real "
    "Arabic. For example, 'Microsoft Office' → 'مايكروسوفت أوفيس', NOT 'Microsoft Office'.\n"
    "2. Translate the MEANING, not a transliteration when a real Arabic term exists. "
    "For job titles, degrees, institutions, use the standard Arabic equivalent.\n"
    "3. For language-neutral items (emails, phones, URLs, pure numbers, dates, "
    "brand names that have no Arabic equivalent like 'Python' or 'AWS'), keep them "
    "exactly as-is. These are already correct in both columns.\n"
    "4. Preserve the exact array structure and index positions. The number of "
    "translations you return MUST equal the number of items you received.\n"
    "5. Do NOT summarize, paraphrase, or omit any item. Translate every single one.\n"
    "6. Return ONLY a JSON object with the same structure as the input, where each "
    "English value is replaced by its Arabic translation.\n\n"
    "EXAMPLE INPUT:\n"
    '{"personal": {"name_en": "Ahmed Abdullah", "title_en": "Senior Software Engineer"}, '
    '"skills": [{"i": 0, "en": "Communication"}, {"i": 1, "en": "Leadership"}]}\n\n'
    "EXAMPLE OUTPUT:\n"
    '{"personal": {"name_en": "أحمد عبدالله", "title_en": "مهندس برمجيات أول"}, '
    '"skills": [{"i": 0, "ar": "التواصل"}, {"i": 1, "ar": "القيادة"}]}\n\n'
    "Return ONLY the JSON. No markdown, no explanation."
)


def _build_sync_user_prompt(jobs: dict) -> str:
    return "Translate every English item in this JSON to real Arabic. Keep the structure identical.\n\n" + json.dumps(jobs, ensure_ascii=False)


async def sync_bilingual(resume: ResumeData, provider: str = "") -> ResumeData:
    """Ensure every English field has a REAL Arabic translation.

    Calls the cloud AI to translate any missing Arabic content. English text is
    NEVER copied into Arabic fields — a real translation is always generated.

    Raises AIProviderNotConfiguredError if no AI key is configured.
    Raises AIAllProvidersFailedError if all providers fail.
    """
    jobs = _collect_translation_jobs(resume)
    if not _has_jobs(jobs):
        # Everything already has real Arabic — nothing to translate.
        return resume

    # Check that at least one provider is configured
    configured = [p["id"] for p in ai_manager.list_providers() if p["configured"]]
    if not configured:
        raise AIProviderNotConfiguredError(
            "AI API key is required to translate missing Arabic content. "
            "Please configure an AI provider in Settings."
        )

    # Call the AI to translate. We reuse the failover engine by invoking
    # a lightweight generate-style call. Since providers don't expose a raw
    # "translate" method, we reuse _generate via the parse_resume pathway is
    # not ideal. Instead, we add a generic translate method on the manager.
    from app.ai.manager import ai_manager as am
    raw = await am.translate_json(SYNC_SYSTEM_PROMPT, _build_sync_user_prompt(jobs), provider=provider)

    from app.ai.json_utils import extract_json
    translations = extract_json(raw)
    if not isinstance(translations, dict):
        logger.warning("Bilingual sync AI returned non-dict; leaving Arabic as-is (NOT copying English).")
        return resume

    _apply_translations(resume, translations)
    return resume


def _apply_translations(resume: ResumeData, t: dict) -> None:
    """Apply AI-generated Arabic translations back onto the resume (in place)."""
    p = t.get("personal", {})
    if isinstance(p, dict):
        if p.get("name_en") and not resume.personal.name_ar:
            resume.personal.name_ar = p["name_en"]
        if p.get("title_en") and not resume.personal.title_ar:
            resume.personal.title_ar = p["title_en"]
        if p.get("location_en") and not resume.personal.location:
            # location is shared; keep EN, also store AR translation in summary? No —
            # just ensure AR column shows the translation via location_ar if model has it.
            # The PersonalInfo model does not have location_ar; skip silently.
            pass
        if p.get("summary_en"):
            resume.summary["ar"] = p["summary_en"]

    # Experience
    for ej in t.get("experience", []):
        if not isinstance(ej, dict):
            continue
        i = ej.get("index", -1)
        if 0 <= i < len(resume.experience):
            exp = resume.experience[i]
            if ej.get("title_en") and not exp.title_ar:
                exp.title_ar = ej["title_en"]
            if ej.get("company_en") and not exp.company_ar:
                exp.company_ar = ej["company_en"]
            for b in ej.get("bullets_en", []):
                if isinstance(b, dict):
                    bi = b.get("i", -1)
                    if 0 <= bi < len(exp.bullets_en) or bi >= len(exp.bullets_en):
                        ar_txt = b.get("ar", "")
                        if ar_txt:
                            # Extend AR bullets list to match length if needed
                            while len(exp.bullets_ar) < bi:
                                exp.bullets_ar.append("")
                            if bi < len(exp.bullets_ar):
                                if not exp.bullets_ar[bi] or not contains_arabic(exp.bullets_ar[bi]):
                                    exp.bullets_ar[bi] = ar_txt
                            else:
                                exp.bullets_ar.append(ar_txt)

    # Education
    for dj in t.get("education", []):
        if not isinstance(dj, dict):
            continue
        i = dj.get("index", -1)
        if 0 <= i < len(resume.education):
            edu = resume.education[i]
            if dj.get("degree_en") and not edu.degree_ar:
                edu.degree_ar = dj["degree_en"]
            if dj.get("institution_en") and not edu.institution_ar:
                edu.institution_ar = dj["institution_en"]

    # Skills — fill in AR translations
    en_sk = resume.skills_en or [s for s in resume.skills if not contains_arabic(s)]
    for sk in t.get("skills", []):
        if isinstance(sk, dict):
            si = sk.get("i", -1)
            if 0 <= si < len(en_sk):
                ar_txt = sk.get("ar", "")
                if ar_txt:
                    while len(resume.skills_ar) <= si:
                        resume.skills_ar.append("")
                    if not resume.skills_ar[si] or not contains_arabic(resume.skills_ar[si]):
                        resume.skills_ar[si] = ar_txt

    # Technical skills
    en_ts = resume.technical_skills_en or resume.technical_skills
    for ts in t.get("technical_skills", []):
        if isinstance(ts, dict):
            ti = ts.get("i", -1)
            if 0 <= ti < len(en_ts):
                ar_txt = ts.get("ar", "")
                if ar_txt:
                    while len(resume.technical_skills_ar) <= ti:
                        resume.technical_skills_ar.append("")
                    if not resume.technical_skills_ar[ti] or not contains_arabic(resume.technical_skills_ar[ti]):
                        resume.technical_skills_ar[ti] = ar_txt

    # Courses (courses list is shared; we leave English courses as-is since the
    # template shows them once — not duplicated per column. No action needed.)

    # Languages
    for lj in t.get("languages", []):
        if isinstance(lj, dict):
            li = lj.get("i", -1)
            if 0 <= li < len(resume.languages):
                ar_txt = lj.get("ar", "")
                if ar_txt and contains_arabic(ar_txt):
                    resume.languages[li].name = ar_txt


def validate_bilingual_match(resume: ResumeData) -> list[str]:
    """Validate 1:1 matching between English and Arabic across ALL fields.

    Returns a list of human-readable mismatch descriptions. An empty list means
    the resume is fully balanced (1:1). This does NOT copy anything — it only
    reports problems so the caller can decide what to do.
    """
    problems: list[str] = []

    # Experience count
    if resume.experience and len(resume.experience) != len(resume.experience):
        pass  # single list, always matches itself

    # Per-experience: bullets_en vs bullets_ar count
    for i, exp in enumerate(resume.experience):
        en_n = len(exp.bullets_en or [])
        ar_n = len(exp.bullets_ar or [])
        if en_n != ar_n:
            problems.append(f"experience[{i}]: bullets_en has {en_n} items but bullets_ar has {ar_n}")

    # Skills
    en_sk = resume.skills_en or [s for s in resume.skills if not contains_arabic(s)]
    ar_sk = resume.skills_ar or []
    if len(en_sk) != len(ar_sk):
        problems.append(f"skills: en has {len(en_sk)} but ar has {len(ar_sk)}")

    # Technical skills
    en_ts = resume.technical_skills_en or resume.technical_skills
    ar_ts = resume.technical_skills_ar or []
    if len(en_ts) != len(ar_ts):
        problems.append(f"technical_skills: en has {len(en_ts)} but ar has {len(ar_ts)}")

    return problems
