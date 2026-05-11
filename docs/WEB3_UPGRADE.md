# Live 0G Testnet Upgrade

The DataMind MVP now ships with first-class, **user-signed** Web3 flows running
against the 0G Galileo testnet. This document explains what changed, how to
deploy the new contracts, and how to walk the demo.

## What's new

**Contracts** (`smart-contracts/src/`):
- `DatasetRegistry.sol` — provenance (unchanged from MVP).
- `DatasetNFT.sol` — ERC-721 ownership receipt; `tokenId == datasetId`.
- `TrainingRegistry.sol` — on-chain training job ledger.
- `UsageEconomy.sol` — native-token fee router for publish / train / premium.
- `LicenseRegistry.sol` — license grants (unchanged from MVP).

**Frontend** (`frontend/`):
- `lib/web3/*` — wagmi/RainbowKit + viem config, ABIs, contracts, utils.
- `components/web3/*` — `WalletConnect`, `WalletBalance`, `NetworkSwitcher`,
  `TransactionStatus`, `FaucetHelper`, `Web3Provider`, `WalletSessionBridge`.
- `hooks/useDatasetPublish.ts` — orchestrates **mint + register + chain-confirm**.
- New env vars under `NEXT_PUBLIC_OG_*` and `NEXT_PUBLIC_DATASET_*`.

**Backend** (`backend/app/`):
- `app/web3/` package: `contracts/`, `services/`, `listeners/`, `utils/`.
- `web3/listeners/indexer.py` — async `eth_getLogs` indexer that mirrors
  on-chain events into Postgres + re-broadcasts via WebSockets.
- `services/datasets/chain_confirm.py` — accepts user-signed receipts.
- New API endpoints: `POST /datasets/{id}/chain-confirm`,
  `POST /training/jobs/{id}/chain-start`,
  `POST /training/jobs/{id}/chain-complete`,
  `GET /web3/config`, `GET /web3/events`.
- New tables: `dataset_nfts`, `blockchain_transactions`.
- New `dataset_status` enum value: `pending_chain`.
- New columns on `training_jobs`: `contract_job_id`, `chain_start_tx_hash`,
  `chain_complete_tx_hash`.

## Deploy contracts to Galileo

```bash
cd smart-contracts
forge install                          # if you have not already
forge build
forge script script/Deploy.s.sol:Deploy \
  --rpc-url $OG_EVM_RPC \
  --private-key $OG_PRIVATE_KEY \
  --broadcast
```

The script prints five addresses. Paste them into `.env`:

```env
DATASET_REGISTRY_ADDRESS=0x...
DATASET_NFT_ADDRESS=0x...
TRAINING_REGISTRY_ADDRESS=0x...
USAGE_ECONOMY_ADDRESS=0x...
LICENSE_REGISTRY_ADDRESS=0x...

# Frontend mirror (required so wagmi can call the contracts):
NEXT_PUBLIC_DATASET_REGISTRY=0x...
NEXT_PUBLIC_DATASET_NFT=0x...
NEXT_PUBLIC_TRAINING_REGISTRY=0x...
NEXT_PUBLIC_USAGE_ECONOMY=0x...
NEXT_PUBLIC_LICENSE_REGISTRY=0x...
```

Optionally re-export ABIs into `frontend/abi/`:

```bash
./scripts/export-abi.sh
```

## Toggle live mode

Mock-first is still the default. To run the demo on-chain set:

```env
DATAMIND_OG_MOCK=0              # 0G Storage uses the Node bridge
DATAMIND_WEB3_USER_TX=1         # wallet signs mint + register
DATAMIND_CHAIN_INDEXER=1        # backend indexes on-chain events
OG_PRIVATE_KEY=                 # only required for *storage* writes; chain writes use user wallet
NEXT_PUBLIC_OG_RPC_URL=https://evmrpc-testnet.0g.ai
NEXT_PUBLIC_CHAIN_ID=16602
```

Then `./scripts/run.sh`.

## Demo flow (10 steps)

1. **Connect wallet** — top-right RainbowKit `Connect wallet`. The
   `WalletSessionBridge` exchanges the address for a JWT against the existing
   `/auth/privy/verify` endpoint (mock token in demo mode).
2. **Get testnet 0G** — open `/dashboard` (or any page surfacing
   `<FaucetHelper />`) and click "Get testnet 0G".
3. **Upload a dataset** — `/upload`; backend handles AI + embeddings + 0G push.
4. **0G storage** — `og.upload` returns the storage root + tx hash.
5. **Dataset NFT mint** — `useDatasetPublish` automatically asks the wallet to
   sign `DatasetRegistry.register(...)` then `DatasetNFT.mintDatasetNFT(...)`.
6. **On-chain registration** — same flow; the receipt's `DatasetRegistered`
   event sets the dataset's `onchain_id`.
7. **Marketplace listing** — `/marketplace` now shows an `NFT` badge on
   minted datasets, and the dataset detail page exposes mint + register tx
   hashes (deep-links to the explorer).
8. **Launch fine-tuning** — `/training` (existing UI) creates the off-chain
   job, then `TrainingRegistry.createTrainingJob` is signed by the user; the
   indexer links `contract_job_id` → `TrainingJob.id`.
9. **Training metrics stream live** — unchanged WebSocket path. The backend
   indexer also publishes when `TrainingCompleted` is emitted.
10. **Provenance** — every receipt is in `blockchain_transactions` and
    `GET /api/v1/web3/events` for a clean audit feed.

## Optional: fees

`UsageEconomy.sol` charges per action. Configure in the deploy script:

```bash
DATAMIND_PUBLISH_FEE=0           # wei
DATAMIND_TRAINING_FEE=0
DATAMIND_PREMIUM_FEE=0
DATAMIND_TREASURY=0xYourTreasury
```

`useDatasetPublish.publish(..., { publishFeeWei: 10_000_000_000_000_000n })`
adds a `payForAction` step before register.

## Caveats

- The Node bridge for 0G Storage uploads (`infra/og-bridge`) still requires a
  funded `OG_PRIVATE_KEY` because storage writes are server-side. Only the
  **registry / NFT / training** transactions are user-signed.
- The indexer assumes a fresh chain: if you paste addresses for an
  already-active deployment, set `DATAMIND_CHAIN_INDEXER_START_BLOCK` to the
  block at which contracts were deployed.
- `dataset_status` now includes `pending_chain` — `0002_web3` Alembic
  migration must run before the new ingest path is used.
