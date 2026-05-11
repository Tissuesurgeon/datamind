#!/usr/bin/env bash
# Export Foundry build artifacts into a stable, frontend-friendly location.
#
# Foundry writes per-contract JSON to `smart-contracts/out/<Name>.sol/<Name>.json`
# (full artifact, with ABI under .abi). The frontend keeps a hand-curated subset
# in `frontend/lib/web3/abi.ts`, but we still copy the canonical artifacts to
# `frontend/abi/` so deploy scripts / downstream tooling can read them.
#
# Usage:
#   ./scripts/export-abi.sh                 # copies all known DataMind contracts
#   FORGE_OUT=./smart-contracts/out ./scripts/export-abi.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FORGE_OUT="${FORGE_OUT:-$ROOT/smart-contracts/out}"
DEST="${DEST:-$ROOT/frontend/abi}"

CONTRACTS=(
  DatasetRegistry
  DatasetNFT
  TrainingRegistry
  UsageEconomy
  LicenseRegistry
)

mkdir -p "$DEST"

missing=()
for c in "${CONTRACTS[@]}"; do
  src="$FORGE_OUT/$c.sol/$c.json"
  if [[ ! -f "$src" ]]; then
    missing+=("$c")
    continue
  fi
  cp "$src" "$DEST/$c.json"
  echo "[export-abi] $c -> $DEST/$c.json"
done

if (( ${#missing[@]} > 0 )); then
  echo "[export-abi] missing (run 'cd smart-contracts && forge build' first):" >&2
  printf '  - %s\n' "${missing[@]}" >&2
  exit 1
fi
