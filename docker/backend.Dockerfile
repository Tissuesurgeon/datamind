# syntax=docker/dockerfile:1.7
# DataMind backend (FastAPI).
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libmagic1 \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# ---- Deps stage --------------------------------------------------------- #
FROM base AS deps
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip wheel \
 && pip install -r /tmp/requirements.txt

# ---- Runtime ------------------------------------------------------------ #
FROM deps AS runtime
# 0G Storage: Node bridge (@0gfoundation/0g-storage-ts-sdk) — required when DATAMIND_OG_MOCK=0
COPY infra/og-bridge /app/infra/og-bridge
WORKDIR /app/infra/og-bridge
RUN npm ci --omit=dev --no-audit --no-fund \
    || npm install --omit=dev --no-audit --no-fund

COPY backend/ /app/backend/
COPY .env.example /app/.env.example
WORKDIR /app/backend

RUN mkdir -p /app/storage_local /app/hf-cache /app/checkpoints

EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=4s --retries=8 \
  CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
