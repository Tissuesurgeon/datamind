"use client";

import { useState } from "react";
import { LogOut, Wallet2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { useAuthHelpers } from "@/lib/privy";
import { shortAddr } from "@/lib/utils";

export function WalletButton({ size = "default" }: { size?: "sm" | "default" | "lg" }) {
  const { authenticated, wallet, signIn, signOut, ready } = useAuthHelpers();
  const [busy, setBusy] = useState(false);

  if (!ready) return null;

  if (!authenticated) {
    return (
      <Button
        size={size}
        variant="default"
        disabled={busy}
        onClick={async () => {
          try {
            setBusy(true);
            await signIn();
            toast.success("Signed in");
          } catch (e) {
            toast.error(e instanceof Error ? e.message : "Sign-in failed");
          } finally {
            setBusy(false);
          }
        }}
      >
        <Wallet2 className="h-4 w-4" />
        {busy ? "Signing in…" : "Connect wallet"}
      </Button>
    );
  }

  return (
    <div className="inline-flex items-center gap-1.5 rounded-lg border border-border-subtle bg-surface-1 pl-3 pr-1 text-sm">
      <span className="font-mono text-xs text-text-muted">
        {shortAddr(wallet?.address)}
      </span>
      <Button
        variant="muted"
        size="icon"
        className="h-7 w-7"
        title="Sign out"
        onClick={() => {
          signOut();
          toast("Signed out");
        }}
      >
        <LogOut className="h-3.5 w-3.5" />
      </Button>
    </div>
  );
}
