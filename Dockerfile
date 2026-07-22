FROM python:3.11-bookworm

# WeasyPrint system dependencies + Arabic fonts + Node.js 22 (for Reflex frontend compilation)
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
# reflex init is NOT needed — rxconfig.py already exists in the repo.
# reflex export compiles the React frontend from the existing app code.
RUN reflex export --frontend-only

# Render sets $PORT at runtime (typically 10000) — this is the PUBLIC port
# that Render's health check scans. Reflex binds to it.
EXPOSE 10000

# Single-process production: Reflex ONLY.
# REFLEX_ENV=prod tells rxconfig.py to use same-origin api_url (empty string).
CMD ["sh", "-c", "REFLEX_ENV=prod reflex run --env prod --backend-port ${PORT:-10000}"]
