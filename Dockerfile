FROM python:3.11-bookworm

# WeasyPrint system dependencies + Arabic fonts
# ملاحظة: fonts-noto-arabic غير متوفر في bookworm، نستخدم fonts-arabeyes أو fonts-kacst
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
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render يمرر الـ port عبر متغير البيئة $PORT
ENV PORT=10000
EXPOSE 10000

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}
