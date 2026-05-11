"use client";

import { Info, ShieldAlert } from "lucide-react";

import { useBackendChainConfig } from "@/lib/queries";
import { PUBLISH_CONTRACTS_READY } from "@/lib/web3/contracts";

function explorerBase(): string {
  const fromEnv = process.env.NEXT_PUBLIC_OG_EXPLORER_URL?.replace(/\/+$/, "");
  return fromEnv || "https://chainscan-galileo.0g.ai";
}

/**
 * Explains why uploads may not show txs on Galileo — backend defaults to mock 0G + mock registry.
 */
export function ChainModeBanner() {
  const { data: cfg, isLoading, isError } = useBackendChainConfig();

  if (isLoading || isError || !cfg) return null;

  if (cfg.web3_user_tx) {
    if (!PUBLISH_CONTRACTS_READY) {
      return (
        <div className="flex gap-3 rounded-2xl border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
          <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" />
          <div className="space-y-1">
            <p className="font-medium">Wallet signing is enabled on the server, but contract addresses are incomplete.</p>
            <p className="text-amber-100/80">
              Set <code className="rounded bg-black/30 px-1">NEXT_PUBLIC_DATASET_REGISTRY</code> and{" "}
              <code className="rounded bg-black/30 px-1">NEXT_PUBLIC_DATASET_NFT</code>{" "}
              to match your deployment (training / usage contracts are only needed for other flows), then restart the
              frontend.
            </p>
          </div>
        </div>
      );
    }
    return (
      <div className="flex gap-3 rounded-2xl border border-border-subtle bg-surface-1 px-4 py-3 text-sm text-text-muted">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-brand-amber-300" />
        <div className="space-y-1">
          <p className="font-medium text-text">
            After storage finishes, your wallet will sign mint + DatasetRegistry transactions.
          </p>
          <p>
            Confirm them in MetaMask (or your wallet), then check{" "}
            <a
              href={explorerBase()}
              target="_blank"
              rel="noreferrer"
              className="text-brand-amber-300 underline-offset-2 hover:underline"
            >
              the 0G explorer
            </a>
            .
          </p>
        </div>
      </div>
    );
  }

  if (!cfg.og_mock && cfg.chain_live) {
    return (
      <div className="flex gap-3 rounded-2xl border border-border-subtle bg-surface-1 px-4 py-3 text-sm text-text-muted">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-brand-amber-300" />
        <div className="space-y-1">
          <p className="font-medium text-text">Live mode: the backend anchors datasets with your configured hot key.</p>
          <p>
            Look for txs from that key on{" "}
            <a
              href={explorerBase()}
              target="_blank"
              rel="noreferrer"
              className="text-brand-amber-300 underline-offset-2 hover:underline"
            >
              chainscan
            </a>
            .
          </p>
        </div>
      </div>
    );
  }

  if (!cfg.og_mock && !cfg.chain_live) {
    return (
      <div className="flex gap-3 rounded-2xl border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
        <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" />
        <div className="space-y-1">
          <p className="font-medium">0G mock is off, but the backend is not chain-live yet.</p>
          <p className="text-amber-100/80">
            Add a funded testnet <code className="rounded bg-black/30 px-1">OG_PRIVATE_KEY</code> and{" "}
            <code className="rounded bg-black/30 px-1">DATASET_REGISTRY_ADDRESS</code>, or set{" "}
            <code className="rounded bg-black/30 px-1">DATAMIND_OG_MOCK=1</code> for local demo.
          </p>
        </div>
      </div>
    );
  }

  // Default hackathon / local: full mock
  return (
    <div className="flex gap-3 rounded-2xl border border-border-subtle bg-surface-1 px-4 py-3 text-sm text-text-muted">
      <Info className="mt-0.5 h-4 w-4 shrink-0 text-text-dim" />
      <div className="space-y-2">
        <p className="font-medium text-text">Demo mode — no on-chain transactions</p>
        <p>
          <code className="rounded bg-black/25 px-1 py-0.5 text-xs">DATAMIND_OG_MOCK=1</code> keeps 0G storage and
          registry simulated. Uploads still run AI + Qdrant; tx hashes in the app are placeholders unless you switch
          modes.
        </p>
        <ul className="list-inside list-disc space-y-1 text-xs text-text-dim">
          <li>
            <strong className="text-text-muted">Wallet-signed:</strong> set{" "}
            <code className="rounded bg-black/25 px-1">DATAMIND_WEB3_USER_TX=1</code>, deploy contracts, paste addresses
            into backend + frontend env (see repo <span className="font-mono">docs/WEB3_UPGRADE.md</span>).
            Only <span className="font-mono">NEXT_PUBLIC_DATASET_REGISTRY</span> and{" "}
            <span className="font-mono">NEXT_PUBLIC_DATASET_NFT</span> are required for uploads.
          </li>
          <li>
            <strong className="text-text-muted">Server-signed:</strong> set{" "}
            <code className="rounded bg-black/25 px-1">DATAMIND_OG_MOCK=0</code>,{" "}
            <code className="rounded bg-black/25 px-1">OG_PRIVATE_KEY</code>,{" "}
            <code className="rounded bg-black/25 px-1">DATASET_REGISTRY_ADDRESS</code>.
          </li>
        </ul>
      </div>
    </div>
  );
}
