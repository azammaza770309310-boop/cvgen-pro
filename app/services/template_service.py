"""Centralized template registry — the SINGLE source of truth for resume templates.

Every template is defined ONCE here. The UI dynamically discovers ALL templates
from this registry — no hardcoded template count anywhere in the application.

Adding a new template to REGISTRY automatically:
  - increases the displayed count
  - makes it available in the gallery, editor, preview, PDF, and DOCX
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List

from app.models.resume import ResumeData
from app.templates_render import (
    render_ats_classic,
    render_minimal_black,
    render_modern_sidebar,
    render_corporate_slate,
    render_botanical_beige,
    render_lavender_minimal,
    render_bilingual_teal_gold,
    render_bilingual_navy,
    render_bilingual_peach,
    render_international_bilingual,
    render_bilingual_ats_classic,
)


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
    supported_languages: List[str]  # e.g. ["en", "ar", "bilingual"]
    accent: str
    render: Callable[[ResumeData], str]


# ---------------------------------------------------------------------------
# REGISTRY — add templates here. The count is ALWAYS len(REGISTRY).
# ---------------------------------------------------------------------------

REGISTRY: List[TemplateDef] = [
    TemplateDef(
        id="bilingual_ats_classic",
        name="Bilingual ATS Classic",
        name_ar="ثنائي اللغة — كلاسيكي ATS",
        description="Simple black & white bilingual resume matching the original CV style.",
        description_ar="قالب بسيط أسود/أبيض يطابق السير الذاتية الأصلية — عناوين ثنائية اللغة جنباً إلى جنب.",
        category="ats",
        ats_level="high",
        supported_languages=["en", "ar", "bilingual"],
        accent="#000000",
        render=render_bilingual_ats_classic,
    ),
    TemplateDef(
        id="ats_classic",
        name="ATS Classic",
        name_ar="كلاسيكي ATS",
        description="Single column, clean layout — maximum ATS compatibility.",
        description_ar="تخطيط بعمود واحد ونظيف — أقصى توافق مع أنظمة ATS.",
        category="ats",
        ats_level="high",
        supported_languages=["en", "ar", "bilingual"],
        accent="#111827",
        render=render_ats_classic,
    ),
    TemplateDef(
        id="minimal_black",
        name="Minimal Black",
        name_ar="أسود مبسط",
        description="30/70 split with a vertical timeline sidebar.",
        description_ar="تقسيم 30/70 مع شريط زمني جانبي.",
        category="creative",
        ats_level="medium",
        supported_languages=["en", "ar", "bilingual"],
        accent="#000000",
        render=render_minimal_black,
    ),
    TemplateDef(
        id="modern_sidebar",
        name="Modern Sidebar",
        name_ar="الشريط الجانبي العصري",
        description="Dark gradient sidebar with photo placeholder.",
        description_ar="شريط جانبي بتدرج داكن مع مكان للصورة.",
        category="creative",
        ats_level="medium",
        supported_languages=["en", "ar", "bilingual"],
        accent="#0f766e",
        render=render_modern_sidebar,
    ),
    TemplateDef(
        id="corporate_slate",
        name="Corporate Slate",
        name_ar="رمادي مؤسسي",
        description="Navy header with slate sidebar — corporate feel.",
        description_ar="ترويسة كحلية مع شريط جانبي رمادي — طابع مؤسسي.",
        category="creative",
        ats_level="medium",
        supported_languages=["en", "ar", "bilingual"],
        accent="#1e3a5f",
        render=render_corporate_slate,
    ),
    TemplateDef(
        id="botanical_beige",
        name="Botanical Beige",
        name_ar="بيج نباتي",
        description="Warm beige with a circular CV monogram.",
        description_ar="لون بيج دافئ مع دائرة للأحرف الأولى.",
        category="creative",
        ats_level="medium",
        supported_languages=["en", "ar", "bilingual"],
        accent="#7d8471",
        render=render_botanical_beige,
    ),
    TemplateDef(
        id="lavender_minimal",
        name="Lavender Minimal",
        name_ar="خزامى مبسط",
        description="Soft lavender with minimal accents.",
        description_ar="لون خزامي ناعم بلمسات مبسطة.",
        category="creative",
        ats_level="medium",
        supported_languages=["en", "ar", "bilingual"],
        accent="#7c6bad",
        render=render_lavender_minimal,
    ),
    TemplateDef(
        id="bilingual_teal_gold",
        name="Bilingual Teal-Gold",
        name_ar="ثنائي اللغة — فيروزي وذهبي",
        description="50/50 mirror layout, teal and gold.",
        description_ar="تخطيط متناظر 50/50 — فيروزي وذهبي.",
        category="bilingual",
        ats_level="low",
        supported_languages=["bilingual"],
        accent="#0d9488",
        render=render_bilingual_teal_gold,
    ),
    TemplateDef(
        id="bilingual_navy",
        name="Bilingual Navy",
        name_ar="ثنائي اللغة — كحلي",
        description="50/50 mirror layout, navy with diamond bullets.",
        description_ar="تخطيط متناظر 50/50 — كحلي مع نقاط ماسية.",
        category="bilingual",
        ats_level="low",
        supported_languages=["bilingual"],
        accent="#1e3a5f",
        render=render_bilingual_navy,
    ),
    TemplateDef(
        id="bilingual_peach",
        name="Bilingual Peach",
        name_ar="ثنائي اللغة — خوخي",
        description="50/50 mirror layout, peach with boxed sections.",
        description_ar="تخطيط متناظر 50/50 — خوخي مع أقسام محاطة بإطار.",
        category="bilingual",
        ats_level="low",
        supported_languages=["bilingual"],
        accent="#e07856",
        render=render_bilingual_peach,
    ),
    TemplateDef(
        id="international_bilingual",
        name="International Bilingual",
        name_ar="دولي ثنائي اللغة",
        description="Single column, stacked EN/AR sections.",
        description_ar="عمود واحد مع أقسام إنجليزية وعربية متراصة.",
        category="bilingual",
        ats_level="medium",
        supported_languages=["bilingual"],
        accent="#334155",
        render=render_international_bilingual,
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
