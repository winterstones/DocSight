FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# ─── Development ───────────────────────────────────────────────────────────────
FROM base AS development

COPY requirements/ ./requirements/
RUN pip install --no-cache-dir -r requirements/development.txt

COPY . .

EXPOSE 8000

# ─── Production ────────────────────────────────────────────────────────────────
FROM base AS production

COPY requirements/ ./requirements/
RUN pip install --no-cache-dir -r requirements/base.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
