# ══════════════════════════════════════════
# Dockerfile — Clawly-apify
# Python + Crawlee + Playwright + Chromium
# ══════════════════════════════════════════

FROM python:3.12-slim

# ── منع التفاعل أثناء البناء ──────────────
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ── مسار Chromium الثابت ──────────────────
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# ── اعتمادات النظام اللازمة لـ Playwright ─
RUN apt-get update && apt-get install -y \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── مجلد العمل ───────────────────────────
WORKDIR /app

# ── تثبيت المكتبات ────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── تثبيت Chromium في المسار الثابت ───────
RUN playwright install --with-deps chromium
RUN chmod -R 777 /ms-playwright

# ── نسخ الكود ────────────────────────────
COPY . .

# ── المنفذ ───────────────────────────────
EXPOSE 8000

# ── أمر التشغيل ──────────────────────────
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
