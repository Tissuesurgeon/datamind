# Infrastructure

## og-bridge

Node sidecar that wraps `@0gfoundation/0g-storage-ts-sdk` for storage uploads + downloads ([0G Storage](https://build.0g.ai/storage/)).
The Python backend shells to it via `infra/og-bridge/cli.mjs`. In mock mode it
returns deterministic hashes so the demo runs without npm install.

```bash
cd infra/og-bridge
npm install
node cli.mjs upload --file ../../scripts/seed/crypto_twitter_sentiment.csv
```

## Deployment notes

### Vercel (frontend)

1. Import the repo, set the root to `frontend/`.
2. Build command: `npm run build`. Output: `.next`.
3. Environment variables:
   - `NEXT_PUBLIC_API_BASE` — public URL of the backend (`https://api.datamind.app/api/v1`)
   - `NEXT_PUBLIC_WS_BASE` — public WS URL (`wss://api.datamind.app/ws`)
   - `NEXT_PUBLIC_PRIVY_APP_ID` — leave unset for mock wallet
   - `NEXT_PUBLIC_CHAIN_ID` — `16602`

### Railway (backend + AI engine)

Two services from the same repo:

| Service    | Dockerfile                       | Healthcheck       | Port |
|------------|----------------------------------|-------------------|------|
| backend    | `docker/backend.Dockerfile`      | `/health`         | 8000 |
| ai-engine  | `docker/ai-engine.Dockerfile`    | `/healthz`        | 8100 |

Add Postgres, Redis, and Qdrant plugins (or external services) and inject
their URLs into both services. Backend env:

- `DATABASE_URL` (Railway PG with `+asyncpg` driver)
- `REDIS_URL`, `QDRANT_URL`
- `AI_ENGINE_URL` — `https://ai-engine.up.railway.app`
- `BACKEND_CORS_ORIGINS=https://app.datamind.app`
- `OG_EVM_RPC`, `OG_INDEXER_RPC`, `OG_PRIVATE_KEY`, `DATAMIND_OG_MOCK=0` for live 0G

### Docker Compose (local prod-style)

```bash
make compose-up        # build + run all services
make compose-logs      # follow
make compose-down      # tear down + remove volumes
```
