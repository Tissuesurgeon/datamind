"use client";

import { useEffect, useRef } from "react";
import { useAccount } from "wagmi";

import { api } from "@/lib/api";
import { useAuthStore, type UserOut } from "@/lib/auth-store";

/**
 * Bridges the wagmi-connected wallet to the existing DataMind backend auth
 * session. Whenever a wallet connects (or switches accounts), we POST to the
 * `/auth/privy/verify` endpoint in demo mode using the real on-chain address.
 * The backend treats `privy_token === "mock"` as demo and issues a JWT bound
 * to the connected wallet — so the rest of the app (uploads, training,
 * marketplace) keeps working unchanged.
 *
 * No UI of its own; mount once near the top of the tree.
 */
export function WalletSessionBridge() {
  const { address, isConnected, status } = useAccount();
  const { token, user, setSession, signOut } = useAuthStore();
  const lastSyncedRef = useRef<string | null>(null);
  /** True only after wagmi has been connected at least once — avoids wiping mock/JWT-only sessions. */
  const hadLiveWalletRef = useRef(false);

  useEffect(() => {
    // While wagmi is still connecting/reconnecting, `isConnected` is often false — do not sign out.
    if (status === "connecting" || status === "reconnecting") {
      return;
    }

    if (!isConnected || !address) {
      // Clear JWT only when the user had a real wallet session and then disconnected.
      // Mock `signIn()` (no extension) must keep working; initial `disconnected` must not erase persisted auth.
      if (hadLiveWalletRef.current) {
        if (token) signOut();
        hadLiveWalletRef.current = false;
      }
      lastSyncedRef.current = null;
      return;
    }

    hadLiveWalletRef.current = true;

    const normalized = address.toLowerCase();
    if (lastSyncedRef.current === normalized) return;

    // If the existing session already belongs to this address, no exchange.
    if (
      token &&
      user?.wallet_address &&
      user.wallet_address.toLowerCase() === normalized
    ) {
      lastSyncedRef.current = normalized;
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const res = await api.post<{ access_token: string; user: UserOut }>(
          "/auth/privy/verify",
          {
            privy_token: "mock",
            wallet_address: address,
            display_name: null,
          },
          { auth: false }
        );
        if (cancelled) return;
        setSession(res.access_token, res.user);
        lastSyncedRef.current = normalized;
      } catch (err) {
        if (process.env.NODE_ENV !== "production") {
          // eslint-disable-next-line no-console
          console.warn("[datamind] wallet→session bridge failed", err);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [isConnected, address, status, token, user, setSession, signOut]);

  return null;
}
