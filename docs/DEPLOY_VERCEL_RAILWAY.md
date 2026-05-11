# Deploy DataMind: Vercel + Railway (step by step)

This guide walks you through putting **DataMind** online:

- **Railway** hosts the **API** (FastAPI), talking to **Postgres**, **Redis**, and **Qdrant**.
- **Vercel** hosts the **website** (Next.js).

You will do **Railway first**, then **Vercel**, because the website needs your API’s public URL.

---

## 1. What you need before you start

1. A **GitHub** account and your DataMind code pushed to a **GitHub repository**.
2. A **Railway** account ([railway.app](https://railway.app)) — sign up with GitHub.
3. A **Vercel** account ([vercel.com](https://vercel.com)) — sign up with GitHub.

**Terms:**

- **Environment variables** — settings your app reads at runtime (passwords, URLs). You paste them into Railway/Vercel dashboards; do **not** commit real secrets to GitHub.
- **Public URL** — the `https://…` address users open in a browser.

---

## 2. Big picture (simple)

```
User browser
    → opens https://your-app.vercel.app (Vercel, Next.js)
    → calls your API at https://your-api.up.railway.app (Railway, FastAPI)
    → API uses Postgres / Redis / Qdrant on Railway (or Qdrant Cloud)
```

**Connect wallet** needs the browser to reach the API and the API to allow your Vercel domain (CORS).

---

## Part A — Railway (backend + database)

### Step A1. Create a Railway project

1. Log in to [Railway](https://railway.app).
2. Click **New Project**.
3. Choose **Deploy from GitHub repo** and select your **DataMind** repository.
4. Railway may create an empty service — you will add **Postgres**, **Redis**, and a **Docker** service for the API.

### Step A2. Add PostgreSQL

1. In the project, click **+ New**.
2. Choose **Database** → **PostgreSQL**.
3. Wait until it finishes provisioning.
4. Click the **Postgres** service → **Variables**.
5. Find **`DATABASE_URL`** (it is created for you).  
   **Important:** Railway’s URL often starts with `postgresql://`. This project needs **`asyncpg`**.

   - Copy the value.
   - Change the start from `postgresql://` to **`postgresql+asyncpg://`** (add `+asyncpg` after `postgresql`).
   - Example:  
     `postgresql+asyncpg://user:pass@host:5432/railway`

You will paste this fixed URL into the **backend** service variables in Step A5.

### Step A3. Add Redis

1. Click **+ New** → **Database** → **Redis**.
2. Open the Redis service → **Variables** and copy **`REDIS_URL`** (or **`REDIS_PRIVATE_URL`** if that is what Railway shows — use the URL meant for internal TCP connections inside Railway).

You will set **`REDIS_URL`** on the backend to this value.

### Step A4. Add Qdrant (vectors)

Qdrant stores search embeddings. Easiest options:

**Option 1 — Qdrant Cloud (simple for beginners)**  
1. Sign up at [cloud.qdrant.io](https://cloud.qdrant.io).  
2. Create a free cluster and copy the **HTTPS URL** and **API key** (if any).  
3. You will set **`QDRANT_URL`** (and **`QDRANT_API_KEY`** if required).

**Option 2 — Another Qdrant on Railway**  
1. In Railway, **+ New** → **Template** and search for **Qdrant**, or deploy a Qdrant service from a community template.  
2. Copy the internal or public URL Railway gives you into **`QDRANT_URL`**.

For a first deploy, **Option 1** is usually the least confusing.

### Step A5. Deploy the FastAPI backend (Docker)

1. Click **+ New** → **GitHub Repo** → pick the **same** DataMind repo (or **Empty Service** and connect the repo).
2. Open the new service → **Settings**:
   - **Build** → **Dockerfile path:** `docker/backend.Dockerfile`
   - **Root directory:** leave as **repository root** (`.` / blank), not `backend/`, because the Dockerfile expects the whole repo.
3. Open **Variables** and add (replace placeholders with your real values):

| Variable | What to put |
|----------|-------------|
| `DATABASE_URL` | Your Postgres URL with **`postgresql+asyncpg://`** (see Step A2). |
| `REDIS_URL` | From the Redis service (Step A3). |
| `QDRANT_URL` | Your Qdrant HTTPS URL, e.g. `https://xxxx.cloud.qdrant.io` |
| `QDRANT_API_KEY` | If your Qdrant cluster uses an API key; else leave empty. |
| `DATAMIND_ENV` | `production` |
| `BACKEND_JWT_SECRET` | A long random string (at least 32 characters). Generate one and keep it secret. |
| `BACKEND_PUBLIC_URL` | Will update after deploy — temporarily `http://localhost:8000`, then set to your Railway **public API URL** (Step A6). |
| `AI_ENGINE_URL` | For a **minimal** deploy you can point this at your API host with a placeholder port you don’t use yet, or deploy the AI engine later. Many hackathon flows work if you add a second Railway service for `ai-engine` later. *Simplest first path:* use a second service only when you need training/embeddings at scale. |

4. **CORS (needed so Vercel can call the API):**  
   After you have your Vercel URL (Part B), come back and set:

   | Variable | Example |
   |----------|---------|
   | `BACKEND_CORS_ORIGINS` | `https://your-app.vercel.app` |

   Use **no spaces** between origins. Multiple sites:  
   `https://app.vercel.app,https://www.yourdomain.com`

5. Click **Deploy** (or save variables — Railway redeploys).

### Step A6. Get your API public URL

1. Open the **backend** service → **Settings** → **Networking**.
2. Click **Generate Domain** (or attach a custom domain).
3. Copy the URL, e.g. `https://datamind-api-production.up.railway.app`.
4. Your REST API base path includes **`/api/v1`**. So your **API base** is:

   `https://YOUR-RAILWAY-HOST/api/v1`

5. Go back to **Variables** and set:

   - `BACKEND_PUBLIC_URL` → `https://YOUR-RAILWAY-HOST` (no `/api/v1` required here).

6. Quick test in a browser or terminal:

   ```bash
   curl https://YOUR-RAILWAY-HOST/health
   ```

   You should see JSON with `"status": "ok"` (or similar).

The backend Docker image already runs **`alembic upgrade head`** before starting the server, so database tables are created on deploy.

### Step A7. (Optional) Seed demo data

To load sample datasets into Postgres:

1. Railway → your backend service → **Shell** or use **Railway CLI** with the service context.
2. From the app directory used in the container (usually `/app/backend`), run:

   ```bash
   python -m app.scripts.seed
   ```

If the shell starts in another folder, `cd` into the backend app root first (check with `ls`).

---

## Part B — Vercel (frontend)

### Step B1. Import the project

1. Log in to [Vercel](https://vercel.com).
2. **Add New** → **Project** → **Import** your GitHub **DataMind** repo.

### Step B2. Configure the build

1. **Root Directory:** click **Edit** and set to **`frontend`**.  
   This folder contains `package.json` for Next.js.
2. **Framework Preset:** Next.js (auto-detected).
3. **Build Command:** default (`npm run build` or `next build`).
4. **Output:** default for Next.js.

### Step B3. Environment variables (Vercel)

In **Environment Variables**, add **Production** (and Preview if you want):

| Name | Value | Notes |
|------|--------|------|
| `BACKEND_INTERNAL_URL` | `https://YOUR-RAILWAY-HOST/api/v1` | Same as API base. Used server-side for `/api/proxy` rewrites so the browser does not need CORS for REST when using the proxy. |
| `NEXT_PUBLIC_WS_BASE` | `wss://YOUR-RAILWAY-HOST/ws` | Change `https` → **`wss`**, path **`/ws`** (WebSockets cannot use `/api/proxy` the same way). |

**Alternative (direct API, no proxy):**  
Instead of relying on `/api/proxy`, you can set:

- `NEXT_PUBLIC_API_BASE` = `https://YOUR-RAILWAY-HOST/api/v1`
- `NEXT_PUBLIC_WS_BASE` = `wss://YOUR-RAILWAY-HOST/ws`

Then **CORS** on Railway **must** include your Vercel URL (you already set `BACKEND_CORS_ORIGINS`).

### Step B4. Deploy

1. Click **Deploy**.
2. When it finishes, open the **`.vercel.app`** URL Vercel shows.

### Step B5. Finish CORS on Railway

1. Copy your exact Vercel production URL, e.g. `https://datamind-xxx.vercel.app`.
2. Railway → backend → **Variables** → **`BACKEND_CORS_ORIGINS`** = that URL (comma-separated if several).
3. Redeploy if Railway does not pick it up automatically.

---

## 3. Check that “Connect wallet” works

1. Open your **Vercel** site.
2. Open the browser **Developer Tools** → **Network**.
3. Click **Connect wallet**.
4. Find a request like **`privy/verify`** (or `auth/privy/verify`).
5. It should be **200** and return JSON with `access_token`.

**If it fails:**

- **Blocked / CORS** — fix `BACKEND_CORS_ORIGINS` on Railway; include the exact Vercel origin (`https://…`, no trailing slash).
- **Calls `localhost`** — on Vercel you must set **`BACKEND_INTERNAL_URL`** or **`NEXT_PUBLIC_API_BASE`** to your Railway URL (see B3).
- **502 / connection** — Railway service asleep or wrong port; check Railway logs for the backend service.

---

## 4. AI engine (optional, advanced)

Training and some embedding-heavy flows expect **`AI_ENGINE_URL`** pointing at the separate **ai-engine** FastAPI service (`ai-engine/` in the repo). For a first deploy you can:

- Skip it until you need training, **or**
- Add **another Railway service** using `docker/ai-engine.Dockerfile` (same repo root context) and set `AI_ENGINE_URL` on the backend to that service’s URL.

---

## 5. Quick reference — URLs

| Purpose | Example shape |
|--------|----------------|
| API health | `https://YOUR-RAILWAY-HOST/health` |
| API docs | `https://YOUR-RAILWAY-HOST/docs` |
| API REST base | `https://YOUR-RAILWAY-HOST/api/v1` |
| WebSocket base | `wss://YOUR-RAILWAY-HOST/ws` |
| Website | `https://YOUR-PROJECT.vercel.app` |

---

## 5b. Optional: deploy contracts first (live on-chain mode)

If you want the **user-signed** Web3 flow (RainbowKit + NFT mint + on-chain
training), deploy contracts to 0G Galileo **before** filling in production env
vars:

```bash
cd smart-contracts
forge install
forge build
forge script script/Deploy.s.sol:Deploy \
  --rpc-url https://evmrpc-testnet.0g.ai \
  --private-key $OG_PRIVATE_KEY \
  --broadcast
```

Copy the printed addresses into **both** sides:

| Railway (backend) | Vercel (frontend) |
|-------------------|--------------------|
| `DATASET_REGISTRY_ADDRESS` | `NEXT_PUBLIC_DATASET_REGISTRY` |
| `DATASET_NFT_ADDRESS` | `NEXT_PUBLIC_DATASET_NFT` |
| `TRAINING_REGISTRY_ADDRESS` | `NEXT_PUBLIC_TRAINING_REGISTRY` |
| `USAGE_ECONOMY_ADDRESS` | `NEXT_PUBLIC_USAGE_ECONOMY` |
| `LICENSE_REGISTRY_ADDRESS` | `NEXT_PUBLIC_LICENSE_REGISTRY` |

Also set on Vercel:

| Variable | Example |
|---------|----------|
| `NEXT_PUBLIC_OG_RPC_URL` | `https://evmrpc-testnet.0g.ai` |
| `NEXT_PUBLIC_OG_EXPLORER_URL` | `https://chainscan-galileo.0g.ai` |
| `NEXT_PUBLIC_OG_FAUCET_URL` | `https://faucet.0g.ai` |
| `NEXT_PUBLIC_CHAIN_ID` | `16602` |
| `NEXT_PUBLIC_WC_PROJECT_ID` | Your WalletConnect / Reown id (optional) |

Then on Railway add:

| Variable | Value |
|---------|-------|
| `DATAMIND_WEB3_USER_TX` | `1` |
| `DATAMIND_CHAIN_INDEXER` | `1` |
| `DATAMIND_CHAIN_INDEXER_START_BLOCK` | block height when contracts were deployed |

See [`docs/WEB3_UPGRADE.md`](WEB3_UPGRADE.md) for the full flow.

## 6. Security reminders

- Never commit **`.env`** with real secrets.
- Use a strong **`BACKEND_JWT_SECRET`** in production.
- **Privy:** leave `PRIVY_APP_ID` empty for the built-in demo wallet, or configure Privy properly for real wallet login (see `.env.example`).

You’re done: **Railway = API + data**, **Vercel = UI**, **CORS + env URLs = working wallet and API calls.**
