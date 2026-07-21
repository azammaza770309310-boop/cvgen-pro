FROM python:3.11-bookworm

# WeasyPrint system dependencies + Arabic fonts + Node.js for Reflex frontend
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

# Install bun (Reflex uses bun for frontend)
RUN npm install -g bun

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Compile Reflex frontend (generates .web/ directory)
RUN reflex init
RUN reflex export --frontend-only

# Render passes port via $PORT
ENV PORT=10000
EXPOSE 10000

# Run Reflex in production mode (serves both frontend + backend)
CMD ["reflex", "run", "--env", "prod"]
