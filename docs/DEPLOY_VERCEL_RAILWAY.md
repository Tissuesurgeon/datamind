# Deploy DataMind on Vercel + Railway

This guide deploys **DataMind** as a split stack:

| Layer | Host | Role |
|-------|------|------|
| **Frontend** | [Vercel](https://vercel.com) | Next.js (marketplace, upload UI, RainbowKit) |
| **Backend** | [Railway](https://railway.app) | FastAPI, Alembic migrations, WebSocket pub/sub |
| **Data** | Railway + managed services | Postgres, Redis; Qdrant Cloud or self-hosted Qdrant |

Do **Railway first**, then **Vercel** — the UI needs a stable **`NEXT_PUBLIC_*` / `BACKEND_INTERNAL_URL`** pointing at the API.

---

## 1. Prerequisites

1. DataMind pushed to a **GitHub** repository.
2. **Railway** and **Vercel** accounts (GitHub login is fine).
3. Understand **environment variables**: you paste secrets in each dashboard; never commit a real `.env` to Git.

**Browser → API:** The frontend must call your Railway hostname (not `localhost`). **CORS** on the backend must list your Vercel origin(s).

---

## 2. Architecture (short)

```
Browser  ──►  https://your-app.vercel.app     (Next.js)
                  │
                  ├─► /api/proxy/*  ──►  https://your-api.up.railway.app/api/v1/*   (optional same-origin REST)
                  └─► wss://your-api…/ws    (WebSockets — must be explicit; see §B3)
Backend  ──►  Postgres, Redis, Qdrant
```

**Upload pipeline (today’s code):** analyze + embed via **`AI_ENGINE_URL`**, vectors in **Qdrant**, optional **0G Storage** (mock or live), then **on-chain** steps if Web3 is enabled.

---

## Part A — Railway (API + Postgres + Redis)

### A1. Create the project

1. Railway → **New Project** → **Deploy from GitHub repo** → select DataMind.

### A2. PostgreSQL

1. **+ New** → **Database** → **PostgreSQL**.
2. Open Postgres → **Variables** → copy **`DATABASE_URL`**.
3. **Normalize for asyncpg:** if the URL starts with `postgresql://`, change it to **`postgresql+asyncpg://`** (insert `+asyncpg`).
   - Example: `postgresql+asyncpg://user:pass@host:5432/railway`

### A3. Redis

1. **+ New** → **Database** → **Redis**.
2. Copy **`REDIS_URL`** (or Railway’s private Redis URL) for **internal** use by the backend.

### A4. Qdrant (vectors)

Embeddings are stored in Qdrant **every** upload path that runs the indexer.

- **Recommended:** [Qdrant Cloud](https://cloud.qdrant.io) → cluster URL + optional **`QDRANT_API_KEY`**.
- **Alternative:** run Qdrant on Railway from a template and point **`QDRANT_URL`** at it.

### A5. Backend service (Docker)

1. **+ New** → connect the **same** GitHub repo.
2. **Settings:**
   - **Dockerfile path:** `docker/backend.Dockerfile`
   - **Root directory:** repository root ( **`.`** — not `backend/`), because the Dockerfile copies `backend/` into the image itself.

3. **Variables** (Production) — core set:

| Variable | Value |
|----------|--------|
| `DATABASE_URL` | Postgres URL with **`postgresql+asyncpg://`** |
| `REDIS_URL` | From Redis service |
| `QDRANT_URL` | `https://…` (Cloud) or internal URL |
| `QDRANT_API_KEY` | If required; else empty |
| `DATAMIND_ENV` | `production` |
| `BACKEND_JWT_SECRET` | Random string, **≥ 32 characters** |
| `BACKEND_PUBLIC_URL` | `https://YOUR-RAILWAY-HOST` (no `/api/v1`; set after first deploy — **A6**) |
| `BACKEND_CORS_ORIGINS` | Your Vercel origin(s), comma-separated, **no spaces** (e.g. `https://app.vercel.app`) |
| `AI_ENGINE_URL` | **Required for real uploads:** URL of the AI engine service (see **§6**). Without it, ingest that depends on analyze/embed will fail. |

The container runs **`alembic upgrade head`** then **`uvicorn`** (see `docker/backend.Dockerfile`).

### A6. Public URL + health check

1. Backend service → **Settings** → **Networking** → **Generate Domain**.
2. Example host: `https://datamind-api-production.up.railway.app`.
3. Set **`BACKEND_PUBLIC_URL`** to that origin (scheme + host, no trailing path).
4. Smoke test:

   ```bash
   curl -sS https://YOUR-RAILWAY-HOST/health
   ```

   REST lives under **`/api/v1`** (e.g. `https://YOUR-RAILWAY-HOST/api/v1/datasets`).

### A7. 0G Storage (mock vs live)

Behavior is controlled by **`DATAMIND_OG_MOCK`** and **`OG_PRIVATE_KEY`** (see `.env.example`).

| Mode | `DATAMIND_OG_MOCK` | `OG_PRIVATE_KEY` | Behavior |
|------|--------------------|------------------|----------|
| **Mock (default)** | `1` (or omit) | optional | Deterministic roots; files mirrored under server storage. **Per-dataset salt** avoids duplicate `storageRoot` on-chain when the same file is uploaded again. |
| **Live** | `0` | **Required** | Backend shells to **`infra/og-bridge/cli.mjs`** with `@0glabs/0g-ts-sdk` (Galileo RPC + indexer). |

**Docker caveat:** The stock **`docker/backend.Dockerfile`** copies **`backend/`** only; it does **not** install Node or bundle **`infra/og-bridge/`**. The Python **`og_client`** shells out to **`node …/infra/og-bridge/cli.mjs`** for **`DATAMIND_OG_MOCK=0`**, so **live 0G uploads on Railway need a custom backend image** (e.g. add Node, `COPY infra/og-bridge`, `npm ci` inside it) **or** equivalent changes to match your layout. The repo also has **`docker/og-bridge.Dockerfile`** for a standalone HTTP bridge used in Docker Compose; wiring production to that HTTP API would need code changes. For hosted demos, **`DATAMIND_OG_MOCK=1`** is the supported default.

Also set when testing Galileo storage locally or on a custom image:

| Variable | Typical value |
|----------|----------------|
| `OG_EVM_RPC` | `https://evmrpc-testnet.0g.ai` |
| `OG_INDEXER_RPC` | `https://indexer-storage-testnet-turbo.0g.ai` |

### A8. Web3 / on-chain (optional)

For **user-signed** transactions (dataset **register** + **NFT mint** after upload), deploy contracts to **0G Galileo (chain id 16602)** and mirror addresses on backend + frontend.

**Backend (Railway):**

| Variable | Notes |
|----------|--------|
| `DATAMIND_WEB3_USER_TX` | `1` = after storage, status **`pending_chain`** until the wallet completes txs + **`POST …/chain-confirm`** |
| `DATASET_REGISTRY_ADDRESS` | From `forge script` |
| `DATASET_NFT_ADDRESS` | |
| `TRAINING_REGISTRY_ADDRESS` | |
| `USAGE_ECONOMY_ADDRESS` | |
| `LICENSE_REGISTRY_ADDRESS` | |
| `OG_EVM_RPC` | Used by the optional chain indexer |
| `DATAMIND_CHAIN_INDEXER` | `1` to poll **`eth_getLogs`** into Postgres; `0` to skip |
| `DATAMIND_CHAIN_INDEXER_START_BLOCK` | Deployment block of your contracts |
| `DATAMIND_CHAIN_INDEXER_POLL_SECONDS` | e.g. `5` |

`OG_PRIVATE_KEY` on the server is **not** used for user-signed registry/NFT calls; the **connected wallet** signs those. The key matters for **live 0G Storage** when **`DATAMIND_OG_MOCK=0`**.

Details: [`docs/WEB3_UPGRADE.md`](WEB3_UPGRADE.md).

### A9. Seed demo data (optional)

Railway backend → **Shell** (working directory should be app root as in the image):

```bash
cd /app/backend && python -m app.scripts.seed
```

Adjust path if your shell opens elsewhere (`ls`, then `cd`).

---

## Part B — Vercel (Next.js frontend)

### B1. Import

**Add New** → **Project** → import the DataMind repo.

### B2. Root directory & build

**Important:** This repo has **no** `package.json` at the **repository root** — only under **`frontend/`**. If Vercel’s **Root Directory** is left as `.`, the build will fail (wrong working directory, missing Next.js, or empty install).

| Setting | Value |
|---------|--------|
| **Root Directory** | **`frontend`** (Project → Settings → General → *Root Directory*) |
| **Framework** | Next.js (auto) |
| **Install Command** | leave default (`npm install` or `npm ci` **inside** `frontend/`) |
| **Build Command** | default `npm run build` |

After changing Root Directory, trigger a **new deployment** (Redeploy).

**Optional check locally** (same as Vercel):

```bash
cd frontend && npm ci && npm run build
```

If that succeeds on your machine but Vercel still fails, open the failed deployment → **Build Logs** and scroll to the **first** `Error:` line; that message is what to fix next.

### B3. Environment variables

Add at least **Production**; repeat for **Preview** if you use preview deploys.

**Recommended (same-origin REST via rewrite):**

| Name | Value |
|------|--------|
| `BACKEND_INTERNAL_URL` | `https://YOUR-RAILWAY-HOST/api/v1` |

In **`next.config.ts`**, `/api/proxy/:path*` rewrites to this base. If **`NEXT_PUBLIC_API_BASE`** is unset on the client, the app uses **`/api/proxy`** in production (see `frontend/lib/env.ts`), so **`BACKEND_INTERNAL_URL`** must be set on Vercel.

**WebSockets (required in production for live progress):** The proxy does **not** tunnel WebSockets. Set explicitly:

| Name | Value |
|------|--------|
| `NEXT_PUBLIC_WS_BASE` | `wss://YOUR-RAILWAY-HOST/ws` |

**Alternative:** Set **`NEXT_PUBLIC_API_BASE`** to `https://YOUR-RAILWAY-HOST/api/v1` and rely on **`BACKEND_CORS_ORIGINS`** including your Vercel URL. You still need **`NEXT_PUBLIC_WS_BASE`** for `wss://…/ws`.

**(chain / Web3 UI)**

| Name | Example / notes |
|------|------------------|
| `NEXT_PUBLIC_CHAIN_ID` | `16602` |
| `NEXT_PUBLIC_OG_RPC_URL` | `https://evmrpc-testnet.0g.ai` |
| `NEXT_PUBLIC_OG_EXPLORER_URL` | `https://chainscan-galileo.0g.ai` |
| `NEXT_PUBLIC_OG_FAUCET_URL` | `https://faucet.0g.ai` |
| `NEXT_PUBLIC_DATASET_REGISTRY` | Match backend `DATASET_REGISTRY_ADDRESS` |
| `NEXT_PUBLIC_DATASET_NFT` | Match `DATASET_NFT_ADDRESS` |
| `NEXT_PUBLIC_TRAINING_REGISTRY` | |
| `NEXT_PUBLIC_USAGE_ECONOMY` | |
| `NEXT_PUBLIC_LICENSE_REGISTRY` | |
| `NEXT_PUBLIC_WC_PROJECT_ID` | Optional WalletConnect / Reown project id |
| `NEXT_PUBLIC_PRIVY_APP_ID` | If using Privy in the browser; must align with backend `PRIVY_*` |

Full list mirrors [`.env.example`](../.env.example).

### B4. Deploy & CORS

1. Deploy on Vercel.
2. Copy the production URL (e.g. `https://datamind-xxx.vercel.app`).
3. Railway backend → **`BACKEND_CORS_ORIGINS`** must include that **exact** origin (no trailing slash).
4. Redeploy backend if variables do not hot-reload.

---

## 3. Verify auth & API

1. Open the Vercel site; **DevTools** → **Network**.
2. **Connect wallet** / complete any Privy flow.
3. Confirm calls to your API (via **`/api/proxy`** or direct **`NEXT_PUBLIC_API_BASE`**) return **200**.

**Common issues**

| Symptom | Fix |
|---------|-----|
| CORS errors | Add Vercel origin to **`BACKEND_CORS_ORIGINS`**. |
| Requests to `localhost` | Set **`BACKEND_INTERNAL_URL`** or **`NEXT_PUBLIC_API_BASE`**. |
| Upload “stuck” without live updates | Set **`NEXT_PUBLIC_WS_BASE`** to **`wss://YOUR-RAILWAY-HOST/ws`**. |
| 502 / timeouts | Railway logs; ensure the service listens on the port Railway expects (`8000` in the Dockerfile). |
| **`OPTIONS …/auth/privy/verify` → 400** | The browser’s **`Origin`** was not allowed. The API now defaults to **`allow_origin_regex`** matching **`https://*.vercel.app`** (see `BACKEND_CORS_ORIGIN_REGEX`). Also add your **exact** frontend URL(s) to **`BACKEND_CORS_ORIGINS`** (no trailing slash), especially for a **custom domain**. Redeploy the backend after changing env. |

---

## 4. AI engine (separate service)

Uploads run **analyze** and **batch embed** against **`AI_ENGINE_URL`** (`ai-engine/` FastAPI in the repo). For production, add **another Railway service** from the same repo:

- **Dockerfile path:** `docker/ai-engine.Dockerfile`.
- Set **`AI_ENGINE_URL`** on the **backend** to that service’s **internal or public** base URL (e.g. `https://datamind-ai.up.railway.app`).

Without a reachable AI engine, pipeline steps that call it will fail even if Postgres/Redis/Qdrant are fine.

---

## 5. URL quick reference

| Purpose | URL |
|---------|-----|
| Health | `https://YOUR-RAILWAY-HOST/health` |
| OpenAPI | `https://YOUR-RAILWAY-HOST/docs` |
| REST base | `https://YOUR-RAILWAY-HOST/api/v1` |
| WebSocket | `wss://YOUR-RAILWAY-HOST/ws` |
| Frontend | `https://YOUR-PROJECT.vercel.app` |

---

## 6. Deploy contracts (Galileo)

If you need the **full** on-chain demo:

```bash
cd smart-contracts
forge install    # first time only
forge build
forge script script/Deploy.s.sol:Deploy \
  --rpc-url https://evmrpc-testnet.0g.ai \
  --private-key "$OG_PRIVATE_KEY" \
  --broadcast
```

Paste printed addresses into Railway **and** Vercel (`DATASET_*` ↔ `NEXT_PUBLIC_DATASET_*`, etc.).

Optional ABI sync for the frontend:

```bash
./scripts/export-abi.sh
```

---

## 7. Security

- Do not commit **`.env`** with real secrets (especially **`BACKEND_JWT_SECRET`**, **`OG_PRIVATE_KEY`**, **`PRIVY_APP_SECRET`**).
- Rotate any key that ever appeared in a public repo.
- Use strong **`BACKEND_JWT_SECRET`** in production.
- **Privy:** for production wallet login, set **`PRIVY_APP_ID`** / **`PRIVY_APP_SECRET`** on the backend and **`NEXT_PUBLIC_PRIVY_APP_ID`** on Vercel; empty Privy envs fall back to demo/mock flows.

---

## 8. Related docs

- [`.env.example`](../.env.example) — authoritative variable list
- [`docs/WEB3_UPGRADE.md`](WEB3_UPGRADE.md) — contracts, indexer, user-tx flow
- [`docs/0G_INTEGRATION.md`](0G_INTEGRATION.md) — 0G Storage behavior
