# DataMind API

Base URL: `http://localhost:8000/api/v1` (dev) — full OpenAPI at `/docs`.

All endpoints accept JSON. Mutating endpoints require a JWT issued by the auth flow.

## Auth

| Method | Path                       | Auth | Description                              |
|--------|----------------------------|------|------------------------------------------|
| POST   | `/auth/nonce`              | —    | Issue a SIWE-style nonce + message.      |
| POST   | `/auth/siwe/verify`        | —    | Verify signature → issue session JWT.    |
| POST   | `/auth/privy/verify`       | —    | Verify Privy token (or mock) → JWT.      |
| GET    | `/auth/me`                 | JWT  | Return the authenticated user.           |

Body of `/auth/siwe/verify`:

```json
{ "wallet_address": "0x…", "nonce": "…", "signature": "0x…", "display_name": "Demo" }
```

Response:

```json
{ "access_token": "eyJ…", "token_type": "bearer", "user": { "id": "01HZ…", "wallet_address": "0x…" } }
```

## Datasets

| Method | Path                       | Auth   | Description                              |
|--------|----------------------------|--------|------------------------------------------|
| POST   | `/datasets` (multipart)    | JWT    | Upload + queue ingest pipeline.          |
| GET    | `/datasets`                | opt    | Paginated list (`?mine=true&category=…`).|
| GET    | `/datasets/{id}`           | —      | Detail incl. analytics + provenance.     |
| PATCH  | `/datasets/{id}`           | JWT    | Update title/description/visibility/etc. |
| DELETE | `/datasets/{id}`           | JWT    | Delete (cascades).                       |

Upload form fields:
- `file` (required, ≤ 200 MB)
- `title` (required)
- `category` — `Web3 | NLP | Finance | Tabular | Vision | Audio | Other`
- `tags` — JSON array string or comma list
- `visibility` — `public | private | unlisted`
- `price_amount`, `license_kind` — optional

Response:

```json
{
  "dataset": { "id": "01HZ…", "title": "…", "status": "processing", "progress": 5 },
  "ws_topic": "dataset:01HZ…"
}
```

## Marketplace

| Method | Path                           | Description                                         |
|--------|--------------------------------|-----------------------------------------------------|
| GET    | `/marketplace`                 | Paginated public datasets (`category=`, `sort=`).   |
| GET    | `/marketplace/trending?limit=` | Top-N trending datasets.                            |

`sort`: `trending | recent | quality | downloads`.

## Search

| Method | Path                | Body                                                                           |
|--------|---------------------|--------------------------------------------------------------------------------|
| POST   | `/search/semantic`  | `{query, limit?, min_score?, category?}`                                       |
| POST   | `/search/hybrid`    | as above, blends semantic top-K with Postgres keyword matches.                 |

Response:

```json
{
  "query": "crypto sentiment trading",
  "mode": "semantic",
  "took_ms": 73,
  "results": [
    { "dataset_id": "01HZ…", "title": "Crypto Twitter Sentiment", "score": 0.81, "snippet": "…" }
  ]
}
```

## Embeddings

| Method | Path                  | Body         | Notes                                  |
|--------|-----------------------|--------------|----------------------------------------|
| POST   | `/embeddings/embed`   | `{text}`     | Returns 384-dim vector + model name.   |

## Training

| Method | Path                       | Auth | Description                                                   |
|--------|----------------------------|------|---------------------------------------------------------------|
| POST   | `/training/jobs`           | JWT  | Create + launch a LoRA fine-tune.                              |
| GET    | `/training/jobs`           | JWT  | List your jobs.                                               |
| GET    | `/training/jobs/{id}`      | —    | Job detail + metrics history.                                 |

Create body:

```json
{
  "dataset_id": "01HZ…",
  "name": "Crypto sentiment LoRA",
  "base_model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
  "task": "causal_lm",
  "epochs": 3,
  "batch_size": 4,
  "learning_rate": 0.0002,
  "lora_r": 8,
  "lora_alpha": 16,
  "max_seq_length": 512
}
```

## Storage proxy

| Method | Path                  | Description                                          |
|--------|-----------------------|------------------------------------------------------|
| GET    | `/storage/{root}`     | Fetch a file by its 0G storage root (or local mock). |

## WebSocket

`ws://localhost:8000/ws/{topic}` — server fans out RealtimeEvents:

```json
{ "type": "upload.progress", "topic": "dataset:01HZ…", "payload": {...}, "ts": 1731297600.5 }
```

Topics in use:
- `dataset:{id}` — upload + AI pipeline events (`upload.started`, `analyze.completed`, `embed.completed`, `storage.anchored`, `upload.completed`, `upload.failed`).
- `training:{id}` — `train.started`, `train.progress`, `train.completed`, `train.failed`.

## Health

`GET /health` returns:

```json
{
  "status": "ok",
  "version": "0.1.0",
  "services": { "og": "mock", "chain": "mock", "privy": "mock" }
}
```
