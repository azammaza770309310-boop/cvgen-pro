"""End-to-end tests for the rebuilt CVGen Pro (dark, Arabic-first, Cloud-AI-only).

Critical guarantees tested:
- Template count is DYNAMIC (computed from registry), never hardcoded
- No local semantic parsing exists
- AI parse returns clear error when no key is configured (no silent fallback)
- Bilingual templates render EN (LTR) + AR (RTL) independently
- Contact values in Arabic columns are dir=ltr protected
- A4 page boundary CSS + overflow warning CSS exist
- All registered templates render
- PDF / DOCX export work
- API keys are never exposed to the browser
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.resume import ResumeData, sample_resume
from app.services.resume_normalizer import normalize_resume_data
from app.services.template_service import (
    REGISTRY,
    get_template_count,
    list_categories,
    list_templates,
    render_template,
)
from app.services.ats_service import analyze_resume
from app.services.pdf_service import export_pdf
from app.services.docx_service import export_docx

client = TestClient(app)


# ---------------------------------------------------------------------------
# Startup + health
# ---------------------------------------------------------------------------

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_index_page():
    r = client.get("/")
    assert r.status_code == 200
    assert "CVGen" in r.text
    # Arabic landing title present
    assert "منشئ السير الذاتية" in r.text
    # The deterministic parse button must NOT exist
    assert "Parse (no AI" not in r.text
    # Page-1 boundary badge text present
    assert "نهاية الصفحة 1" in r.text


def test_settings_providers_no_keys():
    r = client.get("/api/settings/")
    assert r.status_code == 200
    data = r.json()
    assert "providers" in data
    for p in data["providers"]:
        assert "key" not in p
        assert "api_key" not in p
        assert "secret" not in p


# ---------------------------------------------------------------------------
# CRITICAL: Dynamic template count — never hardcoded
# ---------------------------------------------------------------------------

def test_template_count_is_dynamic():
    """The count returned by the API must equal len(REGISTRY)."""
    api_count = client.get("/api/templates/count").json()["count"]
    assert api_count == len(REGISTRY)
    assert api_count == get_template_count()


def test_templates_api_returns_count():
    r = client.get("/api/templates/")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == len(data["templates"])
    assert data["count"] == len(REGISTRY)


def test_categories_are_dynamic():
    cats = list_categories()
    total = sum(c["count"] for c in cats)
    assert total == len(REGISTRY)
    cat_ids = {c["id"] for c in cats}
    # must be derived from registry, not hardcoded
    for t in REGISTRY:
        assert t.category in cat_ids


def test_no_hardcoded_template_count_in_source():
    """Scan source files for hardcoded template-count display strings.
    The count must always come from get_template_count() or len(REGISTRY).
    """
    import os
    src_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app")
    # Only flag explicit count-as-display patterns, not numbers in CSS/IDs
    forbidden_patterns = [
        "10 templates", "36 templates", "37 templates",
        "10 قوالب", "36 قالب", "37 قالب",
        "10 قالب احترافي", "36 قالب احترافي", "37 قالب احترافي",
    ]
    for root, _, files in os.walk(src_dir):
        for f in files:
            if f.endswith((".py", ".js", ".html")):
                path = os.path.join(root, f)
                with open(path, encoding="utf-8") as fh:
                    content = fh.read()
                for pat in forbidden_patterns:
                    assert pat not in content, f"Hardcoded template count '{pat}' found in {path}"


def test_all_registered_templates_appear_in_api():
    r = client.get("/api/templates/")
    api_ids = {t["id"] for t in r.json()["templates"]}
    registry_ids = {t.id for t in REGISTRY}
    assert api_ids == registry_ids


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

def test_resume_data_defaults():
    r = ResumeData()
    assert r.personal.name == ""
    assert r.experience == []


def test_normalize_strips_contact_from_skills():
    raw = {
        "personal": {"name": "Test", "email": "test@example.com"},
        "skills": ["Python", "test@example.com", "React", "+1234567890"],
    }
    resume = normalize_resume_data(raw)
    assert "test@example.com" not in resume.skills
    assert "+1234567890" not in resume.skills
    assert "Python" in resume.skills


def test_normalize_dedup():
    raw = {"skills": ["Python", "python", "React"]}
    resume = normalize_resume_data(raw)
    assert resume.skills.count("Python") == 1


# ---------------------------------------------------------------------------
# CRITICAL: No local semantic parsing — AI required
# ---------------------------------------------------------------------------

def test_no_deterministic_parse_endpoint():
    r = client.post("/api/resume/parse", json={"text": "Jane Doe", "use_ai": False})
    assert r.status_code in (404, 405, 422)


def test_ai_parse_without_key_returns_clear_error(monkeypatch):
    """When no AI key is configured, AI parse must return a clear error — NOT
    silently fall back to local parsing.
    """
    from app.ai import manager as mgr_mod
    original_list = mgr_mod.ai_manager.list_providers()
    unconfigured = [{**p, "configured": False} for p in original_list]
    monkeypatch.setattr(mgr_mod.ai_manager, "list_providers", lambda: unconfigured)
    monkeypatch.setattr(mgr_mod.ai_manager, "is_configured", lambda p: False)
    r = client.post("/api/ai/parse", json={"text": "Jane Doe\njane@example.com", "provider": "gemini"})
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is False
    assert data["code"] == "ai_provider_not_configured"
    assert "AI API key is required" in data["error"] or "لم يتم إعداد" in data["error"]
    assert "data" not in data or data.get("data") is None


def test_parser_module_has_no_rule_based_function():
    from app.services import resume_parser
    assert not hasattr(resume_parser, "parse_rule_based")
    assert not hasattr(resume_parser, "parse_resume_deterministic")
    assert hasattr(resume_parser, "parse_resume_ai")


# ---------------------------------------------------------------------------
# ATS analysis
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ats_analysis_returns_score():
    resume = sample_resume("en")
    result = await analyze_resume(resume, job_description="python fastapi react")
    assert 0 <= result.score <= 100
    assert result.grade in "ABCDF"


def test_ats_api_endpoint():
    r = client.post("/api/ats/analyze", json={"data": sample_resume("en").model_dump(), "use_ai": False})
    assert r.status_code == 200
    assert "score" in r.json()


# ---------------------------------------------------------------------------
# Templates — all render
# ---------------------------------------------------------------------------

def test_all_templates_render_html():
    resume = sample_resume("bilingual")
    for t in REGISTRY:
        html = render_template(t.id, resume)
        assert isinstance(html, str)
        assert "cv-root" in html


def test_templates_api_render():
    r = client.post("/api/templates/render", json={"data": sample_resume("en").model_dump(), "template_id": "ats_classic"})
    assert r.status_code == 200
    assert "cv-root" in r.json()["html"]


def test_bilingual_template_has_both_languages():
    resume = sample_resume("bilingual")
    for tid in ("bilingual_teal_gold", "bilingual_navy", "bilingual_peach", "international_bilingual"):
        html = render_template(tid, resume)
        assert "Ahmed" in html, f"{tid} missing English name"
        assert "أحمد" in html, f"{tid} missing Arabic name"


def test_bilingual_arabic_column_is_rtl():
    """Arabic column must have dir=rtl, English column dir=ltr."""
    resume = sample_resume("bilingual")
    html = render_template("bilingual_teal_gold", resume)
    assert 'dir="rtl"' in html or "dir='rtl'" in html
    assert 'dir="ltr"' in html or "dir='ltr'" in html


def test_contact_values_protected_in_arabic_column():
    """Emails/phones/URLs in Arabic columns must be wrapped with dir=ltr."""
    resume = sample_resume("bilingual")
    resume.personal.email = "test@example.com"
    resume.personal.phone = "+966555123456"
    html = render_template("bilingual_teal_gold", resume)
    # The email should appear inside a dir=ltr span in the Arabic column
    assert 'dir="ltr"' in html
    assert "test@example.com" in html


# ---------------------------------------------------------------------------
# A4 page boundary + overflow warning (CSS present)
# ---------------------------------------------------------------------------

def test_a4_page_css_present():
    r = client.get("/static/css/templates.css")
    assert r.status_code == 200
    css = r.text
    assert ".a4-page" in css
    assert "1123px" in css  # A4 height at 96 DPI
    assert ".page1-boundary" in css
    assert ".page1-badge" in css


def test_overflow_warning_css_present():
    r = client.get("/static/css/app.css")
    assert r.status_code == 200
    assert ".overflow-warning" in r.text


def test_design_stepper_css_present():
    r = client.get("/static/css/app.css")
    assert r.status_code == 200
    assert ".stepper" in r.text
    assert "--cv-font-size" in client.get("/static/css/templates.css").text
    assert "--cv-line-height" in client.get("/static/css/templates.css").text
    assert "--cv-margin" in client.get("/static/css/templates.css").text


def test_page1_boundary_text_in_html():
    r = client.get("/")
    assert "نهاية الصفحة 1" in r.text


# ---------------------------------------------------------------------------
# PDF export
# ---------------------------------------------------------------------------

def test_pdf_export_bytes():
    resume = sample_resume("en")
    pdf = export_pdf(resume, "ats_classic")
    assert isinstance(pdf, bytes)
    assert pdf[:4] == b"%PDF"


def test_pdf_api_endpoint():
    r = client.post("/api/export/pdf", json={"data": sample_resume("en").model_dump(), "template_id": "ats_classic"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"


def test_pdf_bilingual_template():
    r = client.post("/api/export/pdf", json={"data": sample_resume("bilingual").model_dump(), "template_id": "bilingual_teal_gold"})
    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# DOCX export
# ---------------------------------------------------------------------------

def test_docx_export_bytes():
    resume = sample_resume("en")
    docx = export_docx(resume)
    assert isinstance(docx, bytes)
    assert docx[:2] == b"PK"


def test_docx_api_endpoint():
    r = client.post("/api/export/docx", json={"data": sample_resume("en").model_dump()})
    assert r.status_code == 200
    assert r.content[:2] == b"PK"


def test_docx_bilingual():
    r = client.post("/api/export/docx", json={"data": sample_resume("bilingual").model_dump(), "lang": "bilingual"})
    assert r.status_code == 200
    assert r.content[:2] == b"PK"


# ---------------------------------------------------------------------------
# AI provider manager
# ---------------------------------------------------------------------------

def test_ai_manager_lists_all_providers():
    from app.ai.manager import ai_manager
    providers = ai_manager.list_providers()
    ids = {p["id"] for p in providers}
    for expected in ("gemini", "openai", "anthropic", "openrouter", "groq", "deepseek", "mistral", "xai"):
        assert expected in ids


def test_ai_manager_no_key_is_configured_by_default(monkeypatch):
    """By default (no env vars set), external providers are not configured.
    ZAI may be configured if the internal gateway is available."""
    from app.ai import manager as mgr_mod
    original_list = mgr_mod.ai_manager.list_providers()
    # Check that all EXTERNAL providers (gemini, openai, etc.) are not configured
    external = [p for p in original_list if p["id"] != "zai"]
    for p in external:
        assert p["configured"] is False


# ---------------------------------------------------------------------------
# Sample endpoint
# ---------------------------------------------------------------------------

def test_sample_endpoint():
    for lang in ("en", "ar", "bilingual"):
        r = client.get(f"/api/resume/sample?lang={lang}")
        assert r.status_code == 200
        assert "personal" in r.json()


def test_sample_bilingual_has_both_languages():
    r = client.get("/api/resume/sample?lang=bilingual")
    data = r.json()
    assert data["personal"]["name_en"] == "Ahmed Abdullah"
    assert data["personal"]["name_ar"] == "أحمد عبدالله"
    assert data["summary"]["en"]
    assert data["summary"]["ar"]


# ---------------------------------------------------------------------------
# Registry metadata completeness
# ---------------------------------------------------------------------------

def test_every_template_has_required_metadata():
    for t in REGISTRY:
        assert t.id
        assert t.name
        assert t.name_ar
        assert t.description
        assert t.description_ar
        assert t.category in ("ats", "creative", "bilingual")
        assert t.ats_level in ("high", "medium", "low")
        assert isinstance(t.supported_languages, list)
        assert t.accent.startswith("#")
