"""CVGen Pro — Reflex Resume Preview Component

This component renders the A4 resume preview using rx.foreach for nested data.
It mirrors the exact layout of the HTML template but in pure Reflex/Python.

Key: rx.foreach is used for:
- experience[] → each job with bullets_en[] and bullets_ar[]
- education[] → each degree
- skills_en[] / skills_ar[] → each skill
- languages[] → each language
"""
from __future__ import annotations

import reflex as rx
from reflex_app.state import ResumeState


# ---------------------------------------------------------------------------
# Reusable sub-components (rendered via rx.foreach)
# ---------------------------------------------------------------------------

def bullet_item_en(bullet: str) -> rx.Component:
    """Render a single English bullet point."""
    return rx.list_item(
        bullet,
        class_name="editable",
        font_size="9pt",
        color="#000",
        margin_bottom="0.5mm",
    )


def bullet_item_ar(bullet: str) -> rx.Component:
    """Render a single Arabic bullet point."""
    return rx.list_item(
        bullet,
        class_name="editable",
        font_size="9pt",
        color="#000",
        margin_bottom="0.5mm",
        dir="rtl",
    )


def experience_item(exp: dict) -> rx.Component:
    """Render a single experience entry with nested bullets via rx.foreach.

    This is the critical test: nested rx.foreach inside rx.foreach.
    exp is a dict with title_en, company_en, bullets_en[], etc.
    """
    return rx.box(
        # English header
        rx.box(
            rx.text(
                exp["title_en"],
                font_weight="bold",
                font_size="10pt",
                as_="span",
            ),
            rx.text(
                " — ",
                font_size="10pt",
                as_="span",
                color="#555",
            ),
            rx.text(
                exp["company_en"],
                font_size="9pt",
                font_style="italic",
                color="#555",
                as_="span",
            ),
            rx.text(
                f" ({exp['start_date']} – {exp['end_date']})",
                font_size="8pt",
                color="#555",
                as_="span",
            ),
            display="flex",
            flex_wrap="wrap",
            margin_bottom="1mm",
        ),
        # English bullets — NESTED rx.foreach
        rx.unordered_list(
            rx.foreach(exp["bullets_en"], bullet_item_en),
            padding_left="4mm",
            margin_top="1mm",
            list_style_type="disc",
        ),
        # Arabic header
        rx.box(
            rx.text(
                exp["title_ar"],
                font_weight="bold",
                font_size="10pt",
                as_="span",
                dir="rtl",
            ),
            rx.text(
                f" — {exp['company_ar']}",
                font_size="9pt",
                font_style="italic",
                color="#555",
                as_="span",
                dir="rtl",
            ),
            display="flex",
            flex_direction="row-reverse",
            margin_bottom="1mm",
            dir="rtl",
        ),
        # Arabic bullets — NESTED rx.foreach
        rx.unordered_list(
            rx.foreach(exp["bullets_ar"], bullet_item_ar),
            padding_right="4mm",
            padding_left="0",
            margin_top="1mm",
            list_style_type="disc",
            dir="rtl",
        ),
        margin_bottom="4mm",
        class_name="list-item",
    )


def education_item(edu: dict) -> rx.Component:
    """Render a single education entry."""
    return rx.box(
        rx.text(
            edu["degree_en"],
            font_weight="bold",
            font_size="10pt",
        ),
        rx.text(
            edu["institution_en"],
            font_size="9pt",
            font_style="italic",
            color="#555",
        ),
        rx.cond(
            edu["year"] != "",
            rx.text(
                edu["year"],
                font_size="8pt",
                color="#555",
            ),
        ),
        margin_bottom="3mm",
    )


def skill_item(skill: str) -> rx.Component:
    """Render a single skill bullet."""
    return rx.list_item(
        skill,
        font_size="9pt",
        margin_bottom="0.5mm",
    )


def skill_item_ar(skill: str) -> rx.Component:
    """Render a single Arabic skill bullet."""
    return rx.list_item(
        skill,
        font_size="9pt",
        margin_bottom="0.5mm",
        dir="rtl",
    )


def language_item(lang: dict) -> rx.Component:
    """Render a single language entry."""
    return rx.list_item(
        rx.text(
            lang["name"],
            font_size="9pt",
            as_="span",
        ),
        rx.cond(
            lang["level"] != "",
            rx.text(
                f" – {lang['level']}",
                font_size="9pt",
                color="#555",
                as_="span",
            ),
        ),
        margin_bottom="0.5mm",
    )


# ---------------------------------------------------------------------------
# Section helper
# ---------------------------------------------------------------------------

def section(title: str, content: rx.Component) -> rx.Component:
    """Render a section with a title and divider."""
    return rx.box(
        rx.heading(
            title,
            size="sm",
            font_size="11pt",
            font_weight="bold",
            color="#2c3e50",
            padding_bottom="5px",
            margin_bottom="12px",
            border_bottom="1.5px solid #000",
            text_transform="uppercase",
        ),
        content,
        margin_bottom="2mm",
        class_name="section",
    )


# ---------------------------------------------------------------------------
# Main Resume Preview Component (Bilingual Master)
# ---------------------------------------------------------------------------

def resume_preview_bilingual() -> rx.Component:
    """Render the full bilingual A4 resume preview.

    Uses rx.foreach for all nested arrays:
    - experience[] → experience_item (which itself uses rx.foreach for bullets)
    - education[] → education_item
    - skills_en[] → skill_item
    - skills_ar[] → skill_item_ar
    - languages[] → language_item
    """
    return rx.box(
        # ===== A4 PAGE CONTAINER =====
        rx.box(
            # ===== HEADER =====
            rx.box(
                # Names row
                rx.box(
                    rx.heading(
                        ResumeState.name_en,
                        font_size="18pt",
                        font_weight="900",
                        color="#2c3e50",
                        text_transform="uppercase",
                        dir="ltr",
                        as_="h1",
                    ),
                    rx.heading(
                        ResumeState.name_ar,
                        font_size="18pt",
                        font_weight="900",
                        color="#2c3e50",
                        dir="rtl",
                        as_="h1",
                    ),
                    display="flex",
                    justify_content="space-between",
                    align_items="center",
                    direction="ltr",
                    margin_bottom="3mm",
                    class_name="header-names",
                ),
                # Contact bar with blue links
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
                    class_name="contact-bar",
                ),
                padding="10mm 10mm 4mm 10mm",
                background_color="#f8f9fa",
                border_bottom="2px solid #2c3e50",
                class_name="resume-header",
            ),

            # ===== TWO COLUMNS =====
            rx.box(
                # --- ENGLISH COLUMN ---
                rx.box(
                    # Career Objective
                    rx.cond(
                        ResumeState.summary_en != "",
                        section(
                            "CAREER OBJECTIVE",
                            rx.text(
                                ResumeState.summary_en,
                                font_size="9pt",
                                line_height="1.3",
                            ),
                        ),
                    ),
                    # Education — rx.foreach
                    rx.cond(
                        ResumeState.has_education,
                        section(
                            "EDUCATION",
                            rx.foreach(ResumeState.education, education_item),
                        ),
                    ),
                    # Experience — rx.foreach with NESTED rx.foreach for bullets
                    rx.cond(
                        ResumeState.has_experience,
                        section(
                            "EXPERIENCE",
                            rx.foreach(ResumeState.experience, experience_item),
                        ),
                    ),
                    # Courses
                    rx.cond(
                        ResumeState.courses.length() > 0,
                        section(
                            "COURSES",
                            rx.unordered_list(
                                rx.foreach(ResumeState.courses, skill_item),
                                padding_left="4mm",
                                list_style_type="disc",
                            ),
                        ),
                    ),
                    # Skills EN — rx.foreach
                    rx.cond(
                        ResumeState.has_skills_en,
                        section(
                            "SKILLS",
                            rx.unordered_list(
                                rx.foreach(ResumeState.skills_en, skill_item),
                                padding_left="4mm",
                                list_style_type="disc",
                            ),
                        ),
                    ),
                    # Technical Skills EN
                    rx.cond(
                        ResumeState.technical_skills_en.length() > 0,
                        section(
                            "TECHNICAL SKILLS",
                            rx.unordered_list(
                                rx.foreach(ResumeState.technical_skills_en, skill_item),
                                padding_left="4mm",
                                list_style_type="disc",
                            ),
                        ),
                    ),
                    # Languages — rx.foreach
                    rx.cond(
                        ResumeState.languages.length() > 0,
                        section(
                            "LANGUAGES",
                            rx.unordered_list(
                                rx.foreach(ResumeState.languages, language_item),
                                padding_left="4mm",
                                list_style_type="disc",
                            ),
                        ),
                    ),
                    # Column styling
                    flex="1",
                    text_align="left",
                    direction="ltr",
                    dir="ltr",
                    class_name="column col-en",
                ),

                # --- CENTRAL DIVIDER ---
                rx.box(
                    width="1px",
                    background_color="#d1d5db",
                    class_name="central-divider",
                ),

                # --- ARABIC COLUMN ---
                rx.box(
                    # Career Objective AR
                    rx.cond(
                        ResumeState.summary_ar != "",
                        section(
                            "الهدف الوظيفي",
                            rx.text(
                                ResumeState.summary_ar,
                                font_size="9pt",
                                line_height="1.3",
                                dir="rtl",
                            ),
                        ),
                    ),
                    # Education AR
                    rx.cond(
                        ResumeState.has_education,
                        section(
                            "التعليم",
                            rx.foreach(ResumeState.education, education_item),
                        ),
                    ),
                    # Experience AR
                    rx.cond(
                        ResumeState.has_experience,
                        section(
                            "الخبرات المهنية",
                            rx.foreach(ResumeState.experience, experience_item),
                        ),
                    ),
                    # Courses AR
                    rx.cond(
                        ResumeState.courses.length() > 0,
                        section(
                            "الدورات",
                            rx.unordered_list(
                                rx.foreach(ResumeState.courses, skill_item_ar),
                                padding_right="4mm",
                                padding_left="0",
                                list_style_type="disc",
                                dir="rtl",
                            ),
                        ),
                    ),
                    # Skills AR — rx.foreach
                    rx.cond(
                        ResumeState.has_skills_ar,
                        section(
                            "المهارات",
                            rx.unordered_list(
                                rx.foreach(ResumeState.skills_ar, skill_item_ar),
                                padding_right="4mm",
                                padding_left="0",
                                list_style_type="disc",
                                dir="rtl",
                            ),
                        ),
                    ),
                    # Technical Skills AR
                    rx.cond(
                        ResumeState.technical_skills_ar.length() > 0,
                        section(
                            "المهارات التقنية",
                            rx.unordered_list(
                                rx.foreach(ResumeState.technical_skills_ar, skill_item_ar),
                                padding_right="4mm",
                                padding_left="0",
                                list_style_type="disc",
                                dir="rtl",
                            ),
                        ),
                    ),
                    # Languages AR
                    rx.cond(
                        ResumeState.languages.length() > 0,
                        section(
                            "اللغات",
                            rx.unordered_list(
                                rx.foreach(ResumeState.languages, language_item),
                                padding_right="4mm",
                                padding_left="0",
                                list_style_type="disc",
                                dir="rtl",
                            ),
                        ),
                    ),
                    # Column styling
                    flex="1",
                    text_align="right",
                    direction="rtl",
                    dir="rtl",
                    class_name="column col-ar",
                ),
                # Columns container styling
                display="flex",
                direction="ltr",
                flex="1",
                padding="6mm 10mm",
                gap="6mm",
                class_name="columns-container",
            ),

            # A4 page styling
            width="210mm",
            min_height="297mm",
            background_color="white",
            display="flex",
            flex_direction="column",
            overflow="hidden",
            color="#333",
            class_name="a4-page",
            id="resume-document",
        ),
        # Outer wrapper
        display="flex",
        justify_content="center",
        padding="20px",
        background="#2a2a2a",
    )
