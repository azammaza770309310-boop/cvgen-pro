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

    # ===== Raw text input (for AI parsing) =====
    raw_text: str = ""

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

    # ===== Advanced Controls Toggle (mobile UX) =====
    # When False, the advanced control rows (font size, line height, margins,
    # colors, template options, formatting) are collapsed to save screen space.
    # The basic row (save, download PDF/Word, AI assistant, edit content) is
    # always visible.
    show_advanced_controls: bool = False

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

    @rx.var
    def body_font_size_px(self) -> str:
        """Global body font size as a CSS px string (e.g. '9.0px').

        Used by resume body text (summary, bullets, skill lists, etc.) so the
        user's font-size controls scale the body. The header (name, email,
        phone, location) is NOT bound to this — it stays at fixed 24px / 12px.
        """
        return f"{self.font_size}px"

    @rx.var
    def body_font_size_small_px(self) -> str:
        """Slightly smaller body font (for secondary text like dates, levels).

        Scales with the global font_size control. Used for experience company
        lines, education year, language level, etc.
        """
        return f"{max(self.font_size - 1.0, 5.0):.1f}px"

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

    def toggle_advanced_controls(self):
        """Toggle the visibility of the advanced control rows.

        When collapsed (False), only the basic toolbar (save, download,
        AI, edit) is visible — saves screen space on mobile. When expanded
        (True), the font size, line height, margin, reset, and template
        controls are also visible.
        """
        self.show_advanced_controls = not self.show_advanced_controls

    # ------------------------------------------------------------------
    # AI Parsing + PDF/DOCX Export — NATIVE (no FastAPI, no httpx)
    # ------------------------------------------------------------------
    # The Reflex state calls the AI + export modules directly (in-process).
    # app.ai.* and app.services.* are FastAPI-independent — they use httpx
    # for outbound AI calls and WeasyPrint/python-docx for file generation.
    # No second server, no inter-process communication, no port conflicts.
    # Single Source of Truth: the logic lives in app/ and is shared.

    def _build_resume_data_dict(self) -> dict:
        """Build a resume data dict from the current state (for export)."""
        return {
            "personal": {
                "name_en": self.name_en,
                "name_ar": self.name_ar,
                "email": self.email,
                "phone": self.phone,
                "location": self.location,
            },
            "summary": {"en": self.summary_en, "ar": self.summary_ar},
            "experience": [e.model_dump() for e in self.experience],
            "education": [e.model_dump() for e in self.education],
            "skills_en": self.skills_en,
            "skills_ar": self.skills_ar,
            "technical_skills_en": self.technical_skills_en,
            "technical_skills_ar": self.technical_skills_ar,
            "courses": self.courses,
            "languages": [l.model_dump() for l in self.languages],
        }

    def _build_controls_dict(self) -> dict:
        """Build the design controls dict from the current state."""
        return {
            "fontSize": self.font_size,
            "lineHeight": self.line_height,
            "sectionSpacing": float(self.section_spacing),
            "columnDistance": float(self.column_distance),
            "margin": self.margin,
        }

    async def parse_resume_ai(self, raw_text: str = "", provider: str = "", lang: str = "auto"):
        """Parse raw resume text using the cloud AI (Gemini).

        Calls app.services.resume_parser.parse_resume_ai() directly
        (in-process async). Updates the Reflex state with the parsed data.
        """
        from reflex_app.reflex_app.ai_handler import parse_resume

        text = raw_text or self.raw_text or ""
        if not text.strip():
            return rx.toast.error("No text provided")

        self.is_generating = True
        result = await parse_resume(text, provider=provider, lang=lang)
        self.is_generating = False

        if not result.get("success"):
            return rx.toast.error(result.get("error", "AI parse failed"))

        self.set_resume_data(result["data"])
        return rx.toast.success("Resume parsed successfully")

    async def export_pdf(self):
        """Generate a PDF natively (WeasyPrint) and trigger download.

        Calls app.services.pdf_service.export_pdf() directly in-process.
        Sends design controls so the PDF matches the preview exactly.
        """
        from reflex_app.reflex_app.export_handler import export_pdf as _export_pdf, to_data_url

        try:
            data = self._build_resume_data_dict()
            controls = self._build_controls_dict()
            pdf_bytes = _export_pdf(data, self.template_id, controls)
            filename = (self.name_en or self.name_ar or "resume").replace(" ", "_") + ".pdf"
            dl = to_data_url(pdf_bytes, filename)
            return rx.download(data=dl["data"], filename=dl["filename"])
        except Exception as e:
            return rx.toast.error(f"PDF export error: {e}")

    async def export_docx(self):
        """Generate a DOCX natively (python-docx) and trigger download."""
        from reflex_app.reflex_app.export_handler import export_docx as _export_docx, to_data_url

        try:
            data = self._build_resume_data_dict()
            docx_bytes = _export_docx(data, self.template_id)
            filename = (self.name_en or self.name_ar or "resume").replace(" ", "_") + ".docx"
            dl = to_data_url(docx_bytes, filename)
            return rx.download(data=dl["data"], filename=dl["filename"])
        except Exception as e:
            return rx.toast.error(f"DOCX export error: {e}")
