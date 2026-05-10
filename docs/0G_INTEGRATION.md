# 0G Integration

DataMind treats 0G as the canonical storage + compute layer for the AI data
economy. Three surfaces are wired:

- **0G Storage** — datasets, embedding manifests, training checkpoints.
- **0G Compute** — embedding/training/inference jobs (abstracted via `JobRunner`).
- **Galileo Testnet (chain id 16602)** — `DatasetRegistry.sol`, `LicenseRegistry.sol`.

## Mock-by-default

Every 0G surface ships with a deterministic mock so the demo runs without any
keys. Setting the env vars below flips the corresponding surface to **live**:

| Surface       | Mock default                            | Live switch                                                                |
|---------------|------------------------------------------|----------------------------------------------------------------------------|
| 0G Storage    | SHA-256 root + local mirror              | `DATAMIND_OG_MOCK=0` + `OG_PRIVATE_KEY`, `OG_INDEXER_RPC`, `OG_EVM_RPC`     |
| 0G Compute    | LocalRunner (calls ai-engine HTTP)       | `OGComputeRunner` activates when storage is live                           |
| Chain         | in-memory registry                       | deploy contracts then set `DATASET_REGISTRY_ADDRESS` / `LICENSE_REGISTRY_ADDRESS` |

## Storage bridge

`infra/og-bridge/cli.mjs` is a Node sidecar that wraps `@0glabs/0g-ts-sdk`. The
Python backend calls it via subprocess.

```bash
# CLI
node infra/og-bridge/cli.mjs upload --file path/to/file.csv \
  --rpc $OG_EVM_RPC --indexer $OG_INDEXER_RPC --key $OG_PRIVATE_KEY
# stdout: {"root":"0x…","tx_hash":"0x…","size":1024,"mode":"live"}
```

`backend/app/services/storage/og_client.py`:

```python
result = await og_client.upload(local_path)
# {"root": "0x…", "tx_hash": "0x…", "size": 1024, "mode": "live"}
```

The bridge has a long-running `serve` mode used by docker compose's `og-bridge`
profile so multi-host deploys don't need to bundle Node into the backend image.

## Chain registry

`backend/app/services/chain/registry.py` reads the Foundry-built ABI at
`smart-contracts/out/DatasetRegistry.sol/DatasetRegistry.json`, signs with
`OG_PRIVATE_KEY`, and broadcasts via `web3.AsyncWeb3` against `OG_EVM_RPC`.

```python
chain = await registry.register_dataset(
    storage_root=result["root"], metadata_uri=f"0g://{result['root']}"
)
# {"onchain_id": 12, "tx_hash": "0x…", "chain_id": 16602, "mode": "live"}
```

Failures (RPC down, gas estimate fails, etc.) fall back to the mock so the demo
never breaks.

## 0G Compute abstraction

`backend/app/services/compute/og_compute.py` defines a `JobRunner` Protocol with
`submit / poll / cancel / stream_logs`. Two implementations:

- **LocalRunner** — executes via the AI engine HTTP API. Default in mock mode.
- **OGComputeRunner** — HTTP stub against `https://compute-testnet.0g.ai` with a
  fall-through to LocalRunner so the surface always succeeds.

`get_runner()` selects based on env. To migrate to real 0G Compute, only
`OGComputeRunner._base` and the request shape need updating — everything above
already uses the abstract interface.

## Deployment to Galileo

```bash
export OG_EVM_RPC=https://evmrpc-testnet.0g.ai
export OG_PRIVATE_KEY=0x...
make deploy-contracts
# DatasetRegistry deployed at: 0x...
# LicenseRegistry deployed at: 0x...
```

Then in `.env`:

```
DATAMIND_OG_MOCK=0
DATASET_REGISTRY_ADDRESS=0x...
LICENSE_REGISTRY_ADDRESS=0x...
OG_PRIVATE_KEY=0x...
OG_INDEXER_RPC=https://indexer-storage-testnet-turbo.0g.ai
```

Restart the backend; `/health` should now report `og: live, chain: live`.

## Useful links

- 0G docs: https://docs.0g.ai/
- Galileo explorer: https://chainscan-galileo.0g.ai/
- Storage SDK: https://github.com/0glabs/0g-ts-sdk
