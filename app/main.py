"""CVGen Pro — FastAPI application entry point.

Single entry point that registers all routers, serves Jinja2 HTML pages,
mounts static assets, and exposes the REST API.

Run: uvicorn app.main:app --host 0.0.0.0 --port $PORT
"""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

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


logger.info("CVGen Pro FastAPI app initialized — version %s", settings.app_version)
