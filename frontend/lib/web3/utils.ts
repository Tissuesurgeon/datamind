import type { Address, Hex } from "viem";

import { OG_EXPLORER_URL } from "./networks";

export function shortAddress(addr?: string | null, head = 6, tail = 4): string {
  if (!addr) return "";
  if (addr.length <= head + tail + 2) return addr;
  return `${addr.slice(0, head)}…${addr.slice(-tail)}`;
}

export function txUrl(hash?: string | null): string | null {
  if (!hash) return null;
  return `${OG_EXPLORER_URL.replace(/\/+$/, "")}/tx/${hash}`;
}

export function addressUrl(addr?: string | null): string | null {
  if (!addr) return null;
  return `${OG_EXPLORER_URL.replace(/\/+$/, "")}/address/${addr}`;
}

export function tokenUrl(contract: string, tokenId: string | number): string {
  const base = OG_EXPLORER_URL.replace(/\/+$/, "");
  // 0G Galileo ChainScan is Routescan-style: /nft/{address}/{id}
  // (not legacy Blockscout /token/{address}/instance/{id}.)
  return `${base}/nft/${contract}/${tokenId}`;
}

export function ensure0x(hex: string): Hex {
  return (hex.startsWith("0x") ? hex : `0x${hex}`) as Hex;
}

/** Pad an arbitrary hex string to 32 bytes (right-justified). */
export function bytes32(hex: string): Hex {
  const stripped = hex.replace(/^0x/, "");
  if (stripped.length > 64) {
    return ensure0x(stripped.slice(-64));
  }
  return ensure0x(stripped.padStart(64, "0"));
}

export function isAddress(value?: string | null): value is Address {
  return Boolean(value && /^0x[0-9a-fA-F]{40}$/.test(value));
}
