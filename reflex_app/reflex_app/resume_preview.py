"""CVGen Pro — Reflex Resume Preview Component

Fixed UI styling:
- Two equal columns (48% each) with rx.flex + justify="space_between"
- Centered header with rx.vstack + align_items="center"
- A4 canvas: white bg, box_shadow, max_width=800px, padding=2em
- Section dividers: border_bottom 1.5px solid #000
- Blue contact links: #1a5276, text_decoration="none"
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
# Sub-components
# ---------------------------------------------------------------------------

def bullet_item(bullet: BulletData) -> rx.Component:
    return rx.list_item(
        bullet.text,
        font_size="9pt",
        color="#000",
        margin_bottom="2px",
    )


def experience_item(exp: ExperienceData) -> rx.Component:
    return rx.box(
        rx.text(
            exp.title_en,
            font_weight="bold",
            font_size="10pt",
            as_="span",
        ),
        rx.text(
            f" — {exp.company_en} ({exp.start_date} - {exp.end_date})",
            font_size="9pt",
            color="#555",
            as_="span",
        ),
        rx.unordered_list(
            rx.foreach(exp.bullets_en, bullet_item),
            padding_left="15px",
            margin_top="2px",
            list_style_type="disc",
        ),
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
        rx.unordered_list(
            rx.foreach(exp.bullets_ar, bullet_item),
            padding_right="15px",
            padding_left="0",
            margin_top="2px",
            list_style_type="disc",
            dir="rtl",
        ),
        margin_bottom="10px",
    )


def education_item(edu: EducationData) -> rx.Component:
    return rx.box(
        rx.text(edu.degree_en, font_weight="bold", font_size="10pt"),
        rx.text(edu.institution_en, font_size="9pt", color="#555"),
        rx.cond(
            edu.year != "",
            rx.text(edu.year, font_size="8pt", color="#555"),
        ),
        margin_bottom="8px",
    )


def skill_item(skill: str) -> rx.Component:
    return rx.list_item(skill, font_size="9pt", margin_bottom="2px")


def language_item(lang: LanguageData) -> rx.Component:
    return rx.list_item(
        lang.name,
        rx.cond(
            lang.level != "",
            rx.text(f" ({lang.level})", font_size="9pt", color="#555", as_="span"),
        ),
        font_size="9pt",
        margin_bottom="2px",
    )


def section(title: str, content: rx.Component) -> rx.Component:
    return rx.box(
        rx.heading(
            title,
            size="5",
            font_size="11pt",
            font_weight="bold",
            color="#2c3e50",
            padding_bottom="5px",
            margin_bottom="10px",
            border_bottom="1.5px solid #000",
        ),
        content,
        margin_bottom="8px",
    )


# ---------------------------------------------------------------------------
# Header (centered with rx.vstack)
# ---------------------------------------------------------------------------

def resume_header() -> rx.Component:
    return rx.vstack(
        # Names row
        rx.flex(
            rx.heading(
                ResumeState.name_en,
                size="6",
                font_size="2em",
                font_weight="bold",
                color="#2c3e50",
                as_="h1",
            ),
            rx.heading(
                ResumeState.name_ar,
                size="6",
                font_size="2em",
                font_weight="bold",
                color="#2c3e50",
                as_="h1",
                dir="rtl",
            ),
            width="100%",
            justify="between",
            align_items="center",
            direction="row",
        ),
        # Contact bar
        rx.hstack(
            rx.cond(
                ResumeState.email != "",
                rx.link(
                    f"✉️ {ResumeState.email}",
                    href=f"mailto:{ResumeState.email}",
                    color="#1a5276",
                    text_decoration="none",
                    font_size="9pt",
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
                ),
            ),
            rx.cond(
                ResumeState.location != "",
                rx.text(
                    f"📍 {ResumeState.location}",
                    font_size="9pt",
                    color="#555",
                ),
            ),
            spacing="4",
            justify="center",
            align_items="center",
        ),
        align_items="center",
        width="100%",
        padding="10px 0 10px 0",
        border_bottom="2px solid #2c3e50",
        margin_bottom="15px",
        background_color="#f8f9fa",
    )


# ---------------------------------------------------------------------------
# English Column (left, 48%)
# ---------------------------------------------------------------------------

def english_column() -> rx.Component:
    return rx.box(
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
                padding_left="15px", list_style_type="disc",
            )),
        ),
        rx.cond(
            ResumeState.has_skills_en,
            section("SKILLS", rx.unordered_list(
                rx.foreach(ResumeState.skills_en, skill_item),
                padding_left="15px", list_style_type="disc",
            )),
        ),
        rx.cond(
            ResumeState.technical_skills_en.length() > 0,
            section("TECHNICAL SKILLS", rx.unordered_list(
                rx.foreach(ResumeState.technical_skills_en, skill_item),
                padding_left="15px", list_style_type="disc",
            )),
        ),
        rx.cond(
            ResumeState.languages.length() > 0,
            section("LANGUAGES", rx.unordered_list(
                rx.foreach(ResumeState.languages, language_item),
                padding_left="15px", list_style_type="disc",
            )),
        ),
        width="48%",
        text_align="left",
        padding="0 8px",
    )


# ---------------------------------------------------------------------------
# Arabic Column (right, 48%)
# ---------------------------------------------------------------------------

def arabic_column() -> rx.Component:
    return rx.box(
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
                padding_right="15px", padding_left="0", list_style_type="disc", dir="rtl",
            )),
        ),
        rx.cond(
            ResumeState.has_skills_ar,
            section("المهارات", rx.unordered_list(
                rx.foreach(ResumeState.skills_ar, skill_item),
                padding_right="15px", padding_left="0", list_style_type="disc", dir="rtl",
            )),
            # Fallback: if skills_ar is empty, show soft_skills as Arabic skills
            rx.cond(
                ResumeState.soft_skills.length() > 0,
                section("المهارات", rx.unordered_list(
                    rx.foreach(ResumeState.soft_skills, skill_item),
                    padding_right="15px", padding_left="0", list_style_type="disc", dir="rtl",
                )),
            ),
        ),
        rx.cond(
            ResumeState.technical_skills_ar.length() > 0,
            section("المهارات التقنية", rx.unordered_list(
                rx.foreach(ResumeState.technical_skills_ar, skill_item),
                padding_right="15px", padding_left="0", list_style_type="disc", dir="rtl",
            )),
            # Fallback: show technical_skills (generic) if AR-specific is empty
            rx.cond(
                ResumeState.technical_skills_en.length() > 0,
                section("المهارات التقنية", rx.unordered_list(
                    rx.foreach(ResumeState.technical_skills_en, skill_item),
                    padding_right="15px", padding_left="0", list_style_type="disc", dir="rtl",
                )),
            ),
        ),
        rx.cond(
            ResumeState.languages.length() > 0,
            section("اللغات", rx.unordered_list(
                rx.foreach(ResumeState.languages, language_item),
                padding_right="15px", padding_left="0", list_style_type="disc", dir="rtl",
            )),
        ),
        width="48%",
        text_align="right",
        padding="0 8px",
    )


# ---------------------------------------------------------------------------
# Main Resume Preview (A4 Canvas)
# ---------------------------------------------------------------------------

def resume_preview_bilingual() -> rx.Component:
    """A4 resume preview with fixed column widths and centered header."""
    return rx.center(
        rx.box(
            # Header (centered)
            resume_header(),
            # Two equal columns (48% each, space_between)
            rx.flex(
                english_column(),
                rx.box(
                    width="1px",
                    background_color="#ccc",
                    flex_shrink="0",
                ),
                arabic_column(),
                width="100%",
                justify="between",
                direction="row",
                padding="0 10px 20px 10px",
            ),
            # A4 canvas styling
            background_color="white",
            color="black",
            box_shadow="lg",
            padding="2em",
            margin_x="auto",
            max_width="800px",
            width="100%",
            min_height="1100px",
            display="flex",
            flex_direction="column",
        ),
        width="100%",
        padding="20px",
        background_color="#2a2a2a",
    )
