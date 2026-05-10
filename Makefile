# =============================================================================
# DataMind — top-level developer convenience commands.
# =============================================================================

ROOT       := $(shell pwd)
COMPOSE    := docker compose -f docker/docker-compose.yml --project-directory $(ROOT)

.PHONY: help install dev backend ai-engine frontend contracts seed test \
        compose-up compose-down compose-logs migrate fmt lint clean

help: ## Show this help.
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ---- Bootstrap -------------------------------------------------------------

install: ## Install backend, ai-engine and frontend dependencies locally.
	cd backend     && python3.12 -m venv .venv && ./.venv/bin/pip install -U pip && ./.venv/bin/pip install -r requirements.txt
	cd ai-engine   && python3.12 -m venv .venv && ./.venv/bin/pip install -U pip && ./.venv/bin/pip install -r requirements.txt
	cd frontend    && npm install
	cd infra/og-bridge && npm install
	@echo "Done. Next: cp .env.example .env && make dev"

# ---- Local dev (single-script orchestrator) -------------------------------

dev: ## Run the full stack via scripts/run.sh (mock-by-default).
	./scripts/run.sh

# ---- Single-service runs ---------------------------------------------------

backend: ## Run only the FastAPI backend.
	cd backend && ./.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

ai-engine: ## Run only the AI engine FastAPI service.
	cd ai-engine && ./.venv/bin/uvicorn datamind_ai.server:app --host 0.0.0.0 --port 8100 --reload

frontend: ## Run only the Next.js frontend.
	cd frontend && npm run dev

# ---- Contracts -------------------------------------------------------------

contracts: ## Build and test Foundry contracts (installs forge-std on first run).
	cd smart-contracts && \
		[ -d lib/forge-std ] || forge install foundry-rs/forge-std --no-commit && \
		forge build && forge test -vv

deploy-contracts: ## Deploy DatasetRegistry + LicenseRegistry to Galileo testnet.
	cd smart-contracts && forge script script/Deploy.s.sol:Deploy --rpc-url $$OG_EVM_RPC --private-key $$OG_PRIVATE_KEY --broadcast

# ---- Database --------------------------------------------------------------

migrate: ## Apply Alembic migrations.
	cd backend && ./.venv/bin/alembic upgrade head

seed: ## Load demo datasets (Crypto Twitter Sentiment, etc.).
	cd backend && ./.venv/bin/python -m app.scripts.seed

# ---- Docker compose --------------------------------------------------------

compose-up: ## Start full stack via docker compose.
	$(COMPOSE) up -d --build

compose-down: ## Stop docker stack and remove volumes.
	$(COMPOSE) down -v

compose-logs: ## Follow logs of all services.
	$(COMPOSE) logs -f

# ---- QA --------------------------------------------------------------------

test: ## Run backend, ai-engine and contracts tests.
	cd backend     && ./.venv/bin/pytest -q || true
	cd ai-engine   && ./.venv/bin/pytest -q || true
	cd smart-contracts && forge test -vv || true

fmt: ## Format Python and TS sources.
	cd backend     && ./.venv/bin/ruff format . && ./.venv/bin/ruff check --fix .
	cd ai-engine   && ./.venv/bin/ruff format . && ./.venv/bin/ruff check --fix .
	cd frontend    && npm run lint -- --fix || true

lint: ## Lint all sources.
	cd backend     && ./.venv/bin/ruff check .
	cd ai-engine   && ./.venv/bin/ruff check .
	cd frontend    && npm run lint || true

clean: ## Remove venvs, caches, build artifacts.
	rm -rf backend/.venv ai-engine/.venv frontend/.next frontend/node_modules
	rm -rf smart-contracts/out smart-contracts/cache
	rm -rf hf-cache checkpoints storage_local logs .run
