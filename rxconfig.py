"""Reflex production configuration for Render deployment.

Single-process architecture: Reflex runs alone (no FastAPI server).
All AI/PDF/DOCX logic runs natively inside the Reflex state.

The app_name is "reflex_app" — Reflex resolves this to the module
"reflex_app.reflex_app" (app_name + "." + app_name), which maps to
reflex_app/reflex_app/__init__.py containing `app = rx.App()`.
"""
import os
import reflex as rx

# Render sets $PORT at runtime. Default to 3002 for local dev.
_port = os.environ.get("PORT", "3002")

# Use a valid absolute URL at ALL times — SSR/prerender needs it during build.
# On Render, the RENDER env var is set automatically.
if os.environ.get("RENDER"):
    # Production: use the public Render URL (valid absolute HTTPS URL).
    _api_url = "https://cvgen-pro.onrender.com"
else:
    # Local dev / Docker build: use localhost (valid absolute URL).
    _api_url = f"http://localhost:{_port}"

config = rx.Config(
    app_name="reflex_app",
    backend_port=int(_port),
    frontend_port=int(_port),
    api_url=_api_url,
)
