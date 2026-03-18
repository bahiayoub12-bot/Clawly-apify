# ══════════════════════════════════════════
# Dockerfile — my-crawler
# Python + Crawlee + Playwright + Chromium
# ══════════════════════════════════════════

# المرحلة 1: صورة الأساس
FROM python:3.12-slim

# ── منع التفاعل أثناء البناء ──────────────
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ── اعتمادات النظام اللازمة لـ Playwright ─
RUN apt-get update && apt-get install -y \
    # مكتبات المتصفح الأساسية
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
    # أدوات مساعدة
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── مجلد العمل ───────────────────────────
WORKDIR /app

# ── تثبيت المكتبات (طبقة منفصلة للكاش) ──
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── تثبيت Chromium عبر Playwright ────────
# هذا السطر هو "السر" الذي يجعل Crawlee يعمل
RUN playwright install --with-deps chromium

# ── نسخ الكود ────────────────────────────
COPY . .

# ── المنفذ ───────────────────────────────
EXPOSE 8000

# ── أمر التشغيل ──────────────────────────
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
