# syntax=docker/dockerfile:1.7
# DataMind AI engine (FastAPI sidecar).
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HUB_DISABLE_TELEMETRY=1

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ---- Deps --------------------------------------------------------------- #
FROM base AS deps
COPY ai-engine/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip wheel \
 && pip install -r /tmp/requirements.txt

# ---- Runtime ------------------------------------------------------------ #
FROM deps AS runtime
COPY ai-engine/ /app/ai-engine/
WORKDIR /app/ai-engine
ENV PYTHONPATH=/app/ai-engine/src

RUN mkdir -p /app/hf-cache /app/checkpoints

EXPOSE 8100
HEALTHCHECK --interval=15s --timeout=4s --retries=10 \
  CMD curl -fsS http://localhost:8100/healthz || exit 1

CMD ["uvicorn", "datamind_ai.server:app", "--host", "0.0.0.0", "--port", "8100"]
