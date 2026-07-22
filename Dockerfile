FROM python:3.11-bookworm

# WeasyPrint system dependencies + Arabic fonts + Node.js (for Reflex frontend compilation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-noto-core \
    fonts-noto-extra \
    fonts-kacst \
    fonts-hosny-amiri \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install bun (Reflex uses bun for frontend compilation)
RUN npm install -g bun

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Compile the Reflex frontend at build time (produces static .web/ files).
# --frontend-only: only build the React frontend, not the backend.
# --no-prerender: skip SSR (avoids /_event URL parse errors during export).
# || true: if the first command fails, try without --no-prerender.
# If both fail, continue anyway (Reflex will recompile on first run).
RUN cd reflex_app && reflex init || true
RUN cd reflex_app && reflex export --frontend-only --no-prerender || reflex export --frontend-only || true

# Render sets $PORT at runtime (typically 10000) — this is the PUBLIC port
# that Render's health check scans. Reflex binds to it.
EXPOSE 10000

# Single-process production: Reflex ONLY.
# No FastAPI, no second server, no inter-process communication.
# All AI/PDF/DOCX logic runs natively inside the Reflex state via
# reflex_app/ai_handler.py and reflex_app/export_handler.py, which import
# app.ai.* and app.services.* directly (they are FastAPI-independent).
CMD ["sh", "-c", "cd reflex_app && reflex run --env prod --backend-port ${PORT:-10000}"]
