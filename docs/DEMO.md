# DataMind — 8-step demo

Run the full stack in one shot:

```bash
cp .env.example .env
./scripts/run.sh
# Frontend:  http://localhost:3000
# Backend:   http://localhost:8000/docs
# AI engine: http://localhost:8100/docs
```

The `seed` step preloads six showcase datasets so the marketplace and dashboard
are populated even before you upload anything.

---

## Step 1 — Upload

Open `http://localhost:3000/upload`. Drop the seed CSV
`scripts/seed/crypto_twitter_sentiment.csv` (or any CSV / JSON / TXT / PDF).
Fill the form (title, category `Web3`, tags `sentiment, twitter, crypto`),
click **Upload & process**.

> A mock wallet is created on first visit; you'll be auto-signed in if needed.

## Step 2 — Auto-process

The upload page shows a live progress bar driven by `WS /ws/dataset:{id}`. Pipeline stages:

1. Validate format & size
2. Extract metadata
3. AI quality + tagging (ai-engine `/analyze`)
4. Embed + index in Qdrant (`/embed/batch`)
5. Push to 0G Storage (mock mode unless live keys set)
6. Anchor in `DatasetRegistry.sol` (in-memory unless contracts deployed)

## Step 3 — Marketplace

Open `http://localhost:3000/marketplace`. Your new dataset appears alongside
the seeded ones. Filter by category and sort by quality / trending / recent.

## Step 4 — Semantic search

Open `http://localhost:3000/search`. Query: `crypto sentiment trading`. Default
mode `Semantic` returns the dataset with cosine ≥ 0.5. Toggle `Hybrid` to add
keyword reranking.

## Step 5 — Launch fine-tune

From the dataset detail page, click **Launch fine-tune**. Configure:

- Base model: `TinyLlama/TinyLlama-1.1B-Chat-v1.0`
- Epochs: 3
- LR: 0.0002

Hit launch. The Training Studio opens with a live loss chart, log stream, and
progress bar (driven by `WS /ws/training:{id}`).

## Step 6 — Watch progress

The chart updates ~25 Hz from the simulated trainer (deterministic per job id).
Real LoRA fine-tuning kicks in when `AI_LORA_REAL=1` and a GPU is available.

## Step 7 — Predictions + metrics

When the run completes, the page shows final loss, eval loss, accuracy and the
checkpoint storage root. Use `POST /api/v1/embeddings/embed` (via Swagger) for
inference samples. The ai-engine `/infer` endpoint returns deterministic
sentiment-style outputs in mock mode.

## Step 8 — Provenance

Back on the dataset detail page, the **Provenance** card shows:

- Owner wallet
- Storage root (0G)
- Tx hash
- Chain id 16602
- On-chain id (`DatasetRegistry.sol#datasetId`)
- Metadata URI (`0g://…`)

Click **Fetch from 0G** to round-trip the file via the storage proxy
(`GET /api/v1/storage/{root}`).

---

## Live-mode upgrade

To swap the demo to a real 0G testnet end-to-end:

1. `make deploy-contracts` (Galileo testnet)
2. Paste addresses + your private key into `.env`
3. Set `DATAMIND_OG_MOCK=0`
4. `./scripts/run.sh`
5. `/health` now reports `og: live, chain: live`
6. Storage roots and tx hashes shown in the UI become real Galileo links.
