"""Shared prompt builders for AI providers."""
from __future__ import annotations

import json

PARSE_SYSTEM_PROMPT = (
    "You are an expert resume parser. Read the ENTIRE resume document carefully and "
    "extract structured information. Preserve the semantic structure: one job = one "
    "experience entry (do NOT split a single job into multiple entries). "
    "Never put contact info (email/phone/URLs) into skills, courses, or any other list. "
    "Return ONLY valid JSON matching the schema below. No markdown, no explanation.\n\n"
    "JSON SCHEMA:\n"
    "{\n"
    '  "personal": {"name": "", "name_en": "", "name_ar": "", "title": "", "title_en": "", "title_ar": "", "email": "", "phone": "", "location": "", "linkedin": "", "website": "", "github": ""},\n'
    '  "summary": {"en": "", "ar": ""},\n'
    '  "objective": {"en": "", "ar": ""},\n'
    '  "experience": [{"title": "", "title_en": "", "title_ar": "", "company": "", "company_en": "", "company_ar": "", "location": "", "start_date": "", "end_date": "", "current": false, "description": "", "bullets": [], "bullets_en": [], "bullets_ar": []}],\n'
    '  "education": [{"degree": "", "degree_en": "", "degree_ar": "", "institution": "", "institution_en": "", "institution_ar": "", "location": "", "start_date": "", "end_date": "", "year": "", "gpa": "", "description": ""}],\n'
    '  "skills": [],\n'
    '  "technical_skills": [],\n'
    '  "soft_skills": [],\n'
    '  "courses": [],\n'
    '  "certifications": [{"name": "", "issuer": "", "date": "", "url": ""}],\n'
    '  "languages": [{"name": "", "level": ""}],\n'
    '  "projects": [{"name": "", "description": "", "url": "", "technologies": []}],\n'
    '  "volunteering": [],\n'
    '  "achievements": [{"title": "", "description": "", "date": ""}],\n'
    '  "references": [{"name": "", "position": "", "contact": ""}],\n'
    '  "other": []\n'
    "}\n\n"
    "RULES:\n"
    "1. One job position = ONE experience object with multiple bullets. NEVER split bullets into separate experience entries.\n"
    "2. Email, phone, LinkedIn, website, GitHub MUST go in 'personal' only.\n"
    "3. If content is Arabic, fill the _ar fields; if English, fill _en; if bilingual, fill both.\n"
    "4. Leave fields empty ('' or []) when information is not present. Do NOT invent data.\n"
    "5. Return ONLY the JSON object."
)


def build_parse_prompt(text: str, lang: str) -> str:
    hint = ""
    if lang == "ar":
        hint = "The resume is primarily in Arabic."
    elif lang == "en":
        hint = "The resume is primarily in English."
    elif lang == "bilingual":
        hint = "The resume is bilingual (Arabic + English)."
    return (
        f"{hint}\n\nParse the following resume and return ONLY the JSON object:\n\n"
        f"--- RESUME START ---\n{text}\n--- RESUME END ---"
    )


def build_improve_prompt(section: str, content: str, lang: str) -> str:
    return (
        f"You are a professional resume writer. Improve the following '{section}' section. "
        f"Make it concise, impactful, and ATS-friendly. Use strong action verbs. "
        f"Keep the same language ({lang}). Return ONLY the improved text, no explanation.\n\n"
        f"--- ORIGINAL ---\n{content}\n--- END ---"
    )


def build_summary_prompt(role: str, years: int, skills: list[str], lang: str) -> str:
    skills_str = ", ".join(skills[:10]) if skills else "various"
    return (
        f"Write a professional resume summary (2-3 sentences) for a {role} with {years} years "
        f"of experience. Key skills: {skills_str}. Language: {lang}. "
        "Return ONLY the summary text, no headings or explanation."
    )


def build_ats_prompt(resume_dict: dict, job_description: str) -> str:
    resume_str = json.dumps(resume_dict, ensure_ascii=False, indent=2)[:6000]
    jd_part = f"\n\nJOB DESCRIPTION:\n{job_description[:3000]}" if job_description else ""
    return (
        "You are an ATS (Applicant Tracking System) expert. Analyze this resume and return ONLY JSON:\n"
        "{\n"
        '  "score": 0-100,\n'
        '  "recommendations": [{"priority": "high|medium|low", "category": "", "message": ""}],\n'
        '  "keywords_found": [],\n'
        '  "keywords_missing": []\n'
        "}\n\n"
        f"RESUME:\n{resume_str}{jd_part}\n\nReturn ONLY the JSON."
    )


def build_cover_letter_prompt(resume_dict: dict, job_description: str) -> str:
    resume_str = json.dumps(resume_dict, ensure_ascii=False, indent=2)[:4000]
    return (
        "Write a professional cover letter based on this resume"
        + (f" for this job:\n{job_description[:2000]}" if job_description else ".")
        + f"\n\nRESUME:\n{resume_str}\n\nReturn ONLY the cover letter text."
    )
