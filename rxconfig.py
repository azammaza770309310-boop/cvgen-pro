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

# During Docker BUILD (reflex export), REFLEX_ENV is not set yet (it's only
# set in CMD at runtime). So we need a URL that works for BOTH:
#   1. Build time: SSR/prerender needs a valid absolute URL to resolve /_event
#   2. Runtime: browser needs same-origin for WebSocket
#
# Solution: use a placeholder absolute URL during build, and override at
# runtime via the REFLEX_API_URL environment variable.
#
# At Docker build time: api_url = http://localhost:3002 (valid absolute URL,
#   SSR can resolve /_event without ERR_INVALID_URL)
# At Render runtime: CMD sets REFLEX_API_URL to empty string → same-origin
_api_url = os.environ.get("REFLEX_API_URL", f"http://localhost:{_port}")

config = rx.Config(
    app_name="reflex_app",
    backend_port=int(_port),
    frontend_port=int(_port),
    api_url=_api_url,
)
