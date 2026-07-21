"""Shared prompt builders for AI providers."""
from __future__ import annotations

import json

PARSE_SYSTEM_PROMPT = (
    "You are an expert bilingual resume parser. Read the ENTIRE resume document carefully and "
    "extract structured information in BOTH Arabic and English.\n\n"
    "CRITICAL BILINGUAL RULES:\n"
    "1. You MUST provide BOTH Arabic and English versions for EVERY field. Never leave any _en or _ar field empty.\n"
    "2. If the resume is in Arabic only, you MUST translate all content to English for the _en fields.\n"
    "3. If the resume is in English only, you MUST translate all content to Arabic for the _ar fields.\n"
    "4. The number of bullet points (bullets_en, bullets_ar) in each experience MUST be EXACTLY the same count.\n"
    "5. The number of items in skills_en MUST equal skills_ar. Translate each skill.\n"
    "6. The number of items in technical_skills_en MUST equal technical_skills_ar.\n"
    "7. The number of experience entries in experience_en MUST equal experience_ar.\n"
    "8. The number of education entries in education_en MUST equal education_ar.\n"
    "9. This ensures balanced column lengths between Arabic and English.\n\n"
    "DATE FORMAT RULES:\n"
    "- All dates MUST be in format: YYYY/MM or 'Present'.\n"
    "- Example: 2024/03 - Present, 2018/09 - 2022/12.\n"
    "- start_date and end_date must use this format consistently.\n"
    "- If currently employed, end_date = 'Present'.\n\n"
    "NAME RULES:\n"
    "- Do NOT add extra spaces or newlines inside names.\n"
    "- name_en and name_ar must be clean single-line strings.\n\n"
    "SCHEMA (return ONLY this JSON, no markdown, no explanation):\n"
    "{\n"
    '  "personal": {"name": "", "name_en": "", "name_ar": "", "title": "", "title_en": "", "title_ar": "", "email": "", "phone": "", "location": "", "location_en": "", "location_ar": "", "linkedin": "", "website": "", "github": ""},\n'
    '  "summary": {"en": "", "ar": ""},\n'
    '  "objective": {"en": "", "ar": ""},\n'
    '  "experience": [{"title": "", "title_en": "", "title_ar": "", "company": "", "company_en": "", "company_ar": "", "location": "", "start_date": "", "end_date": "", "current": false, "description": "", "description_en": "", "description_ar": "", "bullets": [], "bullets_en": [], "bullets_ar": []}],\n'
    '  "education": [{"degree": "", "degree_en": "", "degree_ar": "", "institution": "", "institution_en": "", "institution_ar": "", "location": "", "start_date": "", "end_date": "", "year": "", "gpa": "", "description": ""}],\n'
    '  "skills": [],\n'
    '  "skills_en": [],\n'
    '  "skills_ar": [],\n'
    '  "technical_skills": [],\n'
    '  "technical_skills_en": [],\n'
    '  "technical_skills_ar": [],\n'
    '  "soft_skills": [],\n'
    '  "courses": [],\n'
    '  "certifications": [{"name": "", "issuer": "", "date": "", "url": ""}],\n'
    '  "languages": [{"name": "", "name_en": "", "name_ar": "", "level": ""}],\n'
    '  "projects": [{"name": "", "description": "", "url": "", "technologies": []}],\n'
    '  "volunteering": [],\n'
    '  "achievements": [{"title": "", "description": "", "date": ""}],\n'
    '  "references": [{"name": "", "position": "", "contact": ""}],\n'
    '  "other": []\n'
    "}\n\n"
    "ABSOLUTE RULES:\n"
    "1. One job position = ONE experience object. NEVER split bullets into separate entries.\n"
    "2. Email, phone, LinkedIn, website, GitHub MUST go in 'personal' only.\n"
    "3. NEVER leave skills_en, skills_ar, technical_skills_en, or technical_skills_ar empty. Always translate.\n"
    "4. bullets_en and bullets_ar must have the SAME count for each experience entry.\n"
    "5. If information is truly missing, use empty string ''. Never use null.\n"
    "6. Clean all names: no extra spaces, no newlines.\n"
    "7. Return ONLY the JSON object.\n\n"
    "TEMPLATE STRUCTURE (7 SECTIONS — fill ALL of them):\n"
    "The resume template has exactly 7 sections in this order:\n"
    "1. CAREER OBJECTIVE / الهدف الوظيفي\n"
    "2. EDUCATION / التعليم\n"
    "3. EXPERIENCE / الخبرات المهنية (dates in format: Month Year - Month Year, e.g. March 2024 - Present)\n"
    "4. COURSES / الدورات\n"
    "5. SKILLS / المهارات\n"
    "6. TECHNICAL SKILLS / المهارات التقنية\n"
    "7. LANGUAGES / اللغات\n"
    "You MUST fill ALL 7 sections with content. If a section is missing from the input, generate it.\n\n"
    "AUTO-FILL RULE (PROACTIVE GENERATION):\n"
    "If the user did not mention or input data for a specific section (such as: experience, courses, skills, or objective/summary), "
    "you are STRICTLY FORBIDDEN from leaving that section empty or returning an empty array. "
    "Instead, as an HR expert, you MUST create and generate professional, accurate, and highly relevant content "
    "appropriate for the user's job title or field. The generated content must follow the same strict balance rules "
    "(same number of bullets in Arabic and English) and the same data schema.\n\n"
    "VISUAL HARMONY & SPACE CONSTRAINT RULE:\n"
    "Imagine this content will be printed on an A4 page with two columns. You are STRICTLY FORBIDDEN from generating "
    "long texts that break the layout. Adhere to these limits precisely:\n"
    "1. Summary/Objective: very concise, no more than 3 lines (max 40 words).\n"
    "2. Experience: no more than 3-4 bullets per job, each bullet is one line or two lines max.\n"
    "3. Skills: no more than 6 skills (to prevent text from dropping to the bottom of the page).\n"
    "4. Visual Balance: ensure the Arabic sentence length is very close to the English translated sentence length "
    "to keep both columns equal in height and final appearance."
)


def build_parse_prompt(text: str, lang: str) -> str:
    hint = ""
    if lang == "ar":
        hint = "The resume is primarily in Arabic. You MUST translate everything to English for _en fields."
    elif lang == "en":
        hint = "The resume is primarily in English. You MUST translate everything to Arabic for _ar fields."
    elif lang == "bilingual":
        hint = "The resume is bilingual (Arabic + English). Fill both _en and _ar fields."
    return (
        f"{hint}\n\n"
        f"IMPORTANT: skills_en and skills_ar must have the SAME number of items. "
        f"bullets_en and bullets_ar must have the SAME number of items per experience. "
        f"All dates in YYYY/MM format.\n\n"
        f"Parse the following resume and return ONLY the JSON object:\n\n"
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
