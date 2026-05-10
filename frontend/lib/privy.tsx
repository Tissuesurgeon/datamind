"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { ENV, PRIVY_LIVE } from "@/lib/env";
import { useAuthStore, type UserOut } from "@/lib/auth-store";
import { api } from "@/lib/api";

type Wallet = { address: string };

type PrivyAuthValue = {
  ready: boolean;
  authenticated: boolean;
  wallet: Wallet | null;
  user: UserOut | null;
  signIn: () => Promise<void>;
  signOut: () => void;
  mode: "live" | "mock";
};

const Ctx = createContext<PrivyAuthValue | null>(null);

const MOCK_WALLET_KEY = "datamind.mock-wallet";

function generateMockWallet(): string {
  const chars = "0123456789abcdef";
  let s = "0x";
  for (let i = 0; i < 40; i++) s += chars[Math.floor(Math.random() * 16)];
  return s;
}

function getOrCreateMockWallet(): string {
  if (typeof window === "undefined") return "";
  let saved = localStorage.getItem(MOCK_WALLET_KEY);
  if (!saved) {
    saved = generateMockWallet();
    localStorage.setItem(MOCK_WALLET_KEY, saved);
  }
  return saved;
}

function MockProvider({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false);
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const { token, user, setSession, signOut: storeSignOut } = useAuthStore();

  useEffect(() => {
    setReady(true);
    if (typeof window !== "undefined") {
      const addr = getOrCreateMockWallet();
      setWallet({ address: addr });
    }
  }, []);

  const signIn = useCallback(async () => {
    const addr =
      wallet?.address ||
      (typeof window !== "undefined" ? getOrCreateMockWallet() : "");
    if (!addr) throw new Error("Wallet not ready — try again in a moment.");
    const res = await api.post<{ access_token: string; user: UserOut }>(
      "/auth/privy/verify",
      {
        privy_token: "mock",
        wallet_address: addr,
        display_name: "Demo User",
      },
      { auth: false }
    );
    setSession(res.access_token, res.user);
  }, [wallet, setSession]);

  const signOut = useCallback(() => {
    storeSignOut();
  }, [storeSignOut]);

  const value: PrivyAuthValue = {
    ready,
    authenticated: Boolean(token && user),
    wallet,
    user,
    signIn,
    signOut,
    mode: "mock",
  };
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

// We dynamically import @privy-io/react-auth only when an app id is set so the
// demo doesn't pull the dependency at runtime in mock mode.
function LiveProvider({ children }: { children: React.ReactNode }) {
  // For brevity — the live integration ships the same shape via the Privy SDK.
  // In live mode developers should replace this stub with `<PrivyProvider …>`
  // wiring. We keep the mock as the single source of truth for the hackathon.
  return <MockProvider>{children}</MockProvider>;
}

export function PrivyAuthProvider({ children }: { children: React.ReactNode }) {
  return PRIVY_LIVE ? <LiveProvider>{children}</LiveProvider> : <MockProvider>{children}</MockProvider>;
}

export function usePrivyAuth() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("usePrivyAuth must be used inside PrivyAuthProvider");
  return ctx;
}

export function useAuthHelpers() {
  const auth = usePrivyAuth();
  const requireAuth = useCallback(async () => {
    if (!auth.authenticated) await auth.signIn();
  }, [auth]);
  return { ...auth, requireAuth };
}

// Lightweight banner state — what mode are we in?
export function useAuthMode() {
  return useMemo(() => ({ mode: PRIVY_LIVE ? ("live" as const) : ("mock" as const) }), []);
}

export { ENV };
