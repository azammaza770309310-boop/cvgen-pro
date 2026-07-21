"""CVGen Pro — Reflex Application Entry Point

Fixed UI: organized control panel with rx.grid, clean layout.
"""
from __future__ import annotations

import reflex as rx
from reflex_app.reflex_app.state import ResumeState
from reflex_app.reflex_app.resume_preview import resume_preview_bilingual


def index() -> rx.Component:
    """Main page: toolbar (grid) + resume preview."""
    return rx.box(
        # ===== TOOLBAR (dark, organized with grid) =====
        rx.vstack(
            # Row 1: Navigation bar
            rx.flex(
                rx.button("✕", on_click=rx.redirect("/"), color_scheme="red", size="2"),
                rx.text("معاينة السيرة الذاتية", color="white", font_weight="bold", font_size="14px"),
                rx.spacer(),
                rx.button("القوالب", variant="ghost", color="white", size="2"),
                rx.button("الألوان", variant="ghost", color="white", size="2"),
                rx.button("تعديل المحتوى", variant="ghost", color="white", size="2"),
                rx.button("مساعد الذكاء ✨", variant="ghost", color="#fbbf24", size="2"),
                rx.button("↶", variant="ghost", color="white", size="2"),
                rx.button("↷", variant="ghost", color="white", size="2"),
                rx.button("💾 حفظ", variant="ghost", color="white", size="2"),
                rx.button("تنزيل PDF", bg="#f97316", color="white", size="2", font_weight="bold"),
                width="100%",
                align_items="center",
                gap="6px",
                padding="8px 16px",
            ),
            # Row 2: Steppers in a 4-column grid
            rx.grid(
                # Font size stepper
                rx.hstack(
                    rx.text("حجم الخط", color="#999", font_size="12px"),
                    rx.button("−", on_click=ResumeState.decrease_font_size, bg="#2d2d2d", color="white", size="2"),
                    rx.text(ResumeState.font_size, color="#f97316", font_weight="bold", font_size="13px", min_width="35px", text_align="center"),
                    rx.button("+", on_click=ResumeState.increase_font_size, bg="#2d2d2d", color="white", size="2"),
                    spacing="6px",
                    align_items="center",
                ),
                # Margin stepper
                rx.hstack(
                    rx.text("الهوامش", color="#999", font_size="12px"),
                    rx.button("−", on_click=ResumeState.decrease_margin, bg="#2d2d2d", color="white", size="2"),
                    rx.text(ResumeState.margin, color="#f97316", font_weight="bold", font_size="13px", min_width="35px", text_align="center"),
                    rx.button("+", on_click=ResumeState.increase_margin, bg="#2d2d2d", color="white", size="2"),
                    spacing="6px",
                    align_items="center",
                ),
                # Reset button
                rx.button(
                    "↺ إعادة ضبط",
                    on_click=ResumeState.reset_controls,
                    bg="#2d2d2d",
                    color="#fbbf24",
                    size="2",
                    border="1px solid #f59e0b",
                ),
                # Page info + load sample
                rx.hstack(
                    rx.text(ResumeState.page_count, color="#999", font_size="12px"),
                    rx.text("صفحة", color="#999", font_size="12px"),
                    rx.spacer(),
                    rx.button("📄 تحميل نموذج", on_click=ResumeState.load_sample, bg="#2d2d2d", color="white", size="2"),
                    spacing="8px",
                    align_items="center",
                ),
                columns="4",
                spacing="4",
                width="100%",
                padding="8px 16px",
            ),
            # Toolbar container
            bg="#1e1e1e",
            width="100%",
            direction="rtl",
            spacing="0",
        ),

        # ===== RESUME PREVIEW =====
        resume_preview_bilingual(),

        width="100%",
        min_height="100vh",
    )


app = rx.App()
app.add_page(index, route="/")
