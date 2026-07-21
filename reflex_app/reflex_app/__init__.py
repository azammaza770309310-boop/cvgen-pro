"""CVGen Pro — Reflex Application Entry Point

Run: reflex run
"""
from __future__ import annotations

import reflex as rx
from reflex_app.reflex_app.state import ResumeState
from reflex_app.reflex_app.resume_preview import resume_preview_bilingual


def index() -> rx.Component:
    """Main page: toolbar + resume preview."""
    return rx.box(
        # ===== TOOLBAR (dark) =====
        rx.box(
            # Row 1: nav
            rx.box(
                rx.button("✕", on_click=rx.redirect("/"), color_scheme="red", size="2"),
                rx.text("معاينة السيرة الذاتية", color="white", font_weight="bold", font_size="14px"),
                rx.button("القوالب", variant="ghost", color="white", size="2"),
                rx.button("الألوان", variant="ghost", color="white", size="2"),
                rx.button("تعديل المحتوى", variant="ghost", color="white", size="2"),
                rx.button("مساعد الذكاء ✨", variant="ghost", color="#fbbf24", size="2"),
                rx.button("↶", variant="ghost", color="white", size="2"),
                rx.button("↷", variant="ghost", color="white", size="2"),
                rx.button("💾 حفظ", variant="ghost", color="white", size="2"),
                rx.button(
                    "تنزيل PDF",
                    bg="#f97316",
                    color="white",
                    size="2",
                    font_weight="bold",
                ),
                display="flex",
                align_items="center",
                gap="8px",
                flex_wrap="wrap",
                padding="6px 12px",
                border_bottom="1px solid #333",
            ),
            # Row 2: steppers
            rx.box(
                rx.text("حجم الخط", color="#999", font_size="11px"),
                rx.button("−", on_click=ResumeState.decrease_font_size, bg="#2d2d2d", color="white", size="2"),
                rx.text(ResumeState.font_size, color="#f97316", font_size="14px", font_weight="bold", min_width="40px", text_align="center"),
                rx.button("+", on_click=ResumeState.increase_font_size, bg="#2d2d2d", color="white", size="2"),
                rx.text("الهوامش", color="#999", font_size="11px"),
                rx.button("−", on_click=ResumeState.decrease_margin, bg="#2d2d2d", color="white", size="2"),
                rx.text(ResumeState.margin, color="#f97316", font_size="14px", font_weight="bold", min_width="40px", text_align="center"),
                rx.button("+", on_click=ResumeState.increase_margin, bg="#2d2d2d", color="white", size="2"),
                rx.button("↺ إعادة ضبط", on_click=ResumeState.reset_controls, bg="#2d2d2d", color="#fbbf24", size="2", border="1px solid #f59e0b"),
                display="flex",
                align_items="center",
                gap="8px",
                flex_wrap="wrap",
                padding="6px 12px",
            ),
            # Row 3: page info
            rx.box(
                rx.text(
                    ResumeState.page_count,
                    color="#999",
                    font_size="12px",
                ),
                rx.text(" صفحة", color="#999", font_size="12px"),
                rx.spacer(),
                rx.button(
                    "📄 تحميل نموذج",
                    on_click=ResumeState.load_sample,
                    bg="#2d2d2d",
                    color="white",
                    size="2",
                ),
                display="flex",
                align_items="center",
                gap="8px",
                padding="6px 12px",
            ),
            bg="#1e1e1e",
            direction="rtl",
        ),

        # ===== RESUME PREVIEW =====
        resume_preview_bilingual(),

        width="100%",
        min_height="100vh",
    )


# ---------------------------------------------------------------------------
# App config
# ---------------------------------------------------------------------------

app = rx.App(
    theme=rx.theme(origin="dark"),
)
app.add_page(index, route="/")
