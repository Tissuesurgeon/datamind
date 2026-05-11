"use client";

import { useMemo } from "react";
import { WagmiProvider } from "wagmi";
import { RainbowKitProvider, darkTheme } from "@rainbow-me/rainbowkit";

import { getWagmiConfig } from "@/lib/web3/wagmi";

import "@rainbow-me/rainbowkit/styles.css";

/**
 * Wraps the app with wagmi + RainbowKit. Place inside `Providers` AFTER the
 * shared `QueryClientProvider` (wagmi v2 reuses TanStack Query).
 */
export function Web3Provider({ children }: { children: React.ReactNode }) {
  const config = useMemo(() => getWagmiConfig(), []);

  return (
    <WagmiProvider config={config}>
      <RainbowKitProvider
        theme={darkTheme({
          accentColor: "#F5A524",
          accentColorForeground: "#0A0A0B",
          borderRadius: "medium",
          fontStack: "system",
        })}
        showRecentTransactions
        modalSize="compact"
      >
        {children}
      </RainbowKitProvider>
    </WagmiProvider>
  );
}
