"""CVGen Pro — FastAPI application entry point.

Single entry point that registers all routers, serves Jinja2 HTML pages,
mounts static assets, and exposes the REST API.

Run: uvicorn app.main:app --host 0.0.0.0 --port $PORT
"""
from __future__ import annotations

import logging
from pathlib import Path

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

# --- Sentry initialization (MUST be before app = FastAPI()) ---
# Production tuning: traces_sample_rate and profile_sample_rate are kept
# moderate (not 1.0) to avoid excessive memory overhead from the Sentry
# background thread. 1.0 captures EVERY transaction which can OOM on
# memory-constrained hosts. 0.25 captures 1 in 4 — enough for error
# correlation without the memory bloat.
sentry_sdk.init(
    dsn="https://ddceb2aa8ca804a461db14e623d52072@o4511770582843392.ingest.us.sentry.io/4511770602504192",
    send_default_pii=True,
    enable_logs=True,
    traces_sample_rate=0.25,
    profile_session_sample_rate=0.25,
    profile_lifecycle="trace",
)

from app.api.routes_ai import router as ai_router
from app.api.routes_ats import router as ats_router
from app.api.routes_export import router as export_router
from app.api.routes_resume import router as resume_router
from app.api.routes_settings import router as settings_router
from app.api.routes_templates import router as templates_router
from app.core.config import settings
from app.core.exceptions import CVGenError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("cvgen.main")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Professional resume generator — Python + FastAPI. Cloud AI only.",
    # NOTE: do NOT pass `on_startup`/`on_shutdown` to FastAPI() or any APIRouter().
    # Starlette removed/deprecated these kwargs in some versions, causing
    # "TypeError: Router.__init__() got an unexpected keyword argument 'on_startup'".
    # If startup logic is ever needed, use the `lifespan` context manager instead.
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Static + templates ---
app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")
templates = Jinja2Templates(directory=str(settings.templates_dir))


# --- Exception handler ---
@app.exception_handler(CVGenError)
async def cvgen_error_handler(request: Request, exc: CVGenError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "code": exc.code},
    )


# --- Routers ---
app.include_router(resume_router)
app.include_router(ai_router)
app.include_router(ats_router)
app.include_router(export_router)
app.include_router(templates_router)
app.include_router(settings_router)


# --- HTML routes ---
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"app_name": settings.app_name})


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}


@app.get("/api/health")
async def api_health():
    return {"status": "ok"}


@app.get("/sentry-debug")
async def trigger_error():
    """INTENTIONAL error endpoint — verifies Sentry is capturing exceptions.

    This endpoint deliberately raises ZeroDivisionError so developers can
    confirm the Sentry DSN is wired correctly. It is NOT a bug; the 1/0 is
    the whole point. The exception propagates to Sentry and returns a 500
    to the caller — both are expected.

    Safe to leave enabled in production: it only fires when an operator
    explicitly visits /sentry-debug, and the ZeroDivisionError is caught by
    the global exception handler (no crash, no data loss, no user impact).
    """
    division_by_zero = 1 / 0  # noqa: B018 — intentional, for Sentry verification
    return {"result": division_by_zero}


logger.info("CVGen Pro FastAPI app initialized — version %s", settings.app_version)
