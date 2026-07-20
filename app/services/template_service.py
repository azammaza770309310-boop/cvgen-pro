"""Centralized template registry — the SINGLE source of truth for resume templates.

ONLY the official master template is registered. The template is FIXED —
only the data is dynamic. Cloud AI provides the data; the renderer provides
the design. The template NEVER changes based on the data.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List

from app.models.resume import ResumeData
from app.templates_render import render_official_bilingual_master


@dataclass
class TemplateDef:
    """Metadata + renderer for one resume template."""
    id: str
    name: str
    name_ar: str
    description: str
    description_ar: str
    category: str  # "ats" | "creative" | "bilingual"
    ats_level: str  # "high" | "medium" | "low"
    supported_languages: List[str]
    accent: str
    render: Callable[[ResumeData], str]


# ---------------------------------------------------------------------------
# REGISTRY — the official master template only.
# The count is ALWAYS len(REGISTRY) = 1.
# ---------------------------------------------------------------------------

REGISTRY: List[TemplateDef] = [
    TemplateDef(
        id="official_bilingual_master",
        name="Official Bilingual Master",
        name_ar="القالب الرسمي ثنائي اللغة",
        description="The official master template — black & white, two-column bilingual layout matching the original CV.",
        description_ar="القالب الرسمي المعتمد — أسود/أبيض، تخطيط ثنائي العمود ثنائي اللغة يطابق السيرة الذاتية الأصلية.",
        category="ats",
        ats_level="high",
        supported_languages=["en", "ar", "bilingual"],
        accent="#000000",
        render=render_official_bilingual_master,
    ),
]


BY_ID: Dict[str, TemplateDef] = {t.id: t for t in REGISTRY}


def get_template_count() -> int:
    """Return the dynamic count of registered templates."""
    return len(REGISTRY)


def list_templates() -> List[dict]:
    """Serialize ALL templates for the API. Count = len(list)."""
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
    """Dynamically compute categories from the registry."""
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
