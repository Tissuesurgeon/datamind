import type { Chain } from "viem";

const DEFAULT_RPC = "https://evmrpc-testnet.0g.ai";
const DEFAULT_EXPLORER = "https://chainscan-galileo.0g.ai";

export const OG_CHAIN_ID = Number(process.env.NEXT_PUBLIC_CHAIN_ID || "16602");
export const OG_RPC_URL = process.env.NEXT_PUBLIC_OG_RPC_URL || DEFAULT_RPC;
export const OG_EXPLORER_URL =
  process.env.NEXT_PUBLIC_OG_EXPLORER_URL || DEFAULT_EXPLORER;
export const OG_FAUCET_URL =
  process.env.NEXT_PUBLIC_OG_FAUCET_URL || "https://faucet.0g.ai";

/**
 * 0G Galileo testnet chain config consumed by wagmi/viem. Override any field
 * from `.env` (NEXT_PUBLIC_*) to point at a different network without touching
 * code.
 */
export const ogGalileo = {
  id: OG_CHAIN_ID,
  name: "0G Galileo",
  nativeCurrency: {
    name: "0G",
    symbol: "0G",
    decimals: 18,
  },
  rpcUrls: {
    default: { http: [OG_RPC_URL] },
    public: { http: [OG_RPC_URL] },
  },
  blockExplorers: {
    default: { name: "0G Chainscan", url: OG_EXPLORER_URL },
  },
  testnet: true,
} as const satisfies Chain;

export const SUPPORTED_CHAINS = [ogGalileo] as const;
