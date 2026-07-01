FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# ── Dependencies ──────────────────────────────────────────────────────────────
FROM base AS deps

COPY pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install -e ".[dev]" || pip install fastapi uvicorn pydantic pydantic-settings \
    sqlalchemy asyncpg alembic celery redis httpx structlog \
    prometheus-client prometheus-fastapi-instrumentator python-jose passlib bcrypt \
    gitpython unidiff networkx numpy scikit-learn tenacity

# ── Application ───────────────────────────────────────────────────────────────
FROM deps AS app

COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

ENV PYTHONPATH=/app/src

RUN mkdir -p /data/repos /data/graphs /data/evaluations /app/models \
    && chown -R appuser:appuser /app /data

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "code_impact.presentation.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ── Celery Worker ─────────────────────────────────────────────────────────────
FROM app AS worker

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD celery -A code_impact.infrastructure.queue.celery_app:celery_app inspect ping -t 5 || exit 1

CMD ["celery", "-A", "code_impact.infrastructure.queue.celery_app:celery_app", "worker", "--loglevel=info", "-Q", "analysis,prediction,embedding"]
