"""CVGen Pro — Reflex Application Entry Point

Fixed UI: organized control panel with rx.grid, clean layout.
"""
from __future__ import annotations

from pathlib import Path
import shutil

import reflex as rx
from reflex_app.reflex_app.state import ResumeState
from reflex_app.reflex_app.resume_preview import resume_preview_bilingual


def _load_template_css_content() -> str:
    """Load templates.css content for embedding in the page.

    In Reflex 0.9.7, app.stylesheets doesn't reliably render custom CSS files
    in the HTML output. Instead, we embed the CSS directly via rx.html() with
    a <style> tag. This guarantees the CSS is loaded and applied to the
    rx.html(preview_html) content.
    """
    css_path = Path(__file__).resolve().parent.parent.parent / "app" / "static" / "css" / "templates.css"
    if css_path.exists():
        return css_path.read_text(encoding="utf-8")
    return ""


# Load CSS content at import time
_template_css = _load_template_css_content()


def index() -> rx.Component:
    """Main page: toolbar (grid) + raw text input + resume preview.

    The toolbar has two tiers:
      1. BASIC row (always visible): navigation, templates, colors, edit,
         AI assistant, undo/redo, save, download PDF.
      2. ADVANCED rows (collapsible): font size, margin steppers, reset,
         page info, load sample. Hidden by default on mobile to save space.

    Below the toolbar is a collapsible raw text input area where users
    paste their resume text for AI parsing.
    """
    return rx.box(
        # ===== CRITICAL: Embed templates.css via <style> tag =====
        # Reflex 0.9.7's app.stylesheets doesn't render custom CSS in the HTML.
        # We embed it directly via rx.html() with a <style> tag so it applies
        # to the rx.html(preview_html) content.
        rx.html(f"<style>{_template_css}</style>"),

        # ===== TOOLBAR (dark, responsive) =====
        rx.vstack(
            # Row 1: BASIC navigation bar — ALWAYS VISIBLE, wraps on mobile
            rx.flex(
                rx.button("✕", on_click=rx.redirect("/"), color_scheme="red", size="2"),
                rx.text("معاينة السيرة الذاتية", color="white", font_weight="bold", font_size="14px"),
                rx.spacer(),
                rx.button("القوالب", on_click=ResumeState.toggle_templates, variant="ghost", color="white", size="2"),
                rx.button("🔑 API", on_click=ResumeState.toggle_api_keys, variant="ghost", color="white", size="2"),
                rx.button("⚙️", on_click=ResumeState.toggle_settings, variant="ghost", color="white", size="2"),
                rx.button("✨ AI", on_click=ResumeState.toggle_input, variant="ghost", color="#fbbf24", size="2"),
                rx.button("↶", on_click=ResumeState.undo, variant="ghost", color="white", size="2"),
                rx.button("↷", on_click=ResumeState.redo, variant="ghost", color="white", size="2"),
                rx.button("Word", on_click=ResumeState.export_docx, variant="ghost", color="white", size="2"),
                rx.button("PDF", on_click=ResumeState.export_pdf, bg="#f97316", color="white", size="2", font_weight="bold"),
                width="100%",
                align_items="center",
                gap="4px",
                padding="8px 12px",
                flex_wrap="wrap",
            ),
            # Row 2: Toggle button for advanced controls — ALWAYS VISIBLE
            rx.flex(
                rx.button(
                    rx.cond(
                        ResumeState.show_advanced_controls,
                        rx.text("▲ إخفاء الإعدادات المتقدمة", font_size="12px"),
                        rx.text("▼ إعدادات متقدمة ⚙️", font_size="12px"),
                    ),
                    on_click=ResumeState.toggle_advanced_controls,
                    variant="ghost",
                    color="#fbbf24",
                    size="2",
                    bg="#2d2d2d",
                    border="1px solid #3d3d3d",
                    border_radius="6px",
                    padding="4px 12px",
                ),
                rx.spacer(),
                rx.text(ResumeState.page_count, color="#666", font_size="11px"),
                rx.text("صفحة", color="#666", font_size="11px"),
                width="100%",
                align_items="center",
                padding="4px 16px",
            ),
            # Row 3: ADVANCED controls — COLLAPSIBLE
            rx.cond(
                ResumeState.show_advanced_controls,
                rx.grid(
                    rx.hstack(
                        rx.text("حجم الخط", color="#999", font_size="12px"),
                        rx.button("−", on_click=ResumeState.decrease_font_size, bg="#2d2d2d", color="white", size="2"),
                        rx.text(ResumeState.font_size, color="#f97316", font_weight="bold", font_size="13px", min_width="35px", text_align="center"),
                        rx.button("+", on_click=ResumeState.increase_font_size, bg="#2d2d2d", color="white", size="2"),
                        spacing="2",
                        align_items="center",
                    ),
                    rx.hstack(
                        rx.text("الهوامش", color="#999", font_size="12px"),
                        rx.button("−", on_click=ResumeState.decrease_margin, bg="#2d2d2d", color="white", size="2"),
                        rx.text(ResumeState.margin, color="#f97316", font_weight="bold", font_size="13px", min_width="35px", text_align="center"),
                        rx.button("+", on_click=ResumeState.increase_margin, bg="#2d2d2d", color="white", size="2"),
                        spacing="2",
                        align_items="center",
                    ),
                    rx.button("↺ إعادة ضبط", on_click=ResumeState.reset_controls, bg="#2d2d2d", color="#fbbf24", size="2", border="1px solid #f59e0b"),
                    rx.button("📄 تحميل نموذج", on_click=ResumeState.load_sample, bg="#2d2d2d", color="white", size="2"),
                    columns="4",
                    spacing="4",
                    width="100%",
                    padding="8px 16px",
                ),
                rx.box(),
            ),
            bg="#1e1e1e",
            width="100%",
            spacing="0",
        ),

        # ===== RAW TEXT INPUT AREA (collapsible) =====
        rx.cond(
            ResumeState.show_input,
            rx.vstack(
                rx.text("الصق معلوماتك هنا كاملةً (الاسم، الهاتف، البريد، الخبرات، التعليم، المهارات...)", color="#999", font_size="12px"),
                rx.text_area(
                    value=ResumeState.raw_text,
                    on_change=ResumeState.set_raw_text,
                    placeholder="الصق سيرتك الذاتية هنا...",
                    width="100%",
                    min_height="200px",
                    bg="#1a1a1a",
                    color="white",
                    border="1px solid #3d3d3d",
                ),
                rx.hstack(
                    rx.button(
                        "⚡ توليد السيرة بالذكاء الاصطناعي",
                        on_click=ResumeState.parse_resume_ai,
                        bg="#f97316",
                        color="white",
                        size="3",
                        font_weight="bold",
                    ),
                    rx.button("إغلاق", on_click=ResumeState.toggle_input, variant="ghost", color="#999", size="2"),
                    spacing="3",
                ),
                width="100%",
                padding="16px",
                bg="#222",
            ),
            rx.box(),
        ),

        # ===== SETTINGS MODAL (API key management) =====
        rx.cond(
            ResumeState.show_settings,
            rx.vstack(
                rx.text("إعدادات API", color="white", font_weight="bold", font_size="16px"),
                rx.foreach(
                    ResumeState.providers_list,
                    lambda p: rx.hstack(
                        rx.text(p["name"], color="white", font_size="13px"),
                        rx.text(f"({p['key_count']} مفاتيح)", color="#999", font_size="11px"),
                        rx.cond(
                            p["configured"],
                            rx.text("✓", color="green", font_size="14px"),
                            rx.text("✗", color="red", font_size="14px"),
                        ),
                        spacing="3",
                    ),
                ),
                rx.button("إغلاق", on_click=ResumeState.toggle_settings, variant="ghost", color="#999", size="2"),
                width="100%",
                max_width="500px",
                padding="20px",
                bg="#1e1e1e",
                border="1px solid #3d3d3d",
                border_radius="8px",
            ),
            rx.box(),
        ),

        # ===== TEMPLATE SELECTOR (collapsible) =====
        rx.cond(
            ResumeState.show_templates,
            rx.vstack(
                rx.text("اختر القالب", color="white", font_weight="bold", font_size="14px"),
                rx.foreach(
                    ResumeState.templates_list,
                    lambda t: rx.button(
                        t["name"],
                        on_click=lambda tid=t["id"]: ResumeState.set_template(tid),
                        bg="#2d2d2d",
                        color="white",
                        size="2",
                        width="100%",
                    ),
                ),
                rx.button("إغلاق", on_click=ResumeState.toggle_templates, variant="ghost", color="#999", size="2"),
                width="100%",
                max_width="300px",
                padding="16px",
                bg="#1e1e1e",
                border="1px solid #3d3d3d",
                border_radius="8px",
            ),
            rx.box(),
        ),

        # ===== API KEYS MANAGEMENT PANEL (collapsible) =====
        rx.cond(
            ResumeState.show_api_keys,
            rx.vstack(
                rx.text("🔑 إدارة مفاتيح API", color="white", font_weight="bold", font_size="16px"),

                # --- Provider list with status ---
                rx.text("المزودون الحاليون:", color="#999", font_size="12px"),
                rx.foreach(
                    ResumeState.providers_list,
                    lambda p: rx.hstack(
                        rx.text(p["name"], color="white", font_size="13px", min_width="120px"),
                        rx.text(f"({p['key_count']} مفاتيح)", color="#999", font_size="11px"),
                        rx.cond(
                            p["configured"],
                            rx.text("✓ مفعّل", color="green", font_size="12px"),
                            rx.text("✗ غير مفعّل", color="red", font_size="12px"),
                        ),
                        spacing="2",
                        width="100%",
                        padding="4px 0",
                        border_bottom="1px solid #333",
                    ),
                ),

                # --- Key list (flattened for rx.foreach) ---
                rx.text("المفاتيح المخزنة:", color="#999", font_size="12px"),
                rx.foreach(
                    ResumeState.provider_keys_list,
                    lambda k: rx.hstack(
                        rx.text(k["provider_name"], color="#ccc", font_size="11px", min_width="80px"),
                        rx.text(k["masked"], color="#666", font_size="10px"),
                        rx.text(f"[{k['source']}]", color="#555", font_size="9px"),
                        rx.cond(
                            k["source"] == "file",
                            rx.button(
                                "🗑",
                                on_click=lambda prov=k["provider"], idx=k["index"]: ResumeState.remove_api_key(prov, idx),
                                size="1",
                                bg="#3d1515",
                                color="#ff6666",
                            ),
                            rx.text("env", color="#555", font_size="9px"),
                        ),
                        spacing="2",
                        width="100%",
                    ),
                ),

                # --- Add new key ---
                rx.divider(border_color="#333"),
                rx.text("➕ إضافة مفتاح جديد:", color="#fbbf24", font_weight="bold", font_size="13px"),
                rx.hstack(
                    rx.select(
                        ["gemini", "openai", "anthropic", "openrouter", "groq", "deepseek", "mistral", "xai"],
                        value=ResumeState.new_key_provider,
                        on_change=ResumeState.set_new_key_provider,
                        size="2",
                        bg="#2d2d2d",
                        color="white",
                    ),
                    rx.input(
                        value=ResumeState.new_key_value,
                        on_change=ResumeState.set_new_key_value,
                        placeholder="ألصق المفتاح هنا...",
                        type="password",
                        size="2",
                        bg="#2d2d2d",
                        color="white",
                        border="1px solid #555",
                        flex="1",
                    ),
                    rx.button(
                        "إضافة",
                        on_click=ResumeState.add_new_api_key,
                        bg="#f97316",
                        color="white",
                        size="2",
                        font_weight="bold",
                    ),
                    spacing="2",
                    width="100%",
                ),

                # --- Test Gemini key ---
                rx.divider(border_color="#333"),
                rx.text("🔬 اختبار مفتاح Gemini:", color="#fbbf24", font_weight="bold", font_size="13px"),
                rx.hstack(
                    rx.input(
                        value=ResumeState.test_key_value,
                        on_change=ResumeState.set_test_key_value,
                        placeholder="ألصق مفتاح Gemini للاختبار...",
                        type="password",
                        size="2",
                        bg="#2d2d2d",
                        color="white",
                        border="1px solid #555",
                        flex="1",
                    ),
                    rx.button(
                        "اختبار",
                        on_click=ResumeState.run_test_gemini_key,
                        bg="#2563eb",
                        color="white",
                        size="2",
                        font_weight="bold",
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.cond(
                    ResumeState.test_key_result != "",
                    rx.text(ResumeState.test_key_result, color="white", font_size="12px", padding="4px 8px"),
                    rx.text(""),
                ),

                # --- Key links (how to get API keys) ---
                rx.divider(border_color="#333"),
                rx.text("🔗 روابط الحصول على المفاتيح:", color="#fbbf24", font_weight="bold", font_size="13px"),
                rx.foreach(
                    ResumeState.key_links_list,
                    lambda kl: rx.hstack(
                        rx.text(kl["provider"], color="#ccc", font_size="11px", min_width="80px", text_transform="capitalize"),
                        rx.link(
                            kl["label"],
                            href=kl["url"],
                            color="#3b82f6",
                            font_size="11px",
                            is_external=True,
                        ),
                        spacing="2",
                        width="100%",
                        padding="2px 0",
                    ),
                ),

                # --- Close button ---
                rx.button("إغلاق", on_click=ResumeState.toggle_api_keys, variant="ghost", color="#999", size="2"),
                width="100%",
                max_width="550px",
                padding="20px",
                bg="#1e1e1e",
                border="1px solid #3d3d3d",
                border_radius="8px",
                spacing="3",
            ),
            rx.box(),
        ),

        # ===== RESUME PREVIEW =====
        resume_preview_bilingual(),

        width="100%",
        min_height="100vh",
    )


app = rx.App()

# Register the main page
app.add_page(index, route="/")

# Health check endpoint — required by Render's deployment health check.
# Reflex 0.9.7 doesn't have @app.api_route, so we add a raw Starlette Route
# to the underlying ASGI application's route list.
from starlette.routing import Route
from starlette.responses import JSONResponse


async def health_check(request):
    """Render health check endpoint.

    Returns a simple JSON 200 response so Render's port scanner confirms
    the service is up.
    """
    return JSONResponse({
        "status": "ok",
        "app": "CVGen Pro",
        "version": "2.0.0",
        "runtime": "reflex",
    })


# Add the health route to the Reflex app's underlying Starlette application.
# In Reflex 0.9.7, the internal ASGI app is accessible via app._api.
app._api.routes.insert(0, Route("/health", health_check, methods=["GET"]))
