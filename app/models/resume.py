"""Unified ResumeData models — the SINGLE source of truth.

Every template, parser, exporter and ATS analyzer consumes these models.
No duplicate ResumeData definitions exist anywhere else in the codebase.
"""
from __future__ import annotations

import re
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class PersonalInfo(BaseModel):
    name: str = ""
    name_en: str = ""
    name_ar: str = ""
    title: str = ""
    title_en: str = ""
    title_ar: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    website: str = ""
    github: str = ""

    def display_name(self, lang: str = "en") -> str:
        if lang == "ar" and self.name_ar:
            return self.name_ar
        if lang == "en" and self.name_en:
            return self.name_en
        return self.name or self.name_en or self.name_ar


class ExperienceItem(BaseModel):
    title: str = ""
    title_en: str = ""
    title_ar: str = ""
    company: str = ""
    company_en: str = ""
    company_ar: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    current: bool = False
    description: str = ""
    bullets: List[str] = Field(default_factory=list)
    bullets_en: List[str] = Field(default_factory=list)
    bullets_ar: List[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    degree: str = ""
    degree_en: str = ""
    degree_ar: str = ""
    institution: str = ""
    institution_en: str = ""
    institution_ar: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    year: str = ""
    gpa: str = ""
    description: str = ""


class SkillItem(BaseModel):
    name: str = ""
    level: str = ""


class LanguageItem(BaseModel):
    name: str = ""
    level: str = ""


class ProjectItem(BaseModel):
    name: str = ""
    description: str = ""
    url: str = ""
    technologies: List[str] = Field(default_factory=list)


class CertificationItem(BaseModel):
    name: str = ""
    issuer: str = ""
    date: str = ""
    url: str = ""


class CourseItem(BaseModel):
    name: str = ""
    issuer: str = ""
    date: str = ""


class AchievementItem(BaseModel):
    title: str = ""
    description: str = ""
    date: str = ""


class ReferenceItem(BaseModel):
    name: str = ""
    position: str = ""
    contact: str = ""


class OtherItem(BaseModel):
    label: str = ""
    value: str = ""


# ---------------------------------------------------------------------------
# Unified ResumeData
# ---------------------------------------------------------------------------


class ResumeData(BaseModel):
    """The single canonical resume model used everywhere in CVGen Pro."""

    personal: PersonalInfo = Field(default_factory=PersonalInfo)
    summary: dict = Field(default_factory=dict)      # {"en": "...", "ar": "..."}
    objective: dict = Field(default_factory=dict)    # {"en": "...", "ar": "..."}

    experience: List[ExperienceItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)

    # Skills are REQUIRED bilingual fields (enforced 1:1 match).
    # The AI parser MUST populate both _en and _ar arrays with identical counts.
    # If a section is missing, the AI auto-generates content rather than leaving empty.
    skills: List[str] = Field(default_factory=list)
    skills_en: List[str] = Field(default_factory=list)
    skills_ar: List[str] = Field(default_factory=list)
    technical_skills: List[str] = Field(default_factory=list)
    technical_skills_en: List[str] = Field(default_factory=list)
    technical_skills_ar: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)

    courses: List[str] = Field(default_factory=list)
    certifications: List[CertificationItem] = Field(default_factory=list)
    languages: List[LanguageItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    volunteering: List[str] = Field(default_factory=list)
    achievements: List[AchievementItem] = Field(default_factory=list)
    references: List[ReferenceItem] = Field(default_factory=list)
    other: List[OtherItem] = Field(default_factory=list)

    # metadata
    template_id: str = "official_bilingual_master"
    lang: str = "en"  # primary display language: en | ar | bilingual

    # ------------------------------------------------------------------
    # Validators — strip junk and guard against bad data
    # ------------------------------------------------------------------

    @field_validator("skills", "skills_en", "skills_ar", "technical_skills", "technical_skills_en", "technical_skills_ar", "soft_skills", "courses", "volunteering", mode="before")
    @classmethod
    def _coerce_str_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            # allow comma separated string
            return [s.strip() for s in re.split(r"[,\n]", v) if s.strip()]
        if isinstance(v, list):
            out = []
            for item in v:
                if isinstance(item, str):
                    if item.strip():
                        out.append(item.strip())
                elif isinstance(item, dict) and item.get("name"):
                    out.append(str(item["name"]).strip())
            return out
        return []

    @field_validator("summary", "objective", mode="before")
    @classmethod
    def _coerce_lang_dict(cls, v):
        if v is None:
            return {}
        if isinstance(v, str):
            return {"en": v.strip()} if v.strip() else {}
        if isinstance(v, dict):
            return {k: str(val).strip() for k, val in v.items() if str(val).strip()}
        return {}

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def summary_text(self, lang: str = "en") -> str:
        if not self.summary:
            return ""
        return self.summary.get(lang) or self.summary.get("en") or ""

    def objective_text(self, lang: str = "en") -> str:
        if not self.objective:
            return ""
        return self.objective.get(lang) or self.objective.get("en") or ""

    def is_empty(self) -> bool:
        return not (
            self.personal.name or self.personal.name_en or self.personal.name_ar
            or self.summary or self.objective
            or self.experience or self.education
            or self.skills or self.technical_skills or self.soft_skills
            or self.courses or self.certifications or self.languages
            or self.projects or self.volunteering or self.achievements
        )


class ResumeDataIn(ResumeData):
    """Input variant — identical shape, used for request validation."""


# ---------------------------------------------------------------------------
# Sample data (used by /api/resume/sample)
# ---------------------------------------------------------------------------


def sample_resume(lang: str = "en") -> ResumeData:
    if lang == "ar":
        return ResumeData(
            personal=PersonalInfo(
                name_ar="أحمد عبدالله",
                name="Ahmed Abdullah",
                title_ar="مهندس برمجيات أول",
                email="ahmed@example.com",
                phone="+966500000000",
                location="الرياض، المملكة العربية السعودية",
                linkedin="linkedin.com/in/ahmed",
            ),
            summary={"ar": "مهندس برمجيات بخبرة 8 سنوات في تطوير تطبيقات الويب والسحابة."},
            experience=[
                ExperienceItem(
                    title_ar="مهندس برمجيات أول",
                    company_ar="شركة التقنية",
                    start_date="2020",
                    end_date="حتى الآن",
                    current=True,
                    bullets_ar=["تصميم وتطوير منصات سحابية", "قيادة فريق من 5 مطورين"],
                )
            ],
            education=[
                EducationItem(
                    degree_ar="بكالوريوس علوم حاسب",
                    institution_ar="جامعة الملك سعود",
                    end_date="2015",
                )
            ],
            skills=["Python", "FastAPI", "React", "AWS"],
            languages=[LanguageItem(name="العربية", level="ممتاز"), LanguageItem(name="الإنجليزية", level="جيد جدا")],
        )

    if lang == "bilingual":
        return ResumeData(
            personal=PersonalInfo(
                name_en="Ahmed Abdullah",
                name_ar="أحمد عبدالله",
                title_en="Senior Software Engineer",
                title_ar="مهندس برمجيات أول",
                email="ahmed@example.com",
                phone="+966500000000",
                location="Riyadh, Saudi Arabia",
                linkedin="linkedin.com/in/ahmed",
            ),
            summary={
                "en": "Senior software engineer with 8+ years building scalable web platforms.",
                "ar": "مهندس برمجيات بخبرة 8 سنوات في تطوير تطبيقات الويب والسحابة.",
            },
            experience=[
                ExperienceItem(
                    title_en="Senior Software Engineer",
                    title_ar="مهندس برمجيات أول",
                    company_en="Tech Corp",
                    company_ar="شركة التقنية",
                    start_date="2020",
                    end_date="Present",
                    current=True,
                    bullets_en=["Designed cloud platforms", "Led a team of 5 engineers"],
                    bullets_ar=["تصميم وتطوير منصات سحابية", "قيادة فريق من 5 مطورين"],
                )
            ],
            education=[
                EducationItem(
                    degree_en="B.Sc. Information Science",
                    degree_ar="بكالوريوس علم المعلومات",
                    institution_en="Umm Al-Qura University",
                    institution_ar="جامعة أم القرى",
                    end_date="2015",
                )
            ],
            skills=["Python", "FastAPI", "React", "AWS", "Docker"],
            technical_skills=["Python", "JavaScript", "TypeScript", "React", "Node.js", "SQL", "Docker", "AWS"],
            languages=[
                LanguageItem(name="Arabic", level="Native"),
                LanguageItem(name="English", level="Fluent"),
            ],
        )

    # English default
    return ResumeData(
        personal=PersonalInfo(
            name_en="Jane Doe",
            name="Jane Doe",
            title_en="Senior Product Designer",
            email="jane.doe@example.com",
            phone="+1 (555) 123-4567",
            location="San Francisco, CA",
            linkedin="linkedin.com/in/janedoe",
            website="janedoe.design",
        ),
        summary={"en": "Senior product designer with 8+ years crafting user-centric digital experiences for SaaS and fintech products."},
        experience=[
            ExperienceItem(
                title_en="Senior Product Designer",
                company_en="Acme Corp",
                start_date="2021",
                end_date="Present",
                current=True,
                bullets_en=[
                    "Led end-to-end design for a fintech dashboard used by 200k+ users",
                    "Established the company design system adopted across 6 product teams",
                    "Increased onboarding completion by 34% through UX research",
                ],
            ),
            ExperienceItem(
                title_en="Product Designer",
                company_en="Beta Studio",
                start_date="2017",
                end_date="2021",
                bullets_en=[
                    "Shipped 15+ mobile features for iOS and Android",
                    "Collaborated with engineering to build a React component library",
                ],
            ),
        ],
        education=[
            EducationItem(
                degree_en="B.A. Interaction Design",
                institution_en="California College of the Arts",
                start_date="2013",
                end_date="2017",
            )
        ],
        skills=["Figma", "Prototyping", "User Research", "Design Systems", "HTML/CSS", "Accessibility"],
        technical_skills=["Figma", "Sketch", "Principle"],
        soft_skills=["Leadership", "Collaboration", "Communication"],
        languages=[LanguageItem(name="English", level="Native"), LanguageItem(name="Spanish", level="Conversational")],
        certifications=[
            CertificationItem(name="Nielsen Norman UX Certification", issuer="NN/g", date="2019"),
        ],
    )
