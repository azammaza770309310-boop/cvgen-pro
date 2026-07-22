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

# In production (Render), the browser reaches the backend on the SAME origin.
# api_url must be a URL the browser can reach. Using 0.0.0.0 breaks browser
# WebSocket connections. In prod, use the public URL or empty string for
# same-origin. In dev, use localhost.
_is_prod = os.environ.get("REFLEX_ENV") == "prod" or os.environ.get("RENDER", "") != ""

if _is_prod:
    # Production: browser and backend share the same origin (Render proxy).
    # Use empty string so Reflex uses relative URLs (same-origin).
    _api_url = ""
else:
    # Dev: browser reaches backend via localhost.
    _api_url = f"http://localhost:{_port}"

config = rx.Config(
    app_name="reflex_app",
    backend_port=int(_port),
    frontend_port=int(_port),
    api_url=_api_url,
)
