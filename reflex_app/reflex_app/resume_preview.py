"""CVGen Pro — Reflex Resume Preview Component

Uses typed rx.Base models (ExperienceData, EducationData, etc.)
so rx.foreach can properly infer types and generate React code.

Key: rx.foreach over List[ExperienceData] (NOT List[Dict])
and nested rx.foreach over List[BulletData] inside each experience.
"""
from __future__ import annotations

import reflex as rx
from reflex_app.reflex_app.state import (
    ResumeState,
    ExperienceData,
    EducationData,
    LanguageData,
    BulletData,
)


# ---------------------------------------------------------------------------
# Sub-components (rendered via rx.foreach)
# ---------------------------------------------------------------------------

def bullet_item(bullet: BulletData) -> rx.Component:
    """Render a single bullet point."""
    return rx.list_item(
        bullet.text,
        font_size="9pt",
        color="#000",
        margin_bottom="0.5mm",
    )


def experience_item(exp: ExperienceData) -> rx.Component:
    """Render a single experience entry with NESTED rx.foreach for bullets.

    CRITICAL: exp is typed as ExperienceData (rx.Base), NOT Dict.
    exp.bullets_en is List[BulletData] — Reflex can infer the type.
    """
    return rx.box(
        # English header
        rx.text(
            exp.title_en,
            font_weight="bold",
            font_size="10pt",
            as_="span",
        ),
        rx.text(
            f" — {exp.company_en} ({exp.start_date} – {exp.end_date})",
            font_size="9pt",
            color="#555",
            as_="span",
        ),
        # English bullets — NESTED rx.foreach over List[BulletData]
        rx.unordered_list(
            rx.foreach(exp.bullets_en, bullet_item),
            padding_left="4mm",
            margin_top="1mm",
            list_style_type="disc",
        ),
        # Arabic header
        rx.text(
            exp.title_ar,
            font_weight="bold",
            font_size="10pt",
            as_="span",
            dir="rtl",
        ),
        rx.text(
            f" — {exp.company_ar}",
            font_size="9pt",
            color="#555",
            as_="span",
            dir="rtl",
        ),
        # Arabic bullets — NESTED rx.foreach
        rx.unordered_list(
            rx.foreach(exp.bullets_ar, bullet_item),
            padding_right="4mm",
            padding_left="0",
            margin_top="1mm",
            list_style_type="disc",
            dir="rtl",
        ),
        margin_bottom="4mm",
    )


def education_item(edu: EducationData) -> rx.Component:
    """Render a single education entry."""
    return rx.box(
        rx.text(edu.degree_en, font_weight="bold", font_size="10pt"),
        rx.text(edu.institution_en, font_size="9pt", color="#555", font_style="italic"),
        rx.cond(
            edu.year != "",
            rx.text(edu.year, font_size="8pt", color="#555"),
        ),
        margin_bottom="3mm",
    )


def skill_item(skill: str) -> rx.Component:
    """Render a single skill (string, not object)."""
    return rx.list_item(skill, font_size="9pt", margin_bottom="0.5mm")


def language_item(lang: LanguageData) -> rx.Component:
    """Render a single language entry."""
    return rx.list_item(
        lang.name,
        rx.cond(
            lang.level != "",
            rx.text(f" – {lang.level}", font_size="9pt", color="#555", as_="span"),
        ),
        font_size="9pt",
        margin_bottom="0.5mm",
    )


# ---------------------------------------------------------------------------
# Section helper
# ---------------------------------------------------------------------------

def section(title: str, content: rx.Component) -> rx.Component:
    """Render a section with title and divider."""
    return rx.box(
        rx.heading(
            title,
            size="5",
            font_size="11pt",
            font_weight="bold",
            color="#2c3e50",
            padding_bottom="5px",
            margin_bottom="12px",
            border_bottom="1.5px solid #000",
        ),
        content,
        margin_bottom="2mm",
    )


# ---------------------------------------------------------------------------
# Main Resume Preview (Bilingual Master)
# ---------------------------------------------------------------------------

def resume_preview_bilingual() -> rx.Component:
    """Full A4 bilingual resume preview using rx.foreach with typed models."""
    return rx.box(
        rx.box(
            # ===== HEADER =====
            rx.box(
                rx.box(
                    rx.heading(
                        ResumeState.name_en,
                        size="6",
                        font_size="18pt",
                        font_weight="900",
                        color="#2c3e50",
                        as_="h1",
                    ),
                    rx.heading(
                        ResumeState.name_ar,
                        size="6",
                        font_size="18pt",
                        font_weight="900",
                        color="#2c3e50",
                        as_="h1",
                        dir="rtl",
                    ),
                    display="flex",
                    justify_content="space-between",
                    margin_bottom="3mm",
                ),
                rx.box(
                    rx.cond(
                        ResumeState.email != "",
                        rx.link(
                            f"✉️ {ResumeState.email}",
                            href=f"mailto:{ResumeState.email}",
                            color="#1a5276",
                            text_decoration="none",
                            font_size="9pt",
                            as_="span",
                        ),
                    ),
                    rx.cond(
                        ResumeState.phone != "",
                        rx.link(
                            f"📞 {ResumeState.phone}",
                            href=f"tel:{ResumeState.phone}",
                            color="#1a5276",
                            text_decoration="none",
                            font_size="9pt",
                            as_="span",
                        ),
                    ),
                    rx.cond(
                        ResumeState.location != "",
                        rx.text(
                            f"📍 {ResumeState.location}",
                            font_size="9pt",
                            color="#555",
                            as_="span",
                        ),
                    ),
                    display="flex",
                    justify_content="center",
                    gap="8mm",
                    flex_wrap="wrap",
                ),
                padding="10mm 10mm 4mm 10mm",
                background_color="#f8f9fa",
                border_bottom="2px solid #2c3e50",
            ),

            # ===== TWO COLUMNS =====
            rx.box(
                # --- ENGLISH COLUMN ---
                rx.box(
                    rx.cond(
                        ResumeState.summary_en != "",
                        section("CAREER OBJECTIVE", rx.text(ResumeState.summary_en, font_size="9pt")),
                    ),
                    rx.cond(
                        ResumeState.has_education,
                        section("EDUCATION", rx.foreach(ResumeState.education, education_item)),
                    ),
                    rx.cond(
                        ResumeState.has_experience,
                        section("EXPERIENCE", rx.foreach(ResumeState.experience, experience_item)),
                    ),
                    rx.cond(
                        ResumeState.courses.length() > 0,
                        section("COURSES", rx.unordered_list(
                            rx.foreach(ResumeState.courses, skill_item),
                            padding_left="4mm", list_style_type="disc",
                        )),
                    ),
                    rx.cond(
                        ResumeState.has_skills_en,
                        section("SKILLS", rx.unordered_list(
                            rx.foreach(ResumeState.skills_en, skill_item),
                            padding_left="4mm", list_style_type="disc",
                        )),
                    ),
                    rx.cond(
                        ResumeState.technical_skills_en.length() > 0,
                        section("TECHNICAL SKILLS", rx.unordered_list(
                            rx.foreach(ResumeState.technical_skills_en, skill_item),
                            padding_left="4mm", list_style_type="disc",
                        )),
                    ),
                    rx.cond(
                        ResumeState.languages.length() > 0,
                        section("LANGUAGES", rx.unordered_list(
                            rx.foreach(ResumeState.languages, language_item),
                            padding_left="4mm", list_style_type="disc",
                        )),
                    ),
                    flex="1", text_align="left", dir="ltr",
                ),
                # Divider
                rx.box(width="1px", background_color="#d1d5db"),
                # --- ARABIC COLUMN ---
                rx.box(
                    rx.cond(
                        ResumeState.summary_ar != "",
                        section("الهدف الوظيفي", rx.text(ResumeState.summary_ar, font_size="9pt", dir="rtl")),
                    ),
                    rx.cond(
                        ResumeState.has_education,
                        section("التعليم", rx.foreach(ResumeState.education, education_item)),
                    ),
                    rx.cond(
                        ResumeState.has_experience,
                        section("الخبرات المهنية", rx.foreach(ResumeState.experience, experience_item)),
                    ),
                    rx.cond(
                        ResumeState.courses.length() > 0,
                        section("الدورات", rx.unordered_list(
                            rx.foreach(ResumeState.courses, skill_item),
                            padding_right="4mm", padding_left="0", list_style_type="disc", dir="rtl",
                        )),
                    ),
                    rx.cond(
                        ResumeState.has_skills_ar,
                        section("المهارات", rx.unordered_list(
                            rx.foreach(ResumeState.skills_ar, skill_item),
                            padding_right="4mm", padding_left="0", list_style_type="disc", dir="rtl",
                        )),
                    ),
                    rx.cond(
                        ResumeState.technical_skills_ar.length() > 0,
                        section("المهارات التقنية", rx.unordered_list(
                            rx.foreach(ResumeState.technical_skills_ar, skill_item),
                            padding_right="4mm", padding_left="0", list_style_type="disc", dir="rtl",
                        )),
                    ),
                    rx.cond(
                        ResumeState.languages.length() > 0,
                        section("اللغات", rx.unordered_list(
                            rx.foreach(ResumeState.languages, language_item),
                            padding_right="4mm", padding_left="0", list_style_type="disc", dir="rtl",
                        )),
                    ),
                    flex="1", text_align="right", dir="rtl",
                ),
                display="flex", direction="ltr", flex="1", padding="6mm 10mm", gap="6mm",
            ),
            width="210mm", min_height="297mm", background_color="white",
            display="flex", flex_direction="column", overflow="hidden", color="#333",
        ),
        display="flex", justify_content="center", padding="20px", background="#2a2a2a",
    )
