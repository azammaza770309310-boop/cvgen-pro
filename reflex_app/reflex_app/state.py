"""CVGen Pro — Reflex State Management

Uses typed dataclasses instead of Dict for nested data,
so Reflex can properly infer types for rx.foreach.
"""
from __future__ import annotations

from pydantic import BaseModel

import reflex as rx
from typing import Any, List


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
    templates_list: list[dict] = []
    template_categories: list[dict] = []

    # ===== Settings / API Key Management =====
    settings: dict[str, Any] = {}
    key_links: dict[str, Any] = {}
    providers_list: list[dict[str, Any]] = []  # Extracted for rx.foreach

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
    show_advanced_controls: bool = False

    # ===== UI Panel Toggles =====
    show_input: bool = False        # Raw text input area
    show_settings: bool = False     # API key settings panel
    show_templates: bool = False    # Template selector panel
    show_api_keys: bool = False     # API keys management panel

    # ===== API Key Input Fields =====
    new_key_provider: str = "gemini"
    new_key_value: str = ""
    test_key_value: str = ""
    test_key_result: str = ""

    # ===== Undo/Redo History (per-session, NOT class-level mutable) =====
    # In Reflex, each session gets its own State instance, so instance attributes
    # are per-user. But class-level mutable defaults (list = []) are SHARED.
    # We use None defaults and initialize in __init__ to guarantee per-session.
    _history: list = None
    _history_index: int = -1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize per-session history — NEVER shared across users
        if self._history is None:
            self._history = []

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

    @rx.var
    def preview_html(self) -> str:
        """The HTML for the resume preview — SINGLE SOURCE OF TRUTH.

        This computed var calls app.templates_render.render_official_bilingual_master()
        (via export_handler.render_template_html) to produce the EXACT SAME HTML
        that the PDF export uses. The Reflex preview renders this via rx.html(),
        guaranteeing preview = PDF (same HTML + same CSS source).

        No separate rendering code path — one renderer, one CSS file, one result.
        """
        from reflex_app.reflex_app.export_handler import render_template_html
        try:
            data = self._build_resume_data_dict()
            return render_template_html(data, self.template_id)
        except Exception:
            # Log the full error server-side; show a generic message to the user
            # (no exception details leaked to the frontend — security).
            import logging
            logging.getLogger("cvgen.reflex").exception("preview_html error")
            return '<div style="color:red;padding:20px;">Preview error. Please check your data and try again.</div>'

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
        self._save_to_history()

    def set_resume_data(self, data: dict = None):
        """Populate state from AI response dict."""
        if data is None:
            data = {}
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
            # Handle both string bullets and dict bullets (from model_dump)
            raw_bullets_en = exp.get("bullets_en") or exp.get("bullets") or []
            raw_bullets_ar = exp.get("bullets_ar") or []
            bullets_en = [BulletData(text=b if isinstance(b, str) else b.get("text", "")) for b in raw_bullets_en]
            bullets_ar = [BulletData(text=b if isinstance(b, str) else b.get("text", "")) for b in raw_bullets_ar]
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
        if data.get("template_id"):
            self.template_id = data["template_id"]
        self._save_to_history()

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

    def set_template(self, template_id: str = ""):
        """Set the active template. Accepts a string arg (via lambda closure)."""
        if template_id:
            self.template_id = template_id
            self._save_to_history()

    def reset_controls(self):
        self.font_size = 9.0
        self.line_height = 1.4
        self.section_spacing = 6
        self.column_distance = 16
        self.margin = 10.0

    def toggle_advanced_controls(self):
        """Toggle the visibility of the advanced control rows."""
        self.show_advanced_controls = not self.show_advanced_controls

    def toggle_input(self):
        """Toggle the raw text input area."""
        self.show_input = not self.show_input

    def toggle_settings(self):
        """Toggle the settings panel."""
        if not self.show_settings:
            self.load_settings()
        self.show_settings = not self.show_settings

    def toggle_templates(self):
        """Toggle the template selector panel."""
        if not self.show_templates:
            self.load_templates_list()
        self.show_templates = not self.show_templates

    def toggle_api_keys(self):
        """Toggle the API keys management panel."""
        if not self.show_api_keys:
            self.load_settings()
        self.show_api_keys = not self.show_api_keys

    def set_new_key_provider(self, provider: str = ""):
        """Set the provider for the new key being added."""
        self.new_key_provider = provider

    def set_new_key_value(self, value: str = ""):
        """Set the value of the new key being added."""
        self.new_key_value = value

    def set_test_key_value(self, value: str = ""):
        """Set the value of the key being tested."""
        self.test_key_value = value

    def add_new_api_key(self):
        """Add the API key from the input fields."""
        if not self.new_key_provider or not self.new_key_value.strip():
            return rx.toast.error("اختر مزود وأدخل المفتاح")
        from reflex_app.reflex_app.settings_handler import add_api_key as _add
        result = _add(self.new_key_provider, self.new_key_value.strip())
        if result.get("success"):
            self.new_key_value = ""  # clear input
            self.load_settings()  # refresh
            return rx.toast.success(result.get("message", "تمت إضافة المفتاح"))
        return rx.toast.error(result.get("error", "فشل الإضافة"))

    def remove_api_key(self, provider: str = "", index: int = 0):
        """Delete an API key by provider and index."""
        from reflex_app.reflex_app.settings_handler import delete_api_key as _del
        result = _del(provider, index)
        if result.get("success"):
            self.load_settings()
            return rx.toast.success(result.get("message", "تم حذف المفتاح"))
        return rx.toast.error(result.get("error", "فشل الحذف"))

    async def run_test_gemini_key(self):
        """Test the Gemini key from the input field."""
        if not self.test_key_value.strip():
            return rx.toast.error("أدخل المفتاح أولاً")
        from reflex_app.reflex_app.settings_handler import test_gemini_key as _test
        result = await _test(self.test_key_value.strip())
        if result.get("success"):
            self.test_key_result = f"✅ {result.get('message', 'نجح الاتصال')}"
            return rx.toast.success(result.get("message", "نجح الاختبار"))
        else:
            error_type = result.get("error_type", "unknown")
            if error_type == "invalid_key":
                self.test_key_result = "❌ المفتاح غير صالح"
            elif error_type == "quota_exceeded":
                self.test_key_result = "⚠️ المفتاح صحيح لكن انتهت الحصة"
            elif error_type == "network_error":
                self.test_key_result = "❌ خطأ في الشبكة"
            else:
                self.test_key_result = f"❌ {result.get('error', 'فشل')[:80]}"
            return rx.toast.error(self.test_key_result)

    def set_raw_text(self, text: str = ""):
        """Set the raw resume text for AI parsing.

        Called by rx.text_area on_change. In Reflex 0.9.7, on_change passes
        the text value directly (not an event object).
        """
        self.raw_text = text

    def undo(self):
        """Undo the last state change."""
        if self._history_index > 0:
            self._history_index -= 1
            self._restore_from_history()

    def redo(self):
        """Redo the next state change."""
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            self._restore_from_history()

    def _save_to_history(self):
        """Save current resume data to history for undo/redo."""
        snapshot = self._build_resume_data_dict()
        # Truncate any forward history (we're at a new branch)
        self._history = self._history[:self._history_index + 1]
        self._history.append(snapshot)
        self._history_index = len(self._history) - 1
        # Cap history at 50 entries to prevent memory bloat
        if len(self._history) > 50:
            self._history = self._history[-50:]
            self._history_index = len(self._history) - 1

    def _restore_from_history(self):
        """Restore resume data from history snapshot.

        Does NOT call _save_to_history (that would create duplicate entries).
        Only restores the data fields + template_id from the snapshot.
        """
        if 0 <= self._history_index < len(self._history):
            data = self._history[self._history_index]
            # Restore fields directly without calling set_resume_data
            # (which would call _save_to_history and corrupt the history)
            personal = data.get("personal", {})
            self.name_en = personal.get("name_en", "")
            self.name_ar = personal.get("name_ar", "")
            self.email = personal.get("email", "")
            self.phone = personal.get("phone", "")
            self.location = personal.get("location", "")
            summary = data.get("summary", {})
            self.summary_en = summary.get("en", "") if isinstance(summary, dict) else ""
            self.summary_ar = summary.get("ar", "") if isinstance(summary, dict) else ""
            
            # Restore experience
            self.experience = []
            for exp in data.get("experience", []):
                raw_bullets_en = exp.get("bullets_en") or exp.get("bullets") or []
                raw_bullets_ar = exp.get("bullets_ar") or []
                bullets_en = [BulletData(text=b if isinstance(b, str) else b.get("text", "")) for b in raw_bullets_en]
                bullets_ar = [BulletData(text=b if isinstance(b, str) else b.get("text", "")) for b in raw_bullets_ar]
                self.experience.append(ExperienceData(
                    title_en=exp.get("title_en", ""),
                    title_ar=exp.get("title_ar", ""),
                    company_en=exp.get("company_en", ""),
                    company_ar=exp.get("company_ar", ""),
                    start_date=exp.get("start_date", ""),
                    end_date=exp.get("end_date", ""),
                    current=exp.get("current", False),
                    bullets_en=bullets_en,
                    bullets_ar=bullets_ar,
                ))
            
            # Restore education
            self.education = []
            for edu in data.get("education", []):
                self.education.append(EducationData(
                    degree_en=edu.get("degree_en", ""),
                    degree_ar=edu.get("degree_ar", ""),
                    institution_en=edu.get("institution_en", ""),
                    institution_ar=edu.get("institution_ar", ""),
                    year=edu.get("year", ""),
                    gpa=edu.get("gpa", ""),
                ))
            
            self.skills_en = data.get("skills_en", [])
            self.skills_ar = data.get("skills_ar", [])
            self.technical_skills_en = data.get("technical_skills_en", [])
            self.technical_skills_ar = data.get("technical_skills_ar", [])
            self.courses = data.get("courses", [])
            self.languages = [LanguageData(name=l.get("name", ""), level=l.get("level", "")) for l in data.get("languages", [])]
            if data.get("template_id"):
                self.template_id = data["template_id"]

    # ------------------------------------------------------------------
    # AI Parsing + PDF/DOCX Export — NATIVE (no FastAPI, no httpx)
    # ------------------------------------------------------------------
    # The Reflex state calls the AI + export modules directly (in-process).
    # app.ai.* and app.services.* are FastAPI-independent — they use httpx
    # for outbound AI calls and WeasyPrint/python-docx for file generation.
    # No second server, no inter-process communication, no port conflicts.
    # Single Source of Truth: the logic lives in app/ and is shared.

    def _build_resume_data_dict(self) -> dict:
        """Build a resume data dict from the current state (for export).

        CRITICAL: ExperienceData.bullets_en is List[BulletData] where BulletData
        has a 'text' field. When serialized with model_dump(), bullets become
        [{"text": "..."}]. But the normalizer expects bullets as List[str].
        We must convert BulletData objects to plain strings here.
        """
        return {
            "personal": {
                "name_en": self.name_en,
                "name_ar": self.name_ar,
                "email": self.email,
                "phone": self.phone,
                "location": self.location,
            },
            "summary": {"en": self.summary_en, "ar": self.summary_ar},
            "experience": [{
                "title_en": e.title_en,
                "title_ar": e.title_ar,
                "company_en": e.company_en,
                "company_ar": e.company_ar,
                "start_date": e.start_date,
                "end_date": e.end_date,
                "current": e.current,
                "bullets_en": [b.text for b in e.bullets_en],
                "bullets_ar": [b.text for b in e.bullets_ar],
            } for e in self.experience],
            "education": [{
                "degree_en": e.degree_en,
                "degree_ar": e.degree_ar,
                "institution_en": e.institution_en,
                "institution_ar": e.institution_ar,
                "year": e.year,
                "gpa": e.gpa,
            } for e in self.education],
            "skills_en": self.skills_en,
            "skills_ar": self.skills_ar,
            "technical_skills_en": self.technical_skills_en,
            "technical_skills_ar": self.technical_skills_ar,
            "courses": self.courses,
            "languages": [{"name": l.name, "level": l.level} for l in self.languages],
            "template_id": self.template_id,
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

    @staticmethod
    def _safe_filename(name: str) -> str:
        """Sanitize a string for use as a filename.

        Removes path separators, null bytes, and other dangerous characters.
        Prevents path traversal via crafted resume names.
        """
        import re
        # Keep only alphanumeric, underscore, hyphen, and space
        safe = re.sub(r'[^\w\s\-]', '', name or "resume").strip().replace(" ", "_")
        return safe or "resume"

    async def parse_resume_ai(self):
        """Parse raw resume text using the cloud AI (Gemini).

        Reads raw_text from state (set by the text_area). Calls
        app.services.resume_parser.parse_resume_ai() directly (in-process).
        """
        from reflex_app.reflex_app.ai_handler import parse_resume

        text = self.raw_text or ""
        if not text.strip():
            return rx.toast.error("No text provided")

        self.is_generating = True
        result = await parse_resume(text)
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
            filename = self._safe_filename(self.name_en or self.name_ar or "resume") + ".pdf"
            dl = to_data_url(pdf_bytes, filename)
            return rx.download(data=dl["data"], filename=dl["filename"])
        except Exception:
            import logging
            logging.getLogger("cvgen.reflex").exception("PDF export error")
            return rx.toast.error("PDF export failed. Please try again.")

    async def export_docx(self):
        """Generate a DOCX natively (python-docx) and trigger download."""
        from reflex_app.reflex_app.export_handler import export_docx as _export_docx, to_data_url

        try:
            data = self._build_resume_data_dict()
            docx_bytes = _export_docx(data, self.template_id)
            filename = self._safe_filename(self.name_en or self.name_ar or "resume") + ".docx"
            dl = to_data_url(docx_bytes, filename)
            return rx.download(data=dl["data"], filename=dl["filename"])
        except Exception:
            import logging
            logging.getLogger("cvgen.reflex").exception("DOCX export error")
            return rx.toast.error("DOCX export failed. Please try again.")

    # ------------------------------------------------------------------
    # Page count (native — renders PDF + counts via pypdf)
    # ------------------------------------------------------------------
    def get_page_count(self) -> int:
        """Return the TRUE page count by rendering the PDF.

        Calls export_handler.get_page_count() directly (in-process).
        """
        from reflex_app.reflex_app.export_handler import get_page_count as _gpc
        try:
            data = self._build_resume_data_dict()
            controls = self._build_controls_dict()
            count = _gpc(data, self.template_id, controls)
            self.page_count = count
            return count
        except Exception as e:
            return self.page_count  # keep previous value on error

    # ------------------------------------------------------------------
    # AI: improve, summary, cover-letter (native)
    # ------------------------------------------------------------------
    async def improve_section(self, section: str = "", content: str = "", lang: str = "en"):
        """Improve a section of text via AI."""
        from reflex_app.reflex_app.ai_handler import improve_section as _improve
        result = await _improve(section, content, lang=lang)
        if not result.get("success"):
            return rx.toast.error(result.get("error", "Improve failed"))
        return result.get("content", "")

    async def generate_summary(self, role: str = "", experience_years: int = 0, skills: list = None, lang: str = "en"):
        """Generate a professional resume summary via AI."""
        from reflex_app.reflex_app.ai_handler import generate_summary as _summary
        result = await _summary(role or "", experience_years or 0, skills or [], lang=lang)
        if not result.get("success"):
            return rx.toast.error(result.get("error", "Summary generation failed"))
        return result.get("summary", "")

    async def generate_cover_letter(self, job_description: str = ""):
        """Generate a cover letter via AI."""
        from reflex_app.reflex_app.ai_handler import generate_cover_letter as _cl
        data = self._build_resume_data_dict()
        result = await _cl(data, job_description)
        if not result.get("success"):
            return rx.toast.error(result.get("error", "Cover letter generation failed"))
        return result.get("content", "")

    # ------------------------------------------------------------------
    # ATS analysis (native — rule-based + optional AI)
    # ------------------------------------------------------------------
    async def analyze_ats(self, job_description: str = "", use_ai: bool = False):
        """Analyze the resume for ATS compatibility.

        Returns the ATS analysis result (score, grade, recommendations).
        """
        from reflex_app.reflex_app.ai_handler import analyze_ats as _ats
        data = self._build_resume_data_dict()
        result = await _ats(data, job_description, use_ai=use_ai)
        if not result.get("success"):
            return rx.toast.error(result.get("error", "ATS analysis failed"))
        return result.get("data")

    # ------------------------------------------------------------------
    # Templates (native — delegates to template_service)
    # ------------------------------------------------------------------
    def load_templates_list(self):
        """Load the templates list + count + categories into state."""
        from reflex_app.reflex_app.export_handler import list_templates, get_template_count, list_categories
        self.templates_list = list_templates()
        self.template_count = get_template_count()
        self.template_categories = list_categories()

    def render_template(self) -> str:
        """Render the current resume as HTML (for preview)."""
        from reflex_app.reflex_app.export_handler import render_template_html
        data = self._build_resume_data_dict()
        return render_template_html(data, self.template_id)

    # ------------------------------------------------------------------
    # Sample resume (native — supports en/ar/bilingual)
    # ------------------------------------------------------------------
    def load_sample_by_lang(self, lang: str = "bilingual"):
        """Load a sample resume for the requested language."""
        from reflex_app.reflex_app.export_handler import get_sample_resume
        data = get_sample_resume(lang)
        self.set_resume_data(data)

    # ------------------------------------------------------------------
    # Normalize (native — cleans structured data)
    # ------------------------------------------------------------------
    def normalize_data(self):
        """Normalize the current resume data in-place."""
        from reflex_app.reflex_app.export_handler import normalize_resume
        data = self._build_resume_data_dict()
        normalized = normalize_resume(data)
        self.set_resume_data(normalized)  # set_resume_data calls _save_to_history

    # ------------------------------------------------------------------
    # Settings / API key management (native)
    # ------------------------------------------------------------------
    def load_settings(self):
        """Load all settings (providers, keys, links) into state."""
        from reflex_app.reflex_app.settings_handler import get_settings, get_key_links
        self.settings = get_settings()
        self.providers_list = self.settings.get("providers", [])
        self.key_links = get_key_links().get("links", {})

    def add_api_key(self, provider: str = "", key: str = ""):
        """Add an API key for a provider."""
        from reflex_app.reflex_app.settings_handler import add_api_key as _add
        result = _add(provider, key)
        if result.get("success"):
            self.load_settings()  # refresh
            return rx.toast.success(result.get("message", "Key added"))
        return rx.toast.error(result.get("error", "Failed to add key"))

    def delete_api_key(self, provider: str = "", index: int = 0):
        """Delete a file-stored API key by index."""
        from reflex_app.reflex_app.settings_handler import delete_api_key as _del
        result = _del(provider, index)
        if result.get("success"):
            self.load_settings()  # refresh
            return rx.toast.success(result.get("message", "Key deleted"))
        return rx.toast.error(result.get("error", "Failed to delete key"))

    async def test_gemini_key(self, key: str = ""):
        """Test a Gemini API key with a real request to Google."""
        from reflex_app.reflex_app.settings_handler import test_gemini_key as _test
        result = await _test(key)
        if result.get("success"):
            return result  # caller shows success message
        return result  # caller shows error based on error_type

    def test_provider_configured(self, provider: str = "") -> bool:
        """Check if a provider is configured."""
        from reflex_app.reflex_app.settings_handler import test_provider_configured as _test
        return _test(provider).get("configured", False)
