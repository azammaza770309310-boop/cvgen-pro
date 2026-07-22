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
# If both fail, continue anyway (the backend can still serve the API).
RUN cd reflex_app && reflex init || true
RUN cd reflex_app && reflex export --frontend-only --no-prerender || reflex export --frontend-only || true

# Render sets $PORT at runtime (typically 10000) — this is the PUBLIC port
# that Render's health check scans. Reflex binds to it.
# The FastAPI API backend runs on internal port 3001 (not exposed to Render).
EXPOSE 10000

# Startup script: run FastAPI (API backend) + Reflex (UI) together.
# 1. Start FastAPI on port 3001 in the background (API for AI/PDF/DOCX).
# 2. Wait 3s for it to be ready.
# 3. Start Reflex in prod mode on $PORT — serves the compiled frontend + state.
# Reflex state calls FastAPI via httpx at http://localhost:3001/api/...
CMD sh -c "\
    uvicorn app.main:app --host 0.0.0.0 --port 3001 & \
    sleep 3 && \
    cd reflex_app && reflex run --env prod --backend-port ${PORT:-10000}"
