# DataMind Smart Contracts

Foundry project containing the on-chain provenance layer for DataMind:

- [`src/DatasetRegistry.sol`](src/DatasetRegistry.sol) — registers datasets by 0G Storage merkle root + metadata URI; tracks ownership, transfers, and metadata updates.
- [`src/LicenseRegistry.sol`](src/LicenseRegistry.sol) — mints licenses (Personal / Commercial / Academic / Exclusive) for registered datasets, with optional expiry and revocation.

## Build & test

```bash
# install forge-std (one-time)
forge install foundry-rs/forge-std --no-commit

forge build
forge test -vv
```

## Deploy to 0G Galileo testnet (chain 16602)

```bash
export OG_EVM_RPC=https://evmrpc-testnet.0g.ai
export OG_PRIVATE_KEY=0x...               # never commit
forge script script/Deploy.s.sol:Deploy \
  --rpc-url $OG_EVM_RPC \
  --private-key $OG_PRIVATE_KEY \
  --broadcast
```

After deploy, paste the printed addresses into the project root `.env`:

```
DATASET_REGISTRY_ADDRESS=0x...
LICENSE_REGISTRY_ADDRESS=0x...
```

## ABI export

`forge build` writes JSON ABIs to `out/<Contract>.sol/<Contract>.json`. The backend reads these directly via `services/chain/registry.py`.
