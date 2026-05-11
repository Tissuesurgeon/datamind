import { http, createConfig } from "wagmi";
import { injected } from "wagmi/connectors";
import { getDefaultConfig } from "@rainbow-me/rainbowkit";
import type { CreateConnectorFn } from "wagmi";

import { OG_RPC_URL, SUPPORTED_CHAINS, ogGalileo } from "./networks";

const PROJECT_ID =
  process.env.NEXT_PUBLIC_WC_PROJECT_ID ||
  process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID ||
  "";

/**
 * RainbowKit-flavoured wagmi config. We prefer `getDefaultConfig` so the
 * shipped wallet list (MetaMask, Coinbase, WalletConnect) just works, and we
 * gracefully fall back to a hand-rolled `createConfig` when no WalletConnect
 * project id is set (avoids RainbowKit's hard-fail in mock/demo mode).
 */
export function buildWagmiConfig() {
  if (PROJECT_ID) {
    return getDefaultConfig({
      appName: "DataMind",
      projectId: PROJECT_ID,
      chains: SUPPORTED_CHAINS as unknown as readonly [
        (typeof SUPPORTED_CHAINS)[number],
        ...(typeof SUPPORTED_CHAINS)[number][],
      ],
      ssr: true,
      transports: {
        [ogGalileo.id]: http(OG_RPC_URL),
      },
    });
  }

  // Demo mode — injected (browser extension) only. Omit WalletConnect when there is
  // no project id so Reown/AppKit does not spam 403 config fetches.
  return createConfig({
    chains: SUPPORTED_CHAINS as unknown as readonly [
      (typeof SUPPORTED_CHAINS)[number],
      ...(typeof SUPPORTED_CHAINS)[number][],
    ],
    transports: {
      [ogGalileo.id]: http(OG_RPC_URL),
    },
    connectors: [injected({ shimDisconnect: true })] as unknown as CreateConnectorFn[],
    ssr: true,
  });
}

export const WEB3_ENABLED = Boolean(
  process.env.NEXT_PUBLIC_OG_RPC_URL || process.env.NEXT_PUBLIC_DATASET_REGISTRY
);
