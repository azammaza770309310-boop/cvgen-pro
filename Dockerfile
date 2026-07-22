FROM python:3.11-bookworm

# WeasyPrint system dependencies + Arabic fonts
# (No Node.js / bun needed — FastAPI serves its own Jinja2 + static frontend)
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
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render sets $PORT at runtime (typically 10000).
# We bind 0.0.0.0 so Render's port scan can detect the open port.
EXPOSE 10000

# Run the FastAPI app directly with uvicorn.
# (Replaces the broken `reflex run --env prod` which produced a blank page.)
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"
