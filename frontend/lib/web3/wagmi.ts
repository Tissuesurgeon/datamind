import type { Config } from "wagmi";

import { buildWagmiConfig } from "./config";

let _config: Config | null = null;

/** Singleton wagmi config used by `WagmiProvider` and any direct wagmi action. */
export function getWagmiConfig(): Config {
  if (_config) return _config;
  _config = buildWagmiConfig();
  return _config;
}
