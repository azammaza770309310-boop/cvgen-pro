"""CVGen Pro — Reflex Application Entry Point

Restores the OLD UI/UX design from the FastAPI/Jinja2 app, adapted to Reflex.

The OLD UI had:
- Landing page: textarea + provider select + font select + template select + generate button
- Editor view: dark toolbar (7 rows: nav, steppers, controls, options, color picker,
  template gallery, page info) + A4 preview below
- Settings modal for API keys
- This Reflex version keeps the same layout and button arrangement.
"""
from __future__ import annotations

from pathlib import Path

import reflex as rx
from reflex_app.reflex_app.state import ResumeState
from reflex_app.reflex_app.resume_preview import resume_preview_bilingual


def _load_template_css_content() -> str:
    """Load templates.css content for embedding in the page."""
    css_path = Path(__file__).resolve().parent.parent.parent / "app" / "static" / "css" / "templates.css"
    if css_path.exists():
        return css_path.read_text(encoding="utf-8")
    return ""


_template_css = _load_template_css_content()

# Old UI color scheme
_BG_DARK = "#1e1e1e"
_BG_DARKER = "#181818"
_BG_CARD = "#252525"
_BG_INPUT = "#2d2d2d"
_TEXT_WHITE = "#ffffff"
_TEXT_MUTED = "#999999"
_TEXT_GOLD = "#fbbf24"
_TEXT_ORANGE = "#f97316"
_BORDER = "#3d3d3d"
_BTN_GHOST = "#2d2d2d"


def index() -> rx.Component:
    """Main page — restores the OLD UI with landing page + editor."""
    return rx.box(
        # CSS
        rx.html(f"<style>{_template_css}</style>"),

        # ===== LANDING PAGE (visible when no resume loaded) =====
        rx.cond(
            ResumeState.name_en == "",
            # Landing view
            rx.vstack(
                # Header
                rx.text("منشئ السير الذاتية بالذكاء الاصطناعي", color=_TEXT_WHITE, font_size="24px", font_weight="bold"),
                rx.text("حوّل معلوماتك الخام إلى سيرة ذاتية احترافية بالقالب الرسمي المعتمد.", color=_TEXT_MUTED, font_size="14px"),
                spacing="2",
                margin_bottom="20px",
            ),
            rx.box(),  # empty when editor is visible
        ),

        # ===== INPUT CARD (always visible on landing) =====
        rx.cond(
            ResumeState.name_en == "",
            rx.vstack(
                # Textarea
                rx.text_area(
                    value=ResumeState.raw_text,
                    on_change=ResumeState.set_raw_text,
                    placeholder="الصق معلوماتك هنا كاملةً (الاسم، الهاتف، البريد، الخبرات، التعليم، المهارات...)",
                    width="100%",
                    min_height="180px",
                    bg=_BG_INPUT,
                    color=_TEXT_WHITE,
                    border=f"1px solid {_BORDER}",
                    border_radius="8px",
                    padding="12px",
                    font_size="14px",
                ),
                # Generate button
                rx.button(
                    "⚡ توليد ومعاينة السيرة الذاتية",
                    on_click=ResumeState.parse_resume_ai,
                    bg=_TEXT_ORANGE,
                    color=_TEXT_WHITE,
                    size="4",
                    font_weight="bold",
                    width="100%",
                    margin_top="12px",
                ),
                # Load sample
                rx.button(
                    "📄 تحميل نموذج للتجربة",
                    on_click=ResumeState.load_sample,
                    bg=_BTN_GHOST,
                    color=_TEXT_WHITE,
                    size="2",
                    width="100%",
                    margin_top="8px",
                ),
                # API keys
                rx.button(
                    "⚙ إعدادات API",
                    on_click=ResumeState.toggle_api_keys,
                    bg=_BTN_GHOST,
                    color=_TEXT_GOLD,
                    size="2",
                    margin_top="8px",
                ),
                width="100%",
                max_width="600px",
                padding="24px",
                bg=_BG_CARD,
                border_radius="12px",
                spacing="2",
            ),
            rx.box(),  # hidden when editor is visible
        ),

        # ===== EDITOR VIEW (visible when resume is loaded) =====
        rx.cond(
            ResumeState.name_en != "",
            rx.vstack(
                # ===== EDITOR TOOLBAR (dark, RTL, matching old layout) =====
                rx.vstack(
                    # Row 1: Nav bar
                    rx.flex(
                        rx.button("✕", on_click=lambda: ResumeState.set_resume_data({}), color_scheme="red", size="2"),
                        rx.text("معاينة السيرة الذاتية", color=_TEXT_WHITE, font_weight="bold", font_size="14px"),
                        rx.spacer(),
                        rx.button("القوالب", on_click=ResumeState.toggle_templates, variant="ghost", color=_TEXT_WHITE, size="2"),
                        rx.button("🔑 API", on_click=ResumeState.toggle_api_keys, variant="ghost", color=_TEXT_WHITE, size="2"),
                        rx.button("⚙ إعدادات", on_click=ResumeState.toggle_settings, variant="ghost", color=_TEXT_WHITE, size="2"),
                        rx.button("✨ AI", on_click=ResumeState.toggle_input, variant="ghost", color=_TEXT_GOLD, size="2"),
                        rx.button("↶", on_click=ResumeState.undo, variant="ghost", color=_TEXT_WHITE, size="2"),
                        rx.button("↷", on_click=ResumeState.redo, variant="ghost", color=_TEXT_WHITE, size="2"),
                        rx.button("💾 Word", on_click=ResumeState.export_docx, variant="ghost", color=_TEXT_WHITE, size="2"),
                        rx.button("تنزيل PDF", on_click=ResumeState.export_pdf, bg=_TEXT_ORANGE, color=_TEXT_WHITE, size="2", font_weight="bold"),
                        width="100%",
                        align_items="center",
                        gap="4px",
                        padding="8px 12px",
                        flex_wrap="wrap",
                    ),
                    # Row 2: Advanced toggle
                    rx.flex(
                        rx.button(
                            rx.cond(
                                ResumeState.show_advanced_controls,
                                rx.text("▲ إخفاء الإعدادات المتقدمة", font_size="12px"),
                                rx.text("▼ إعدادات متقدمة ⚙️", font_size="12px"),
                            ),
                            on_click=ResumeState.toggle_advanced_controls,
                            variant="ghost",
                            color=_TEXT_GOLD,
                            size="2",
                            bg=_BG_INPUT,
                            border=f"1px solid {_BORDER}",
                            border_radius="6px",
                            padding="4px 12px",
                        ),
                        rx.spacer(),
                        rx.text(ResumeState.page_count, color="#666", font_size="11px"),
                        rx.text("صفحة", color="#666", font_size="11px"),
                        width="100%",
                        align_items="center",
                        padding="4px 12px",
                    ),
                    # Row 3: Advanced controls (collapsible)
                    rx.cond(
                        ResumeState.show_advanced_controls,
                        rx.grid(
                            rx.hstack(
                                rx.text("حجم الخط", color=_TEXT_MUTED, font_size="12px"),
                                rx.button("−", on_click=ResumeState.decrease_font_size, bg=_BG_INPUT, color=_TEXT_WHITE, size="2"),
                                rx.text(ResumeState.font_size, color=_TEXT_ORANGE, font_weight="bold", font_size="13px", min_width="35px", text_align="center"),
                                rx.button("+", on_click=ResumeState.increase_font_size, bg=_BG_INPUT, color=_TEXT_WHITE, size="2"),
                                spacing="2",
                                align_items="center",
                            ),
                            rx.hstack(
                                rx.text("الهوامش", color=_TEXT_MUTED, font_size="12px"),
                                rx.button("−", on_click=ResumeState.decrease_margin, bg=_BG_INPUT, color=_TEXT_WHITE, size="2"),
                                rx.text(ResumeState.margin, color=_TEXT_ORANGE, font_weight="bold", font_size="13px", min_width="35px", text_align="center"),
                                rx.button("+", on_click=ResumeState.increase_margin, bg=_BG_INPUT, color=_TEXT_WHITE, size="2"),
                                spacing="2",
                                align_items="center",
                            ),
                            rx.button("↺ إعادة ضبط", on_click=ResumeState.reset_controls, bg=_BG_INPUT, color=_TEXT_GOLD, size="2", border=f"1px solid #f59e0b"),
                            rx.button("📄 تحميل نموذج", on_click=ResumeState.load_sample, bg=_BG_INPUT, color=_TEXT_WHITE, size="2"),
                            columns="4",
                            spacing="4",
                            width="100%",
                            padding="8px 12px",
                        ),
                        rx.box(),
                    ),
                    bg=_BG_DARK,
                    width="100%",
                    spacing="0",
                ),

                # ===== RESUME PREVIEW =====
                resume_preview_bilingual(),
                width="100%",
                spacing="0",
            ),
            rx.box(),  # hidden when no resume
        ),

        # ===== RAW TEXT INPUT PANEL (collapsible) =====
        rx.cond(
            ResumeState.show_input,
            rx.vstack(
                rx.text("الصق معلوماتك هنا كاملةً", color=_TEXT_MUTED, font_size="12px"),
                rx.text_area(
                    value=ResumeState.raw_text,
                    on_change=ResumeState.set_raw_text,
                    placeholder="الصق سيرتك الذاتية هنا...",
                    width="100%",
                    min_height="150px",
                    bg=_BG_INPUT,
                    color=_TEXT_WHITE,
                    border=f"1px solid {_BORDER}",
                ),
                rx.hstack(
                    rx.button("⚡ توليد بالذكاء الاصطناعي", on_click=ResumeState.parse_resume_ai, bg=_TEXT_ORANGE, color=_TEXT_WHITE, size="3", font_weight="bold"),
                    rx.button("إغلاق", on_click=ResumeState.toggle_input, variant="ghost", color=_TEXT_MUTED, size="2"),
                    spacing="3",
                ),
                width="100%",
                max_width="600px",
                padding="16px",
                bg=_BG_CARD,
                border_radius="8px",
            ),
            rx.box(),
        ),

        # ===== API KEYS PANEL (collapsible) =====
        rx.cond(
            ResumeState.show_api_keys,
            rx.vstack(
                rx.text("🔑 إدارة مفاتيح API", color=_TEXT_WHITE, font_weight="bold", font_size="16px"),

                # Providers
                rx.foreach(
                    ResumeState.providers_list,
                    lambda p: rx.hstack(
                        rx.text(p["name"], color=_TEXT_WHITE, font_size="13px", min_width="120px"),
                        rx.text(f"({p['key_count']} مفاتيح)", color=_TEXT_MUTED, font_size="11px"),
                        rx.cond(
                            p["configured"],
                            rx.text("✓ مفعّل", color="green", font_size="12px"),
                            rx.text("✗ غير مفعّل", color="red", font_size="12px"),
                        ),
                        spacing="2",
                        width="100%",
                        padding="4px 0",
                        border_bottom=f"1px solid {_BORDER}",
                    ),
                ),

                # Stored keys
                rx.text("المفاتيح المخزنة:", color=_TEXT_MUTED, font_size="12px"),
                rx.foreach(
                    ResumeState.provider_keys_list,
                    lambda k: rx.hstack(
                        rx.text(k["provider_name"], color="#ccc", font_size="11px", min_width="80px"),
                        rx.text(k["masked"], color="#666", font_size="10px"),
                        rx.text(f"[{k['source']}]", color="#555", font_size="9px"),
                        rx.cond(
                            k["source"] == "file",
                            rx.button("🗑", on_click=lambda prov=k["provider"], idx=k["index"]: ResumeState.remove_api_key(prov, idx), size="1", bg="#3d1515", color="#ff6666"),
                            rx.text("env", color="#555", font_size="9px"),
                        ),
                        spacing="2",
                        width="100%",
                    ),
                ),

                # Add key
                rx.divider(border_color=_BORDER),
                rx.text("➕ إضافة مفتاح جديد:", color=_TEXT_GOLD, font_weight="bold", font_size="13px"),
                rx.hstack(
                    rx.select(
                        ["gemini", "openai", "anthropic", "openrouter", "groq", "deepseek", "mistral", "xai"],
                        value=ResumeState.new_key_provider,
                        on_change=ResumeState.set_new_key_provider,
                        size="2",
                        bg=_BG_INPUT,
                        color=_TEXT_WHITE,
                    ),
                    rx.input(
                        value=ResumeState.new_key_value,
                        on_change=ResumeState.set_new_key_value,
                        placeholder="ألصق المفتاح هنا...",
                        type="password",
                        size="2",
                        bg=_BG_INPUT,
                        color=_TEXT_WHITE,
                        border=f"1px solid #555",
                        flex="1",
                    ),
                    rx.button("إضافة", on_click=ResumeState.add_new_api_key, bg=_TEXT_ORANGE, color=_TEXT_WHITE, size="2", font_weight="bold"),
                    spacing="2",
                    width="100%",
                ),

                # Test Gemini
                rx.divider(border_color=_BORDER),
                rx.text("🔬 اختبار مفتاح Gemini:", color=_TEXT_GOLD, font_weight="bold", font_size="13px"),
                rx.hstack(
                    rx.input(
                        value=ResumeState.test_key_value,
                        on_change=ResumeState.set_test_key_value,
                        placeholder="ألصق مفتاح Gemini للاختبار...",
                        type="password",
                        size="2",
                        bg=_BG_INPUT,
                        color=_TEXT_WHITE,
                        border="1px solid #555",
                        flex="1",
                    ),
                    rx.button("اختبار", on_click=ResumeState.run_test_gemini_key, bg="#2563eb", color=_TEXT_WHITE, size="2", font_weight="bold"),
                    spacing="2",
                    width="100%",
                ),
                rx.cond(
                    ResumeState.test_key_result != "",
                    rx.text(ResumeState.test_key_result, color=_TEXT_WHITE, font_size="12px", padding="4px 8px"),
                    rx.text(""),
                ),

                # Key links
                rx.divider(border_color=_BORDER),
                rx.text("🔗 روابط الحصول على المفاتيح:", color=_TEXT_GOLD, font_weight="bold", font_size="13px"),
                rx.foreach(
                    ResumeState.key_links_list,
                    lambda kl: rx.hstack(
                        rx.text(kl["provider"], color="#ccc", font_size="11px", min_width="80px", text_transform="capitalize"),
                        rx.link(kl["label"], href=kl["url"], color="#3b82f6", font_size="11px", is_external=True),
                        spacing="2",
                        width="100%",
                        padding="2px 0",
                    ),
                ),

                rx.button("إغلاق", on_click=ResumeState.toggle_api_keys, variant="ghost", color=_TEXT_MUTED, size="2"),
                width="100%",
                max_width="550px",
                padding="20px",
                bg=_BG_DARK,
                border=f"1px solid {_BORDER}",
                border_radius="8px",
                spacing="3",
            ),
            rx.box(),
        ),

        # ===== SETTINGS PANEL (collapsible) =====
        rx.cond(
            ResumeState.show_settings,
            rx.vstack(
                rx.text("⚙️ الإعدادات", color=_TEXT_WHITE, font_weight="bold", font_size="16px"),
                rx.foreach(
                    ResumeState.providers_list,
                    lambda p: rx.hstack(
                        rx.text(p["name"], color=_TEXT_WHITE, font_size="13px"),
                        rx.cond(p["configured"], rx.text("✓", color="green", font_size="14px"), rx.text("✗", color="red", font_size="14px")),
                        spacing="3",
                    ),
                ),
                rx.button("إغلاق", on_click=ResumeState.toggle_settings, variant="ghost", color=_TEXT_MUTED, size="2"),
                width="100%",
                max_width="400px",
                padding="20px",
                bg=_BG_DARK,
                border=f"1px solid {_BORDER}",
                border_radius="8px",
            ),
            rx.box(),
        ),

        # ===== TEMPLATE SELECTOR (collapsible) =====
        rx.cond(
            ResumeState.show_templates,
            rx.vstack(
                rx.text("اختر القالب", color=_TEXT_WHITE, font_weight="bold", font_size="14px"),
                rx.foreach(
                    ResumeState.templates_list,
                    lambda t: rx.button(
                        t["name"],
                        on_click=lambda tid=t["id"]: ResumeState.set_template(tid),
                        bg=_BG_INPUT,
                        color=_TEXT_WHITE,
                        size="2",
                        width="100%",
                    ),
                ),
                rx.button("إغلاق", on_click=ResumeState.toggle_templates, variant="ghost", color=_TEXT_MUTED, size="2"),
                width="100%",
                max_width="300px",
                padding="16px",
                bg=_BG_DARK,
                border=f"1px solid {_BORDER}",
                border_radius="8px",
            ),
            rx.box(),
        ),

        # Page background
        bg="#2a2a2a",
        width="100%",
        min_height="100vh",
    )


app = rx.App()
app.add_page(index, route="/")

# Health check endpoint
from starlette.routing import Route
from starlette.responses import JSONResponse


async def health_check(request):
    return JSONResponse({"status": "ok", "app": "CVGen Pro", "version": "2.0.0", "runtime": "reflex"})


app._api.routes.insert(0, Route("/health", health_check, methods=["GET"]))
