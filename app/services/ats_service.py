"""ATS analysis service — deterministic checks + optional AI layer.

Deterministic checks cover:
  - Contact information
  - Professional summary / objective
  - Experience (presence, quantification)
  - Education
  - Skills (count, relevance)
  - Keywords (from job description)
  - Languages
  - Courses / Certifications
  - Length / word count
  - Formatting (bullets, dates)
  - Section completeness

Returns a 0-100 score, A-F grade, per-check results, and recommendations.
"""
from __future__ import annotations

import logging
import re
from typing import List

from app.models.resume import ResumeData
from app.schemas.ats import ATSCheck, ATSRecommendation, ATSResponse
from app.services.resume_normalizer import normalize_resume_data

logger = logging.getLogger("cvgen.ats")

GRADE_BOUNDS = [(90, "A"), (80, "B"), (70, "C"), (60, "D"), (0, "F")]


def _grade(score: int) -> str:
    for bound, g in GRADE_BOUNDS:
        if score >= bound:
            return g
    return "F"


def _count_words(resume: ResumeData) -> int:
    chunks = [
        resume.summary_text(), resume.objective_text(),
        resume.personal.name, resume.personal.title,
    ]
    for e in resume.experience:
        chunks.append(e.title)
        chunks.append(e.company)
        chunks.append(e.description)
        chunks.extend(e.bullets)
        chunks.extend(e.bullets_en)
        chunks.extend(e.bullets_ar)
    for ed in resume.education:
        chunks.append(ed.degree)
        chunks.append(ed.institution)
    chunks.extend(resume.skills)
    chunks.extend(resume.technical_skills)
    chunks.extend(resume.soft_skills)
    text = " ".join(c for c in chunks if c)
    return len(text.split())


def _quantified_bullets(resume: ResumeData) -> int:
    total = 0
    quantified = 0
    pat = re.compile(r"\d+%|\$\d|\d+x|\b\d{2,}\b")
    for e in resume.experience:
        for b in (e.bullets + e.bullets_en + e.bullets_ar):
            if b.strip():
                total += 1
                if pat.search(b):
                    quantified += 1
    return quantified, total


async def analyze_resume(resume: ResumeData, job_description: str = "", use_ai: bool = False, provider: str = "") -> ATSResponse:
    checks: List[ATSCheck] = []
    recs: List[ATSRecommendation] = []

    # --- Contact ---
    p = resume.personal
    contact_fields = [bool(p.email), bool(p.phone), bool(p.location or p.linkedin or p.website)]
    contact_score = int(sum(contact_fields) / 3 * 100)
    checks.append(ATSCheck(
        category="Contact Information",
        passed=contact_score >= 66,
        score=contact_score,
        message=f"{sum(contact_fields)}/3 core contact fields present",
        detail="Email, phone, and location/LinkedIn/website recommended.",
    ))
    if not p.email:
        recs.append(ATSRecommendation(priority="high", category="Contact", message="Add a professional email address."))
    if not p.phone:
        recs.append(ATSRecommendation(priority="high", category="Contact", message="Add a phone number."))
    if not (p.linkedin or p.website):
        recs.append(ATSRecommendation(priority="medium", category="Contact", message="Add a LinkedIn profile or personal website."))

    # --- Summary ---
    summary_text = resume.summary_text()
    summary_score = 100 if len(summary_text.split()) >= 20 else (50 if summary_text else 0)
    checks.append(ATSCheck(
        category="Professional Summary",
        passed=bool(summary_text) and len(summary_text.split()) >= 20,
        score=summary_score,
        message="Summary present and substantial" if summary_score == 100 else ("Summary too short" if summary_text else "No summary"),
    ))
    if not summary_text:
        recs.append(ATSRecommendation(priority="high", category="Summary", message="Add a 2-3 sentence professional summary."))

    # --- Experience ---
    has_exp = len(resume.experience) > 0
    exp_score = min(100, len(resume.experience) * 40)
    quant, total_b = _quantified_bullets(resume)
    quant_ratio = (quant / total_b) if total_b else 0
    if has_exp and quant_ratio < 0.3:
        exp_score = int(exp_score * 0.8)
    checks.append(ATSCheck(
        category="Experience",
        passed=has_exp,
        score=exp_score,
        message=f"{len(resume.experience)} experience entries; {quant}/{total_b} quantified bullets",
    ))
    if not has_exp:
        recs.append(ATSRecommendation(priority="high", category="Experience", message="Add work experience entries."))
    elif quant_ratio < 0.3:
        recs.append(ATSRecommendation(priority="high", category="Experience", message="Quantify achievements with numbers (%, $, time saved)."))

    # --- Education ---
    has_edu = len(resume.education) > 0
    edu_score = 100 if has_edu else 0
    checks.append(ATSCheck(
        category="Education",
        passed=has_edu,
        score=edu_score,
        message=f"{len(resume.education)} education entries",
    ))
    if not has_edu:
        recs.append(ATSRecommendation(priority="medium", category="Education", message="Add at least one education entry."))

    # --- Skills ---
    total_skills = len(resume.skills) + len(resume.technical_skills) + len(resume.soft_skills)
    skills_score = min(100, total_skills * 10)
    checks.append(ATSCheck(
        category="Skills",
        passed=total_skills >= 5,
        score=skills_score,
        message=f"{total_skills} skills total",
    ))
    if total_skills < 5:
        recs.append(ATSRecommendation(priority="high", category="Skills", message="Add at least 5-10 relevant skills."))

    # --- Keywords (vs job description) ---
    keywords_found: List[str] = []
    keywords_missing: List[str] = []
    if job_description:
        jd_tokens = set(re.findall(r"[A-Za-z][A-Za-z+#.0-9]{2,}", job_description.lower()))
        resume_text = _resume_to_text(resume).lower()
        # common stop words to skip
        stop = {"the", "and", "for", "with", "you", "are", "our", "this", "that", "will", "have", "from", "your", "all", "any", "can", "but", "not", "they", "their"}
        meaningful = [t for t in jd_tokens if t not in stop and len(t) > 3]
        for kw in meaningful:
            if kw in resume_text:
                keywords_found.append(kw)
            else:
                keywords_missing.append(kw)
        kw_score = int((len(keywords_found) / max(1, len(meaningful))) * 100) if meaningful else 100
        checks.append(ATSCheck(
            category="Keyword Match",
            passed=kw_score >= 50,
            score=kw_score,
            message=f"{len(keywords_found)}/{len(meaningful)} job keywords matched",
        ))
        if keywords_missing:
            top = ", ".join(keywords_missing[:8])
            recs.append(ATSRecommendation(priority="high", category="Keywords", message=f"Add missing keywords: {top}"))

    # --- Languages ---
    lang_score = min(100, len(resume.languages) * 50)
    checks.append(ATSCheck(
        category="Languages",
        passed=len(resume.languages) >= 1,
        score=lang_score,
        message=f"{len(resume.languages)} languages",
    ))

    # --- Courses / Certifications ---
    cert_score = min(100, (len(resume.certifications) + len(resume.courses)) * 25)
    checks.append(ATSCheck(
        category="Certifications & Courses",
        passed=bool(resume.certifications or resume.courses),
        score=cert_score,
        message=f"{len(resume.certifications)} certs, {len(resume.courses)} courses",
    ))

    # --- Length ---
    wc = _count_words(resume)
    if 300 <= wc <= 900:
        length_score = 100
    elif wc < 300:
        length_score = max(0, int(wc / 300 * 100))
    else:
        length_score = max(40, 100 - (wc - 900) // 10)
    checks.append(ATSCheck(
        category="Length",
        passed=300 <= wc <= 900,
        score=length_score,
        message=f"{wc} words",
    ))
    if wc < 300:
        recs.append(ATSRecommendation(priority="medium", category="Length", message="Resume is short — add more detail to experience and skills."))
    elif wc > 900:
        recs.append(ATSRecommendation(priority="medium", category="Length", message="Resume may be too long — consider trimming to 1-2 pages."))

    # --- Formatting ---
    has_bullets = any(e.bullets or e.bullets_en or e.bullets_ar for e in resume.experience)
    has_dates = any(e.start_date or e.end_date for e in resume.experience)
    fmt_score = (100 if has_bullets else 0) + (100 if has_dates else 0)
    fmt_score = fmt_score // 2 if (has_bullets or has_dates) else 0
    checks.append(ATSCheck(
        category="Formatting",
        passed=has_bullets and has_dates,
        score=fmt_score,
        message=f"bullets={'yes' if has_bullets else 'no'}, dates={'yes' if has_dates else 'no'}",
    ))

    # --- Section completeness ---
    sections_present = sum([
        bool(resume.summary or resume.objective),
        bool(resume.experience),
        bool(resume.education),
        total_skills > 0,
        bool(resume.languages),
    ])
    completeness_score = int(sections_present / 5 * 100)
    checks.append(ATSCheck(
        category="Section Completeness",
        passed=sections_present >= 4,
        score=completeness_score,
        message=f"{sections_present}/5 core sections present",
    ))

    # --- Optional AI layer ---
    if use_ai:
        try:
            from app.ai.manager import ai_manager
            ai_result = await ai_manager.analyze_ats(resume.model_dump(), job_description, provider=provider)
            if isinstance(ai_result, dict):
                for r in (ai_result.get("recommendations") or [])[:5]:
                    if isinstance(r, dict):
                        recs.append(ATSRecommendation(
                            priority=r.get("priority", "medium"),
                            category=r.get("category", "AI"),
                            message=r.get("message", ""),
                        ))
                if ai_result.get("keywords_missing"):
                    keywords_missing.extend(ai_result["keywords_missing"])
        except Exception as e:
            logger.warning("AI ATS analysis skipped: %s", e)

    # --- Final score (weighted average of check scores) ---
    if checks:
        total = sum(c.score for c in checks)
        score = int(total / len(checks))
    else:
        score = 0

    return ATSResponse(
        score=score,
        grade=_grade(score),
        checks=checks,
        recommendations=recs,
        keywords_found=keywords_found,
        keywords_missing=list(set(keywords_missing)),
    )


def _resume_to_text(resume: ResumeData) -> str:
    parts = [
        resume.personal.name, resume.personal.title, resume.personal.name_en, resume.personal.name_ar,
        resume.summary_text(), resume.objective_text(),
    ]
    for e in resume.experience:
        parts.append(e.title)
        parts.append(e.title_en)
        parts.append(e.title_ar)
        parts.append(e.company)
        parts.append(e.description)
        parts.extend(e.bullets)
        parts.extend(e.bullets_en)
        parts.extend(e.bullets_ar)
    for ed in resume.education:
        parts.append(ed.degree)
        parts.append(ed.institution)
    parts.extend(resume.skills)
    parts.extend(resume.technical_skills)
    parts.extend(resume.soft_skills)
    parts.extend(resume.courses)
    parts.extend(resume.volunteering)
    for c in resume.certifications:
        parts.append(c.name)
    for l in resume.languages:
        parts.append(l.name)
    return " ".join(p for p in parts if p)
