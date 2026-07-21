"""CVGen Pro — Reflex State Management

Uses typed dataclasses instead of Dict for nested data,
so Reflex can properly infer types for rx.foreach.
"""
from __future__ import annotations

from pydantic import BaseModel

import reflex as rx
from typing import List


# ---------------------------------------------------------------------------
# Typed data models (NOT Dict — Reflex needs concrete types for foreach)
# ---------------------------------------------------------------------------

class BulletData(BaseModel):
    """Single bullet point."""
    text: str = ""


class ExperienceData(BaseModel):
    """Single experience entry — typed for rx.foreach."""
    title_en: str = ""
    title_ar: str = ""
    company_en: str = ""
    company_ar: str = ""
    start_date: str = ""
    end_date: str = ""
    current: bool = False
    bullets_en: List[BulletData] = []
    bullets_ar: List[BulletData] = []


class EducationData(BaseModel):
    """Single education entry — typed for rx.foreach."""
    degree_en: str = ""
    degree_ar: str = ""
    institution_en: str = ""
    institution_ar: str = ""
    year: str = ""
    gpa: str = ""


class LanguageData(BaseModel):
    """Single language entry."""
    name: str = ""
    level: str = ""


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class ResumeState(rx.State):
    """Main state for the resume application."""

    # ===== Personal Info =====
    name_en: str = ""
    name_ar: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""

    # ===== Summary =====
    summary_en: str = ""
    summary_ar: str = ""

    # ===== Typed Arrays (for rx.foreach) =====
    experience: List[ExperienceData] = []
    education: List[EducationData] = []
    skills_en: List[str] = []
    skills_ar: List[str] = []
    technical_skills_en: List[str] = []
    technical_skills_ar: List[str] = []
    courses: List[str] = []
    languages: List[LanguageData] = []

    # ===== Template Selection =====
    template_id: str = "official_bilingual_master"
    template_count: int = 3

    # ===== Editor Controls =====
    font_size: float = 9.0
    line_height: float = 1.4
    section_spacing: int = 6
    column_distance: int = 16
    margin: float = 10.0

    # ===== Preview State =====
    page_count: int = 1
    current_page: int = 1

    # ===== Loading States =====
    is_generating: bool = False

    # ------------------------------------------------------------------
    # Computed properties
    # ------------------------------------------------------------------

    @rx.var
    def has_experience(self) -> bool:
        return len(self.experience) > 0

    @rx.var
    def has_education(self) -> bool:
        return len(self.education) > 0

    @rx.var
    def has_skills_en(self) -> bool:
        return len(self.skills_en) > 0

    @rx.var
    def has_skills_ar(self) -> bool:
        return len(self.skills_ar) > 0

    @rx.var
    def display_name(self) -> str:
        return self.name_en or self.name_ar or "Untitled"

    @rx.var
    def is_overflow(self) -> bool:
        return self.page_count > 1

    # ------------------------------------------------------------------
    # Event Handlers
    # ------------------------------------------------------------------

    def load_sample(self):
        """Load sample bilingual resume data."""
        self.name_en = "Ahmed Abdullah"
        self.name_ar = "أحمد عبدالله"
        self.email = "ahmed@example.com"
        self.phone = "+966500000000"
        self.location = "Riyadh, Saudi Arabia"
        self.summary_en = "Senior software engineer with 8+ years building scalable web platforms."
        self.summary_ar = "مهندس برمجيات بخبرة 8 سنوات في تطوير تطبيقات الويب والسحابة."

        self.experience = [
            ExperienceData(
                title_en="Senior Software Engineer",
                title_ar="مهندس برمجيات أول",
                company_en="Tech Corp",
                company_ar="شركة التقنية",
                start_date="2020/01",
                end_date="Present",
                current=True,
                bullets_en=[
                    BulletData(text="Designed cloud platforms serving 1M+ users"),
                    BulletData(text="Led a team of 5 engineers"),
                ],
                bullets_ar=[
                    BulletData(text="تصميم منصات سحابية تخدم مليون مستخدم"),
                    BulletData(text="قيادة فريق من 5 مطورين"),
                ],
            ),
            ExperienceData(
                title_en="Software Engineer",
                title_ar="مهندس برمجيات",
                company_en="Startup Inc",
                company_ar="ستارت أب",
                start_date="2015/06",
                end_date="2019/12",
                bullets_en=[
                    BulletData(text="Built REST APIs in Python"),
                    BulletData(text="Shipped 20+ features"),
                ],
                bullets_ar=[
                    BulletData(text="بناء واجهات برمجية بلغة بايثون"),
                    BulletData(text="تطوير 20 ميزة"),
                ],
            ),
        ]

        self.education = [
            EducationData(
                degree_en="B.Sc. Computer Science",
                degree_ar="بكالوريوس علوم حاسب",
                institution_en="King Saud University",
                institution_ar="جامعة الملك سعود",
                year="2015",
                gpa="4.5/5.0",
            )
        ]

        self.skills_en = ["Python", "FastAPI", "React", "Docker", "AWS"]
        self.skills_ar = ["بايثون", "فاست أي بي آي", "ريأكت", "دوكر", "أمازون"]
        self.technical_skills_en = ["PostgreSQL", "Redis", "Kubernetes"]
        self.technical_skills_ar = ["بوستجري", "ريديس", "كوبرنتيس"]
        self.courses = ["Deep Learning Specialization", "Docker for Developers"]
        self.languages = [
            LanguageData(name="Arabic", level="Native"),
            LanguageData(name="English", level="Fluent"),
        ]

    def set_resume_data(self, data: dict):
        """Populate state from AI response dict."""
        personal = data.get("personal", {})
        self.name_en = personal.get("name_en", "") or personal.get("name", "")
        self.name_ar = personal.get("name_ar", "") or personal.get("name", "")
        self.email = personal.get("email", "")
        self.phone = personal.get("phone", "")
        self.location = personal.get("location", "")

        summary = data.get("summary", {})
        self.summary_en = summary.get("en", "") if isinstance(summary, dict) else str(summary)
        self.summary_ar = summary.get("ar", "") if isinstance(summary, dict) else ""

        self.experience = []
        for exp in data.get("experience", []):
            bullets_en = [BulletData(text=b) for b in (exp.get("bullets_en") or exp.get("bullets") or [])]
            bullets_ar = [BulletData(text=b) for b in (exp.get("bullets_ar") or [])]
            self.experience.append(ExperienceData(
                title_en=exp.get("title_en", "") or exp.get("title", ""),
                title_ar=exp.get("title_ar", "") or exp.get("title", ""),
                company_en=exp.get("company_en", "") or exp.get("company", ""),
                company_ar=exp.get("company_ar", "") or exp.get("company", ""),
                start_date=exp.get("start_date", ""),
                end_date=exp.get("end_date", ""),
                current=exp.get("current", False),
                bullets_en=bullets_en,
                bullets_ar=bullets_ar,
            ))

        self.education = []
        for edu in data.get("education", []):
            self.education.append(EducationData(
                degree_en=edu.get("degree_en", "") or edu.get("degree", ""),
                degree_ar=edu.get("degree_ar", "") or edu.get("degree", ""),
                institution_en=edu.get("institution_en", "") or edu.get("institution", ""),
                institution_ar=edu.get("institution_ar", "") or edu.get("institution", ""),
                year=edu.get("year", "") or edu.get("end_date", ""),
                gpa=edu.get("gpa", ""),
            ))

        self.skills_en = data.get("skills_en", []) or data.get("skills", [])
        self.skills_ar = data.get("skills_ar", []) or data.get("soft_skills", [])
        self.technical_skills_en = data.get("technical_skills_en", []) or data.get("technical_skills", [])
        self.technical_skills_ar = data.get("technical_skills_ar", []) or []
        self.courses = data.get("courses", [])
        self.languages = [LanguageData(name=l.get("name", ""), level=l.get("level", "")) for l in data.get("languages", [])]

    def increase_font_size(self):
        if self.font_size < 14.0:
            self.font_size = round(self.font_size + 0.3, 2)

    def decrease_font_size(self):
        if self.font_size > 5.0:
            self.font_size = round(self.font_size - 0.3, 2)

    def increase_margin(self):
        if self.margin < 25.0:
            self.margin = round(self.margin + 0.5, 2)

    def decrease_margin(self):
        if self.margin > 1.0:
            self.margin = round(self.margin - 0.5, 2)

    def set_template(self, template_id: str):
        self.template_id = template_id

    def reset_controls(self):
        self.font_size = 9.0
        self.line_height = 1.4
        self.section_spacing = 6
        self.column_distance = 16
        self.margin = 10.0
