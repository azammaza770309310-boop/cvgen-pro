# CVGen Pro — Professional Resume Generator

A clean, production-ready **Python + FastAPI** resume generator. Cloud AI only — no Node.js, no local LLMs.

## Architecture

```
Browser
  ↓
FastAPI (single service)
  ├── Jinja2 HTML pages
  ├── REST API (/api/*)
  ├── AI Provider Manager → Gemini / OpenAI / Claude / OpenRouter / Groq / DeepSeek / Mistral / xAI
  ├── Resume Parser (whole-document AI + deterministic fallback)
  ├── Resume Normalizer (single normalize_resume_data pipeline)
  ├── ATS Analyzer (deterministic checks + optional AI)
  ├── Template Engine (10 templates, single registry)
  ├── PDF Exporter (WeasyPrint — matches preview)
  └── DOCX Exporter (python-docx)
```

**No** Next.js. **No** Node.js backend. **No** local AI. **No** silent local fallback.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Validation | Pydantic v2, Pydantic Settings |
| HTML | Jinja2 templates + HTML5 + Vanilla JS |
| PDF | WeasyPrint (HTML → PDF, same CSS as preview) |
| DOCX | python-docx |
| AI | Cloud providers only (httpx) |
| DB | SQLite-ready (architecture supports future DB) |

## Project Structure

```
cvgen-pro/
├── app/
│   ├── main.py                 # FastAPI entry point
│   ├── api/                    # REST routes (resume, ai, ats, export, templates, settings)
│   ├── core/                   # config, exceptions
│   ├── models/                 # unified ResumeData Pydantic models (single source of truth)
│   ├── schemas/                # request/response DTOs
│   ├── services/               # parser, normalizer, ats, template, pdf, docx
│   ├── ai/                     # AIProvider base + 8 providers + manager with failover
│   ├── templates/              # Jinja2 HTML (index.html)
│   ├── static/                 # css, js, fonts
│   ├── templates_render.py     # 10 template HTML renderers
│   └── utils/                  # arabic, dates, validation
├── tests/
├── requirements.txt
├── render.yaml
├── Dockerfile
├── .env.example
└── run.py
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your GEMINI_API_KEY
uvicorn app.main:app --reload --port 3000
```

Open http://localhost:3000

## Deployment (Render)

The `render.yaml` deploys this directly as a Python web service:

```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set your AI API keys as environment variables in the Render dashboard.

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Main UI |
| GET | `/health` | Health check |
| GET | `/api/resume/sample` | Sample resume (?lang=en\|ar\|bilingual) |
| POST | `/api/resume/parse` | Deterministic parse |
| POST | `/api/resume/normalize` | Normalize raw dict |
| POST | `/api/resume/save` | Save draft |
| GET | `/api/resume/{id}` | Load draft |
| POST | `/api/ai/parse` | AI whole-document parse |
| POST | `/api/ai/improve` | Improve a section |
| POST | `/api/ai/summary` | Generate summary |
| POST | `/api/ai/cover-letter` | Generate cover letter |
| POST | `/api/ats/analyze` | ATS analysis |
| POST | `/api/export/pdf` | WeasyPrint PDF |
| POST | `/api/export/docx` | Word document |
| GET | `/api/templates/` | List 10 templates |
| POST | `/api/templates/render` | Render resume to HTML |
| GET | `/api/settings/` | Provider metadata (safe, no keys) |

## 10 Templates

1. ATS Classic — single column, max ATS compatibility
2. Minimal Black — 30/70 split with timeline
3. Modern Sidebar — dark sidebar with photo placeholder
4. Corporate Slate — navy header + slate sidebar
5. Botanical Beige — warm beige with circle monogram
6. Lavender Minimal — soft lavender
7. Bilingual Teal-Gold — 50/50 mirror, teal + gold
8. Bilingual Navy — 50/50 mirror, navy + diamond bullets
9. Bilingual Peach — 50/50 mirror, boxed sections
10. International Bilingual — single column, stacked EN/AR

## AI Provider Failover

```
requested provider → backup provider → primary → any other configured
```

If all fail, a clear error is returned. No silent local fallback.

## Single Sources of Truth

- **ResumeData** → `app/models/resume.py`
- **AIManager** → `app/ai/manager.py`
- **Template registry** → `app/services/template_service.py`
- **Normalization** → `app/services/resume_normalizer.py`
- **PDF rendering** → `app/services/pdf_service.py` (uses template registry, same CSS as preview)
