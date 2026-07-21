"""CVGen Pro — Reflex State Management

This module manages all application state for the Reflex SPA:
- Resume data (nested: personal, experience[], education[], skills[])
- Template selection
- AI provider config
- Editor controls (font size, margins, etc.)
- Preview state (page count, overflow)

Uses rx.Var for reactive state — when data changes, the UI updates automatically.
"""
from __future__ import annotations

import reflex as rx
from typing import List, Dict, Optional
from dataclasses import dataclass, field


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

    # ===== Nested Arrays (for rx.foreach) =====
    # Each experience is a dict with title_en, title_ar, company_en, company_ar,
    # start_date, end_date, bullets_en[], bullets_ar[]
    experience: List[Dict] = []
    education: List[Dict] = []
    skills_en: List[str] = []
    skills_ar: List[str] = []
    technical_skills_en: List[str] = []
    technical_skills_ar: List[str] = []
    courses: List[str] = []
    languages: List[Dict] = []

    # ===== Template Selection =====
    template_id: str = "official_bilingual_master"
    template_count: int = 3  # dynamic from registry

    # ===== Editor Controls =====
    font_size: float = 9.0
    line_height: float = 1.4
    section_spacing: int = 6
    column_distance: int = 16
    margin: float = 10.0

    # ===== Preview State =====
    page_count: int = 1
    current_page: int = 1
    overflow_warning: str = ""

    # ===== AI Provider =====
    ai_provider: str = ""
    ai_status: str = "جاري التحقق..."
    ai_configured: bool = False

    # ===== Loading States =====
    is_generating: bool = False
    is_exporting: bool = False

    # ===== Error State =====
    error_message: str = ""

    # ------------------------------------------------------------------
    # Computed properties (for rx.foreach rendering)
    # ------------------------------------------------------------------

    @rx.var
    def has_experience(self) -> bool:
        """Check if there are any experience entries."""
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
        """Display name based on available data."""
        return self.name_en or self.name_ar or "Untitled"

    @rx.var
    def contact_info(self) -> str:
        """Formatted contact info string."""
        parts = []
        if self.email:
            parts.append(self.email)
        if self.phone:
            parts.append(self.phone)
        if self.location:
            parts.append(self.location)
        return " | ".join(parts)

    @rx.var
    def is_overflow(self) -> bool:
        """Check if resume exceeds one page."""
        return self.page_count > 1

    # ------------------------------------------------------------------
    # Event Handlers
    # ------------------------------------------------------------------

    def set_resume_data(self, data: dict):
        """Populate all state fields from a structured resume dict (from AI)."""
        personal = data.get("personal", {})
        self.name_en = personal.get("name_en", "") or personal.get("name", "")
        self.name_ar = personal.get("name_ar", "") or personal.get("name", "")
        self.email = personal.get("email", "")
        self.phone = personal.get("phone", "")
        self.location = personal.get("location", "")
        self.linkedin = personal.get("linkedin", "")

        summary = data.get("summary", {})
        self.summary_en = summary.get("en", "") if isinstance(summary, dict) else str(summary)
        self.summary_ar = summary.get("ar", "") if isinstance(summary, dict) else ""

        # Experience: list of dicts
        self.experience = []
        for exp in data.get("experience", []):
            self.experience.append({
                "title_en": exp.get("title_en", "") or exp.get("title", ""),
                "title_ar": exp.get("title_ar", "") or exp.get("title", ""),
                "company_en": exp.get("company_en", "") or exp.get("company", ""),
                "company_ar": exp.get("company_ar", "") or exp.get("company", ""),
                "start_date": exp.get("start_date", ""),
                "end_date": exp.get("end_date", ""),
                "current": exp.get("current", False),
                "bullets_en": exp.get("bullets_en", []) or exp.get("bullets", []),
                "bullets_ar": exp.get("bullets_ar", []) or [],
            })

        # Education
        self.education = []
        for edu in data.get("education", []):
            self.education.append({
                "degree_en": edu.get("degree_en", "") or edu.get("degree", ""),
                "degree_ar": edu.get("degree_ar", "") or edu.get("degree", ""),
                "institution_en": edu.get("institution_en", "") or edu.get("institution", ""),
                "institution_ar": edu.get("institution_ar", "") or edu.get("institution", ""),
                "year": edu.get("year", "") or edu.get("end_date", ""),
                "gpa": edu.get("gpa", ""),
            })

        # Skills
        self.skills_en = data.get("skills_en", []) or data.get("skills", [])
        self.skills_ar = data.get("skills_ar", []) or data.get("soft_skills", [])
        self.technical_skills_en = data.get("technical_skills_en", []) or data.get("technical_skills", [])
        self.technical_skills_ar = data.get("technical_skills_ar", []) or []
        self.courses = data.get("courses", [])
        self.languages = data.get("languages", [])

    def load_sample(self):
        """Load sample bilingual resume data for testing."""
        self.set_resume_data({
            "personal": {
                "name_en": "Ahmed Abdullah",
                "name_ar": "أحمد عبدالله",
                "email": "ahmed@example.com",
                "phone": "+966500000000",
                "location": "Riyadh, Saudi Arabia",
                "linkedin": "linkedin.com/in/ahmed",
            },
            "summary": {
                "en": "Senior software engineer with 8+ years building scalable web platforms.",
                "ar": "مهندس برمجيات بخبرة 8 سنوات في تطوير تطبيقات الويب والسحابة.",
            },
            "experience": [
                {
                    "title_en": "Senior Software Engineer",
                    "title_ar": "مهندس برمجيات أول",
                    "company_en": "Tech Corp",
                    "company_ar": "شركة التقنية",
                    "start_date": "2020/01",
                    "end_date": "Present",
                    "current": True,
                    "bullets_en": ["Designed cloud platforms serving 1M+ users", "Led a team of 5 engineers"],
                    "bullets_ar": ["تصميم منصات سحابية تخدم مليون مستخدم", "قيادة فريق من 5 مطورين"],
                },
                {
                    "title_en": "Software Engineer",
                    "title_ar": "مهندس برمجيات",
                    "company_en": "Startup Inc",
                    "company_ar": "ستارت أب",
                    "start_date": "2015/06",
                    "end_date": "2019/12",
                    "current": False,
                    "bullets_en": ["Built REST APIs in Python", "Shipped 20+ features"],
                    "bullets_ar": ["بناء واجهات برمجية بلغة بايثون", "تطوير 20 ميزة"],
                },
            ],
            "education": [
                {
                    "degree_en": "B.Sc. Computer Science",
                    "degree_ar": "بكالوريوس علوم حاسب",
                    "institution_en": "King Saud University",
                    "institution_ar": "جامعة الملك سعود",
                    "year": "2015",
                    "gpa": "4.5/5.0",
                }
            ],
            "skills_en": ["Python", "FastAPI", "React", "Docker", "AWS"],
            "skills_ar": ["بايثون", "فاست أي بي آي", "ريأكت", "دوكر", "أمازون"],
            "technical_skills_en": ["PostgreSQL", "Redis", "Kubernetes"],
            "technical_skills_ar": ["بوستجري إس كيو إل", "ريديس", "كوبرنتيس"],
            "courses": ["Deep Learning Specialization", "Docker for Developers"],
            "languages": [
                {"name": "Arabic", "level": "Native"},
                {"name": "English", "level": "Fluent"},
            ],
        })

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
        """Reset all design controls to defaults."""
        self.font_size = 9.0
        self.line_height = 1.4
        self.section_spacing = 6
        self.column_distance = 16
        self.margin = 10.0
