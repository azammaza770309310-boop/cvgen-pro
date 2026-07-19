# CVGen Pro — Architecture Migration Report

## Overview

CVGen Pro has been fully migrated to a clean, production-ready **Python + FastAPI** architecture. The entire application runs as a single Python service — no Node.js, no Next.js, no local AI models.

**Status: ✅ Complete and verified**

---

## 1. Files Removed (Legacy Architecture)

The previous Next.js environment at `/home/z/my-project` was stopped (Next.js dev server killed on port 3000). The new Python project lives at `/home/z/audit` with zero Node.js dependencies. No legacy Python files were carried over — this is a clean rebuild.

Removed/deprecated concepts:
- Next.js App Router (`src/app/page.tsx`, API routes)
- Node.js backend / Express / NestJS
- ReportLab PDF architecture (replaced by WeasyPrint)
- Duplicate ResumeData models (consolidated to one)
- Duplicate parser logic (consolidated to one normalizer)
- Duplicate template registries (consolidated to one)
- Local AI / Ollama / LM Studio / Hugging Face local inference
- Silent local-AI fallback

---

## 2. Files Created

### Core Application (`app/`)

| File | Purpose |
|------|---------|
| `app/__init__.py` | Package marker |
| `app/main.py` | **FastAPI entry point** — registers routers, mounts static, serves Jinja2, exception handler |
| `app/core/config.py` | Pydantic Settings — all API keys server-side, `get_provider_keys()`, path helpers |
| `app/core/exceptions.py` | `CVGenError`, `AIProviderError`, `AIAllProvidersFailedError`, `ResumeValidationError`, etc. |
| `app/models/resume.py` | **Unified ResumeData** — the single source of truth (PersonalInfo, ExperienceItem, EducationItem, SkillItem, LanguageItem, ProjectItem, CertificationItem, + `sample_resume()`) |
| `app/models/ai.py` | AI request/response models |
| `app/models/settings.py` | Settings response models |
| `app/schemas/ats.py` | ATS request/response DTOs |
| `app/schemas/export.py` | Export request DTO |
| `app/utils/arabic.py` | `contains_arabic()`, `detect_lang()`, `normalize_arabic()` |
| `app/utils/dates.py` | `split_date_range()`, `normalize_year()` |
| `app/utils/validation.py` | Contact extractors (email/phone/linkedin/github/website), `is_contact_token()`, section alias dictionary (EN+AR), `detect_section()`, `dedup_strings()` |

### AI Layer (`app/ai/`)

| File | Purpose |
|------|---------|
| `app/ai/base.py` | `AIProvider` ABC — `parse_resume`, `improve_resume`, `generate_summary`, `analyze_ats`, `generate_cover_letter` + key rotation |
| `app/ai/prompts.py` | Shared prompt builders (whole-document parse, improve, summary, ATS, cover letter) |
| `app/ai/json_utils.py` | `extract_json()` — handles fenced blocks, embedded JSON |
| `app/ai/gemini.py` | Google Gemini 2.0 Flash (primary) |
| `app/ai/openai.py` | OpenAI GPT-4o mini |
| `app/ai/anthropic.py` | Anthropic Claude 3.5 Sonnet |
| `app/ai/openrouter.py` | OpenRouter (multi-model router) |
| `app/ai/groq.py` | Groq Llama 3.3 70B |
| `app/ai/compat.py` | DeepSeek, Mistral, xAI (OpenAI-compatible) |
| `app/ai/manager.py` | **AIManager** — provider registry, failover chain (requested → backup → primary → any configured), `_run_with_failover()` |

### Services (`app/services/`)

| File | Purpose |
|------|---------|
| `app/services/resume_parser.py` | Hybrid: `parse_resume_ai()` (whole-doc AI) + `parse_resume_deterministic()` (rule-based fallback with two-pass experience grouping) |
| `app/services/resume_normalizer.py` | **`normalize_resume_data()`** — single normalization pipeline: Pydantic validation → contact validation → dedup → strip contact from skill lists |
| `app/services/ats_service.py` | `analyze_resume()` — 10 deterministic check categories + optional AI layer, 0-100 score, A-F grade |
| `app/services/template_service.py` | **Template registry** — 10 `TemplateDef` entries, `list_templates()`, `render_template()` |
| `app/services/pdf_service.py` | WeasyPrint — uses same template renderer + CSS as preview |
| `app/services/docx_service.py` | python-docx — EN/AR/bilingual with RTL support |

### Template Renderers

| File | Purpose |
|------|---------|
| `app/templates_render.py` | 10 HTML renderers (one function per template) + shared helpers (`bullets_for`, `title_for`, `date_range`, etc.) |

### API Routes (`app/api/`)

| File | Endpoints |
|------|-----------|
| `app/api/routes_resume.py` | `GET /api/resume/sample`, `POST /api/resume/parse`, `POST /api/resume/normalize`, `POST /api/resume/save`, `GET /api/resume/{id}`, `GET /api/resume/` |
| `app/api/routes_ai.py` | `POST /api/ai/parse`, `POST /api/ai/improve`, `POST /api/ai/summary`, `POST /api/ai/cover-letter` |
| `app/api/routes_ats.py` | `POST /api/ats/analyze` |
| `app/api/routes_export.py` | `POST /api/export/pdf`, `POST /api/export/docx` |
| `app/api/routes_templates.py` | `GET /api/templates/`, `POST /api/templates/render` |
| `app/api/routes_settings.py` | `GET /api/settings/`, `GET /api/settings/providers`, `POST /api/settings/test-key` |

### Frontend

| File | Purpose |
|------|---------|
| `app/templates/index.html` | Jinja2 main UI — 8 tabs (Paste CV, Personal, Experience, Education, Skills, Extra, Template, ATS), preview panel, providers modal |
| `app/static/css/app.css` | Application UI styles (header, tabs, forms, template grid, ATS results, modal, toast, responsive) |
| `app/static/css/templates.css` | **Shared CSS for all 10 templates + A4 page simulation** (used by both preview and WeasyPrint) |
| `app/static/js/app.js` | Vanilla JS — state management, form binding, experience/education editors, preview rendering, live page count, ATS analysis, PDF/DOCX export, sample loading |

### Deployment & Config

| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies (fastapi, uvicorn, pydantic, jinja2, weasyprint, python-docx, httpx) |
| `render.yaml` | Render deployment config — Python web service, `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| `Dockerfile` | Python 3.11-slim + WeasyPrint system deps |
| `.env.example` | Environment variable template (all API keys server-side) |
| `.gitignore` | Python ignores |
| `README.md` | Full documentation |
| `run.py` | `python run.py` entry point |
| `pytest.ini` | pytest config (asyncio auto mode) |
| `start_server.py` | Double-fork daemonizer (for this sandbox) |

### Tests

| File | Purpose |
|------|---------|
| `tests/test_cvgen.py` | 33 tests covering all layers |

---

## 3. Files Migrated

All logic from the previous architecture was reimplemented (not copied) in Python:

- **ResumeData model** → `app/models/resume.py` (Pydantic v2, single source of truth)
- **AI parser with key rotation** → `app/ai/` (8 providers + manager with failover)
- **Rule-based parser** → `app/services/resume_parser.py` (two-pass experience grouping, word-bounded date regex)
- **Normalizer** → `app/services/resume_normalizer.py` (single pipeline)
- **ATS analyzer** → `app/services/ats_service.py` (10 checks + AI layer)
- **10 templates** → `app/templates_render.py` + `app/services/template_service.py`
- **WeasyPrint PDF** → `app/services/pdf_service.py` (shares CSS with preview)
- **DOCX export** → `app/services/docx_service.py`
- **Frontend** → Jinja2 + vanilla JS (same UI features: editor, preview, page count, ATS, export)

---

## 4. Dependencies Removed

- Node.js / npm / Bun
- Next.js 16
- React
- Express / NestJS
- ReportLab (replaced by WeasyPrint)
- Any local AI runtime (Ollama, LM Studio, Hugging Face local inference)
- TypeScript

---

## 5. Dependencies Added (Python)

```
fastapi==0.128.0
uvicorn[standard]==0.32.0
pydantic==2.12.5
pydantic-settings==2.5.2
jinja2==3.1.6
weasyprint==68.0
python-docx==1.1.2
httpx==0.27.2
python-multipart==0.0.12
```

Dev: `pytest`, `pytest-asyncio`

---

## 6. API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Main UI (Jinja2) |
| GET | `/health` | Health check |
| GET | `/api/resume/sample?lang=en\|ar\|bilingual` | Sample resume |
| POST | `/api/resume/parse` | Deterministic parse |
| POST | `/api/resume/normalize` | Normalize raw dict |
| POST | `/api/resume/save` | Save draft (in-memory, DB-ready) |
| GET | `/api/resume/{id}` | Load draft |
| GET | `/api/resume/` | List saved drafts |
| POST | `/api/ai/parse` | AI whole-document parse |
| POST | `/api/ai/improve` | Improve a section |
| POST | `/api/ai/summary` | Generate summary |
| POST | `/api/ai/cover-letter` | Generate cover letter |
| POST | `/api/ats/analyze` | ATS analysis (deterministic + optional AI) |
| POST | `/api/export/pdf` | WeasyPrint PDF (Unicode filenames) |
| POST | `/api/export/docx` | Word document (RTL support) |
| GET | `/api/templates/` | List 10 templates (metadata) |
| POST | `/api/templates/render` | Render resume to HTML |
| GET | `/api/settings/` | Provider metadata (safe — no keys) |
| GET | `/api/settings/providers` | Providers alias |
| POST | `/api/settings/test-key` | Check if provider configured |

---

## 7. AI Provider Architecture

```
FastAPI
  ↓
AIManager (app/ai/manager.py)
  ├── _failover_chain(): requested → backup → primary → any configured
  ├── _run_with_failover(): tries each provider, rotates keys, collects errors
  └── _instantiate(): picks provider class from PROVIDER_CLASSES registry
       ↓
AIProvider (ABC)  ← implemented by:
  ├── GeminiProvider      (Google Gemini 2.0 Flash)  — primary
  ├── OpenAIProvider      (GPT-4o mini)
  ├── AnthropicProvider   (Claude 3.5 Sonnet)
  ├── OpenRouterProvider  (multi-model router)        — backup
  ├── GroqProvider        (Llama 3.3 70B)
  ├── DeepSeekProvider    (DeepSeek Chat)
  ├── MistralProvider     (Mistral Large)
  └── XAIProvider         (Grok 2)
```

**Key features:**
- API keys read from environment variables only — never exposed to frontend
- `/api/settings/` returns only safe metadata (`configured: true/false`, never the key)
- Multi-key rotation per provider (`GEMINI_BACKUP_KEYS` for comma-separated backups)
- Failover chain: if primary fails, tries backup, then any other configured provider
- **No local AI fallback.** If all cloud providers fail, a clear `AIAllProvidersFailedError` is returned
- If no AI key is configured at all, the deterministic rule-based parser is used (with a logged warning)

---

## 8. Render Deployment Configuration

`render.yaml`:
```yaml
services:
  - type: web
    name: cvgen-pro
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: GEMINI_API_KEY      # set in Render dashboard
      - key: OPENAI_API_KEY      # optional
      - key: ANTHROPIC_API_KEY   # optional
      - key: OPENROUTER_API_KEY  # optional backup
      - key: GROQ_API_KEY        # optional
      - key: DEFAULT_AI_PROVIDER
        value: gemini
      - key: BACKUP_AI_PROVIDER
        value: openrouter
```

**Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Requirements:** Python only. No Node.js, npm, Bun, GPU, CUDA, Ollama, or local LLM.

---

## 9. Test Results

```
$ python -m pytest tests/ -q
.................................                                        [100%]
33 passed in 2.72s
```

```
$ python -m compileall app -q
(exit 0 — clean)
```

**33 tests covering:**
- ✅ FastAPI startup + `/health` + `/` HTML page
- ✅ ResumeData schema validation (defaults, coercion, summary dict)
- ✅ Normalizer (strips contact from skills, dedup)
- ✅ English CV parsing (contact, skills-no-contact, experience grouped, education, languages)
- ✅ Arabic CV parsing (contact, clean skills)
- ✅ Multiple jobs + multiple education records
- ✅ API parse endpoint (success + empty-text 400)
- ✅ ATS analysis (score, grade, checks) + API endpoint
- ✅ All 10 templates registered + render HTML
- ✅ Templates API (list + render)
- ✅ PDF export (bytes + `%PDF` magic + API endpoint)
- ✅ DOCX export (bytes + `PK` magic + API endpoint)
- ✅ AI parse without key (graceful deterministic fallback)
- ✅ AI unknown provider (no crash)
- ✅ A4 page CSS present
- ✅ Sample endpoint (en/ar/bilingual)

---

## 10. Browser Verification (Agent Browser)

End-to-end verification performed with Agent Browser against `http://localhost:3000`:

| Check | Result |
|-------|--------|
| Page loads (no blank screen, no hydration crash) | ✅ |
| 8 editor tabs render (Paste CV, Personal, Experience, Education, Skills, Extra, Template, ATS) | ✅ |
| Bilingual sample auto-loads on page open | ✅ |
| Preview renders with A4 page simulation | ✅ |
| **Live page count works** ("Page 1 of 2" on Modern Sidebar template) | ✅ |
| Template grid shows all 10 templates | ✅ |
| Template switching updates preview live | ✅ |
| Deterministic parse extracts email correctly | ✅ |
| Experience entries grouped correctly (2 jobs = 2 entries) | ✅ |
| ATS analysis returns score + grade + checks + recommendations | ✅ |
| PDF download endpoint returns valid PDF (200, `application/pdf`) | ✅ |
| DOCX download endpoint returns valid DOCX (200, Word MIME) | ✅ |
| Providers modal shows safe metadata (no keys) | ✅ |
| Browser console: no errors | ✅ |
| Server log: all 200 OK (only harmless 404 for favicon + 403 for stale Next.js HMR) | ✅ |

---

## 11. Confirmation

✅ The application runs as **ONE Python FastAPI service** on port 3000.
✅ **No Node.js** — the Next.js dev server was stopped; the Python app serves everything.
✅ **No local AI** — all semantic processing uses cloud providers (Gemini/OpenAI/Claude/OpenRouter/Groq/DeepSeek/Mistral/xAI). No Ollama, no LM Studio, no Hugging Face local inference.
✅ **No silent local fallback** — if all cloud providers fail, a clear `AIAllProvidersFailedError` is raised.
✅ **Single source of truth** for ResumeData (`app/models/resume.py`), AIManager (`app/ai/manager.py`), template registry (`app/services/template_service.py`), normalization (`app/services/resume_normalizer.py`), and PDF rendering (`app/services/pdf_service.py`).
✅ **PDF matches preview** — both use the same `templates.css` and the same template renderers.
✅ Deployable directly to Render as a Python web service.

---

## Final Production Flow

```
Browser
  ↓
FastAPI (single Python service, port 3000)
  ↓
Cloud AI Provider Manager (AIManager + failover)
  ↓
Gemini / OpenAI / Claude / OpenRouter / Groq / DeepSeek / Mistral / xAI
  ↓
Pydantic ResumeData (validated + normalized + deduplicated)
  ↓
Structured Editor (Jinja2 + Vanilla JS)
  ↓
10 Templates (single registry)
  ↓
A4 Live Preview + Live Page Count
  ↓
WeasyPrint PDF / python-docx DOCX
```

**Python + FastAPI + Pydantic + Jinja2 + Vanilla JavaScript + Cloud AI APIs + WeasyPrint + python-docx.**
