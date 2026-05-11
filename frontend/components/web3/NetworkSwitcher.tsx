"use client";

import { useAccount, useSwitchChain } from "wagmi";
import { AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { OG_CHAIN_ID, ogGalileo } from "@/lib/web3/networks";

/**
 * Inline banner displayed when the user is connected to the wrong chain.
 * Renders nothing when the wallet is connected to the configured OG network
 * (or when no wallet is connected at all).
 */
export function NetworkSwitcher() {
  const { chain, isConnected } = useAccount();
  const { switchChain, isPending } = useSwitchChain();

  if (!isConnected) return null;
  if (chain?.id === OG_CHAIN_ID) return null;

  return (
    <div className="flex items-center justify-between gap-3 rounded-lg border border-brand-magenta-500/30 bg-brand-magenta-500/10 px-3 py-2 text-sm">
      <div className="inline-flex items-center gap-2 text-brand-magenta-300">
        <AlertTriangle className="h-4 w-4" />
        <span>
          Connected to {chain?.name ?? "an unsupported network"}. DataMind runs
          on {ogGalileo.name}.
        </span>
      </div>
      <Button
        size="sm"
        variant="muted"
        disabled={isPending}
        onClick={() => switchChain({ chainId: OG_CHAIN_ID })}
      >
        {isPending ? "Switching…" : `Switch to ${ogGalileo.name}`}
      </Button>
    </div>
  );
}
