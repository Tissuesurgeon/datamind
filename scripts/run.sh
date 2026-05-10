#!/usr/bin/env bash
# DataMind — full-stack dev orchestrator.
# Bootstraps Python venvs, applies migrations, seeds demo data,
# then starts backend + ai-engine + frontend (and Docker datastores
# unless --no-docker is passed).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# --------------------------------------------------------------------------- #
# Argument parsing                                                            #
# --------------------------------------------------------------------------- #
WITH_DOCKER=true
SEED_DEMO=true
WITH_FRONTEND=true
PY="${PY:-python3.12}"

usage() {
  cat <<EOF
Usage: ./scripts/run.sh [options]

  --no-docker    Don't start postgres/qdrant/redis via docker compose
  --no-seed      Skip seeding demo datasets
  --no-frontend  Skip starting the Next.js frontend
  -h, --help     Show this help

Env overrides:
  PY=/usr/bin/python3.12 ./scripts/run.sh
EOF
}

for arg in "$@"; do
  case "$arg" in
    --no-docker)   WITH_DOCKER=false ;;
    --no-seed)     SEED_DEMO=false ;;
    --no-frontend) WITH_FRONTEND=false ;;
    -h|--help)     usage; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; usage >&2; exit 1 ;;
  esac
done

# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #
log()   { printf "\033[1;36m[run]\033[0m %s\n" "$*"; }
warn()  { printf "\033[1;33m[warn]\033[0m %s\n" "$*"; }
error() { printf "\033[1;31m[err]\033[0m %s\n" "$*" >&2; }

ensure_python() {
  if ! command -v "$PY" >/dev/null 2>&1; then
    error "Python not found ($PY). Install Python 3.12 or set PY=/path/to/python."
    exit 1
  fi
}

ensure_venv() {
  local dir="$1"
  local stamp="$dir/.venv/.deps-installed"
  if [[ ! -d "$dir/.venv" ]]; then
    log "Creating venv at $dir/.venv"
    "$PY" -m venv "$dir/.venv"
  fi
  if [[ ! -f "$stamp" ]] || [[ "$dir/requirements.txt" -nt "$stamp" ]]; then
    log "Installing $dir Python deps…"
    "$dir/.venv/bin/pip" install -U pip wheel >/dev/null
    "$dir/.venv/bin/pip" install -r "$dir/requirements.txt"
    touch "$stamp"
  fi
}

ensure_env() {
  if [[ ! -f "$ROOT/.env" ]]; then
    log "Creating .env from .env.example (mock mode)"
    cp "$ROOT/.env.example" "$ROOT/.env"
  fi
  set -a
  # shellcheck disable=SC1091
  . "$ROOT/.env"
  set +a
}

# --------------------------------------------------------------------------- #
# Pre-flight                                                                  #
# --------------------------------------------------------------------------- #
ensure_python
ensure_env
mkdir -p "$ROOT/.run" "$ROOT/storage_local" "$ROOT/hf-cache" "$ROOT/checkpoints"

# --------------------------------------------------------------------------- #
# Docker datastores                                                           #
# --------------------------------------------------------------------------- #
DOCKER_CMD=""
if $WITH_DOCKER; then
  if ! command -v docker >/dev/null 2>&1; then
    warn "Docker not found. Skipping datastores. Set DATABASE_URL/QDRANT_URL/REDIS_URL or pass --no-docker."
  elif docker info >/dev/null 2>&1; then
    DOCKER_CMD="docker"
  elif command -v sudo >/dev/null 2>&1 && sudo -n docker info >/dev/null 2>&1; then
    warn "Using passwordless sudo for Docker (user '$USER' not in 'docker' group)."
    DOCKER_CMD="sudo docker"
  else
    warn "Docker is installed but not accessible by '$USER'."
    warn "  Fix once with:  sudo usermod -aG docker $USER && newgrp docker"
    warn "  Or rerun:       sudo ./scripts/run.sh"
    warn "  Or skip Docker: ./scripts/run.sh --no-docker  (you must provide reachable DATABASE_URL/QDRANT_URL/REDIS_URL)"
    if ! ${ALLOW_NO_DOCKER:-false}; then
      error "Aborting — Docker requested but unusable. Rerun with --no-docker to continue without datastores."
      exit 1
    fi
  fi

  if [[ -n "$DOCKER_CMD" ]]; then
    log "Starting Postgres + Qdrant + Redis via docker compose"
    $DOCKER_CMD compose -f "$ROOT/docker/docker-compose.yml" --project-directory "$ROOT" up -d postgres qdrant redis
    sleep 4
  fi
fi

# --------------------------------------------------------------------------- #
# Backend bootstrap                                                            #
# --------------------------------------------------------------------------- #
ensure_venv "$ROOT/backend"
log "Applying Alembic migrations"
( cd "$ROOT/backend" && ./.venv/bin/alembic upgrade head ) || warn "Alembic migration failed (DB may be down)"

if $SEED_DEMO; then
  log "Seeding demo datasets"
  ( cd "$ROOT/backend" && ./.venv/bin/python -m app.scripts.seed ) || warn "Seeding failed"
fi

# --------------------------------------------------------------------------- #
# AI engine                                                                    #
# --------------------------------------------------------------------------- #
ensure_venv "$ROOT/ai-engine"

# --------------------------------------------------------------------------- #
# Cleanup hook                                                                 #
# --------------------------------------------------------------------------- #
PIDS=()
cleanup() {
  log "Stopping background services…"
  for pid in "${PIDS[@]:-}"; do
    [[ -n "${pid:-}" ]] && kill "$pid" 2>/dev/null || true
  done
}
trap cleanup EXIT INT TERM

# --------------------------------------------------------------------------- #
# Launch services                                                              #
# --------------------------------------------------------------------------- #
log "Starting AI engine on :${AI_ENGINE_PORT:-8100}"
( cd "$ROOT/ai-engine" && ./.venv/bin/uvicorn datamind_ai.server:app \
    --host 0.0.0.0 --port "${AI_ENGINE_PORT:-8100}" \
    >"$ROOT/.run/ai-engine.log" 2>&1 ) &
PIDS+=($!)

log "Starting backend on :${BACKEND_PORT:-8000}"
( cd "$ROOT/backend" && ./.venv/bin/uvicorn app.main:app \
    --host 0.0.0.0 --port "${BACKEND_PORT:-8000}" --reload \
    >"$ROOT/.run/backend.log" 2>&1 ) &
PIDS+=($!)

if $WITH_FRONTEND; then
  if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
    log "Installing frontend dependencies (first run)"
    ( cd "$ROOT/frontend" && npm install )
  fi
  log "Starting frontend on :3000"
  ( cd "$ROOT/frontend" && npm run dev >"$ROOT/.run/frontend.log" 2>&1 ) &
  PIDS+=($!)
fi

log "DataMind is up. Logs in $ROOT/.run/*.log"
log "  Frontend  : http://localhost:3000"
log "  Backend   : http://localhost:${BACKEND_PORT:-8000}/docs"
log "  AI Engine : http://localhost:${AI_ENGINE_PORT:-8100}/docs"
log "Press Ctrl+C to stop."

wait
