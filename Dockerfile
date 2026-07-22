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
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install bun (Reflex uses bun for frontend compilation)
RUN npm install -g bun

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Compile the Reflex frontend at build time.
# reflex init + reflex export must run from the project root (where rxconfig.py lives).
RUN reflex init
RUN reflex export --frontend-only

# Render sets $PORT at runtime (typically 10000) — this is the PUBLIC port
# that Render's health check scans. Reflex binds to it.
EXPOSE 10000

# Single-process production: Reflex ONLY.
# Runs from /app (project root) where rxconfig.py lives.
# All AI/PDF/DOCX logic runs natively inside the Reflex state.
CMD ["sh", "-c", "reflex run --env prod --backend-port ${PORT:-10000}"]
