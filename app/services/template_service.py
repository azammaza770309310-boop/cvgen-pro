"""Centralized template registry — the SINGLE source of truth for resume templates.

3 official templates:
1. official_bilingual_master — Two-column (EN left, AR right)
2. official_english_single — Single-column English-only
3. official_arabic_single — Single-column Arabic-only RTL

Templates are FIXED — only data is dynamic.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List

from app.models.resume import ResumeData
from app.templates_render import (
    render_official_bilingual_master,
    render_english_single_column,
    render_arabic_single_column,
)


@dataclass
class TemplateDef:
    """Metadata + renderer for one resume template."""
    id: str
    name: str
    name_ar: str
    description: str
    description_ar: str
    category: str
    ats_level: str
    supported_languages: List[str]
    accent: str
    render: Callable[[ResumeData], str]


REGISTRY: List[TemplateDef] = [
    TemplateDef(
        id="official_bilingual_master",
        name="Bilingual Master",
        name_ar="ثنائي اللغة",
        description="Two-column bilingual layout — English left, Arabic right.",
        description_ar="تخطيط ثنائي العمود — إنجليزي يسار، عربي يمين.",
        category="bilingual",
        ats_level="high",
        supported_languages=["en", "ar", "bilingual"],
        accent="#000000",
        render=render_official_bilingual_master,
    ),
    TemplateDef(
        id="official_english_single",
        name="English Single",
        name_ar="إنجليزي فردي",
        description="Single-column English-only resume, centered header with blue links.",
        description_ar="سيرة بعمود واحد بالإنجليزية فقط، رأس مركزي بروابط زرقاء.",
        category="ats",
        ats_level="high",
        supported_languages=["en"],
        accent="#1a5276",
        render=render_english_single_column,
    ),
    TemplateDef(
        id="official_arabic_single",
        name="Arabic Single",
        name_ar="عربي فردي",
        description="Single-column Arabic-only resume, RTL, centered header.",
        description_ar="سيرة بعمود واحد بالعربية فقط، RTL، رأس مركزي.",
        category="ats",
        ats_level="high",
        supported_languages=["ar"],
        accent="#000000",
        render=render_arabic_single_column,
    ),
]


BY_ID: Dict[str, TemplateDef] = {t.id: t for t in REGISTRY}


def get_template_count() -> int:
    return len(REGISTRY)


def list_templates() -> List[dict]:
    return [
        {
            "id": t.id,
            "name": t.name,
            "name_ar": t.name_ar,
            "description": t.description,
            "description_ar": t.description_ar,
            "category": t.category,
            "ats_level": t.ats_level,
            "supported_languages": t.supported_languages,
            "accent": t.accent,
        }
        for t in REGISTRY
    ]


def list_categories() -> List[dict]:
    cats: Dict[str, dict] = {}
    for t in REGISTRY:
        c = t.category
        if c not in cats:
            cats[c] = {"id": c, "label_en": c.title(), "label_ar": _CATEGORY_AR.get(c, c), "count": 0}
        cats[c]["count"] += 1
    return list(cats.values())


_CATEGORY_AR = {
    "ats": "ATS",
    "creative": "إبداعية",
    "bilingual": "ثنائية اللغة",
}


def get_template(template_id: str) -> TemplateDef:
    t = BY_ID.get(template_id)
    if not t:
        return REGISTRY[0]
    return t


def render_template(template_id: str, resume: ResumeData) -> str:
    t = get_template(template_id)
    return t.render(resume)
