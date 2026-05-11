"use client";

import { ConnectButton } from "@rainbow-me/rainbowkit";
import { Wallet2 } from "lucide-react";

import { Button } from "@/components/ui/button";

/**
 * Thin wrapper around RainbowKit's `ConnectButton`. We render our own button
 * shell so the wallet pill matches the rest of the DataMind UI (no white
 * RainbowKit chrome bleeding into our dark theme).
 */
export function WalletConnect({
  size = "default",
}: {
  size?: "sm" | "default" | "lg";
}) {
  return (
    <ConnectButton.Custom>
      {({
        account,
        chain,
        openAccountModal,
        openChainModal,
        openConnectModal,
        authenticationStatus,
        mounted,
      }) => {
        const ready =
          mounted && authenticationStatus !== "loading";
        const connected =
          ready &&
          account &&
          chain &&
          (!authenticationStatus || authenticationStatus === "authenticated");

        return (
          <div
            aria-hidden={!ready}
            style={{
              opacity: ready ? 1 : 0,
              pointerEvents: ready ? "auto" : "none",
              userSelect: ready ? "auto" : "none",
            }}
            className="inline-flex items-center gap-2"
          >
            {(() => {
              if (!connected) {
                return (
                  <Button size={size} onClick={openConnectModal} type="button">
                    <Wallet2 className="h-4 w-4" />
                    Connect wallet
                  </Button>
                );
              }
              if (chain.unsupported) {
                return (
                  <Button
                    size={size}
                    variant="muted"
                    onClick={openChainModal}
                    type="button"
                    className="text-brand-magenta-300"
                  >
                    Wrong network
                  </Button>
                );
              }
              return (
                <div className="inline-flex items-center gap-1.5 rounded-lg border border-border-subtle bg-surface-1 px-2 py-1 text-sm">
                  <button
                    type="button"
                    onClick={openChainModal}
                    className="font-mono text-[11px] uppercase tracking-[0.18em] text-text-muted hover:text-brand-amber-300"
                    title={chain.name}
                  >
                    {chain.name}
                  </button>
                  <span className="text-text-dim">/</span>
                  <button
                    type="button"
                    onClick={openAccountModal}
                    className="font-mono text-xs text-text hover:text-brand-amber-300"
                  >
                    {account.displayName}
                  </button>
                </div>
              );
            })()}
          </div>
        );
      }}
    </ConnectButton.Custom>
  );
}
