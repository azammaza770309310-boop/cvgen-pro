"""Reflex production configuration for Render deployment.

Render exposes a single port ($PORT, typically 10000). Reflex's production
mode needs both a frontend and backend — we solve this by:
  1. Running the Reflex backend on $PORT (the public-facing port).
  2. The Reflex frontend is compiled at build time (`reflex export --frontend-only`)
     and served as static files by the backend itself.
  3. FastAPI runs on a separate internal port (3001) as the API backend
     for AI parsing, PDF/DOCX export. Reflex state calls it via httpx.

This file is read by `reflex run` / `reflex export` at build and runtime.
"""
import os
import reflex as rx

# Render sets $PORT at runtime. Default to 10000 for local dev.
_port = os.environ.get("PORT", "10000")

# The FastAPI backend runs on this internal port (not exposed to Render's
# port scanner — only Reflex's $PORT is public). Reflex state calls it
# via httpx at http://localhost:3001/api/...
_api_port = os.environ.get("API_PORT", "3001")

config = rx.Config(
    app_name="reflex_app",
    backend_port=int(_port),
    frontend_port=int(_port),
    # api_url is what the BROWSER uses to reach the Reflex backend.
    # On Render, the public URL is relative (same origin).
    api_url=f"http://0.0.0.0:{_port}",
    # The FastAPI API backend URL (used by Reflex state via httpx, server-side).
    # This is an internal call — never exposed to the browser.
    backend_dialog_url=f"http://localhost:{_api_port}",
)
