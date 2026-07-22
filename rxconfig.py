"""Reflex production configuration for Render deployment.

Single-process architecture: Reflex runs alone (no FastAPI server).
All AI/PDF/DOCX logic runs natively inside the Reflex state via
reflex_app/ai_handler.py and reflex_app/export_handler.py, which import
app.ai.* and app.services.* directly (FastAPI-independent modules).

Render exposes a single port ($PORT, typically 10000). Reflex binds to it
for both the frontend (compiled React) and the backend (state handlers).
"""
import os
import reflex as rx

# Render sets $PORT at runtime. Default to 10000 for local dev.
_port = os.environ.get("PORT", "10000")

config = rx.Config(
    app_name="reflex_app",
    backend_port=int(_port),
    frontend_port=int(_port),
    # api_url is what the BROWSER uses to reach the Reflex backend.
    # On Render, the public URL is relative (same origin).
    api_url=f"http://0.0.0.0:{_port}",
)
