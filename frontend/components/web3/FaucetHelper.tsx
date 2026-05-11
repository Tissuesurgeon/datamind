"use client";

import { useState } from "react";
import { useAccount, useBalance } from "wagmi";
import { Copy, ExternalLink, RefreshCw } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { OG_CHAIN_ID, OG_FAUCET_URL, ogGalileo } from "@/lib/web3/networks";
import { shortAddress } from "@/lib/web3/utils";

/**
 * Onboarding card for 0G testnet faucet. Shows the connected wallet, current
 * balance, copy-to-clipboard, and a deep-link to the official faucet.
 */
export function FaucetHelper() {
  const { address, isConnected } = useAccount();
  const { data, refetch, isFetching } = useBalance({
    address,
    chainId: OG_CHAIN_ID,
    query: { enabled: Boolean(address) },
  });
  const [copied, setCopied] = useState(false);

  const balanceLabel = data
    ? `${Number(data.formatted).toFixed(4)} ${data.symbol}`
    : isFetching
    ? "…"
    : "0";

  const copy = async () => {
    if (!address) return;
    try {
      await navigator.clipboard.writeText(address);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
      toast.success("Address copied");
    } catch {
      toast.error("Clipboard blocked");
    }
  };

  return (
    <div className="rounded-2xl border border-border-subtle bg-surface-1 p-5">
      <header className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-medium tracking-tight">Get {ogGalileo.name} tokens</h3>
          <p className="mt-1 text-xs text-text-muted">
            Testnet 0G is required to publish datasets and launch training jobs.
          </p>
        </div>
        <a
          href={OG_FAUCET_URL}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 rounded-md border border-border-subtle bg-surface-2 px-2.5 py-1 text-xs text-text-muted hover:text-brand-amber-300"
        >
          Open faucet
          <ExternalLink className="h-3 w-3" />
        </a>
      </header>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div className="rounded-lg border border-border-subtle bg-surface-0 p-3">
          <div className="text-[10px] uppercase tracking-[0.22em] text-text-dim">
            Wallet
          </div>
          <div className="mt-1 flex items-center justify-between">
            <span className="font-mono text-xs text-text">
              {isConnected ? shortAddress(address) : "Not connected"}
            </span>
            {isConnected ? (
              <button
                type="button"
                onClick={copy}
                className="text-text-dim hover:text-brand-amber-300"
                title="Copy address"
              >
                <Copy className={`h-3.5 w-3.5 ${copied ? "text-brand-amber-300" : ""}`} />
              </button>
            ) : null}
          </div>
        </div>
        <div className="rounded-lg border border-border-subtle bg-surface-0 p-3">
          <div className="flex items-center justify-between">
            <div className="text-[10px] uppercase tracking-[0.22em] text-text-dim">
              Balance
            </div>
            {isConnected ? (
              <button
                type="button"
                onClick={() => refetch()}
                className="text-text-dim hover:text-brand-amber-300"
                title="Refresh balance"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? "animate-spin" : ""}`} />
              </button>
            ) : null}
          </div>
          <div className="mt-1 font-mono text-xs text-text">{balanceLabel}</div>
        </div>
      </div>

      {!isConnected ? (
        <p className="mt-3 text-xs text-text-dim">
          Connect a wallet to copy your address and refresh the balance.
        </p>
      ) : (
        <ol className="mt-3 space-y-1 text-xs text-text-muted">
          <li>1. Copy your wallet address.</li>
          <li>2. Open the {ogGalileo.name} faucet and request tokens.</li>
          <li>3. Refresh — fees for publishing and training will then succeed.</li>
        </ol>
      )}

      <div className="mt-4">
        <Button asChild size="sm" variant="muted">
          <a href={OG_FAUCET_URL} target="_blank" rel="noreferrer">
            Get testnet 0G
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        </Button>
      </div>
    </div>
  );
}
