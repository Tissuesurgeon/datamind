"use client";

import { useAccount, useBalance } from "wagmi";
import { Coins } from "lucide-react";

import { OG_CHAIN_ID } from "@/lib/web3/networks";

/** Compact 0G balance pill — shows nothing when the wallet is not connected. */
export function WalletBalance() {
  const { address, isConnected } = useAccount();
  const { data, isLoading } = useBalance({
    address,
    chainId: OG_CHAIN_ID,
    query: { enabled: Boolean(address) },
  });

  if (!isConnected || !address) return null;

  const formatted = data
    ? `${Number(data.formatted).toFixed(3)} ${data.symbol}`
    : isLoading
    ? "…"
    : "0 0G";

  return (
    <div className="inline-flex items-center gap-1.5 rounded-lg border border-border-subtle bg-surface-1 px-2 py-1 font-mono text-xs text-text-muted">
      <Coins className="h-3.5 w-3.5 text-brand-amber-300" />
      <span>{formatted}</span>
    </div>
  );
}
