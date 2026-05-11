"use client";

import { CheckCircle2, ExternalLink, Loader2, XCircle } from "lucide-react";
import Link from "next/link";

import { cn } from "@/lib/utils";
import { txUrl } from "@/lib/web3/utils";

export type TxState = "idle" | "pending" | "confirming" | "success" | "error";

export type TxStepProps = {
  label: string;
  state: TxState;
  hash?: string | null;
  error?: string | null;
};

const stateStyles: Record<TxState, string> = {
  idle: "text-text-dim border-border-subtle",
  pending: "text-brand-amber-300 border-brand-amber-500/40",
  confirming: "text-brand-amber-300 border-brand-amber-500/40",
  success: "text-emerald-300 border-emerald-500/30",
  error: "text-brand-magenta-300 border-brand-magenta-500/40",
};

function StateIcon({ state }: { state: TxState }) {
  if (state === "pending" || state === "confirming") {
    return <Loader2 className="h-4 w-4 animate-spin" />;
  }
  if (state === "success") return <CheckCircle2 className="h-4 w-4" />;
  if (state === "error") return <XCircle className="h-4 w-4" />;
  return <span className="h-2.5 w-2.5 rounded-full border border-current" />;
}

/** Single transaction status row — label, state pill, optional explorer link. */
export function TxStep({ label, state, hash, error }: TxStepProps) {
  const href = txUrl(hash);
  return (
    <div
      className={cn(
        "flex items-center justify-between gap-3 rounded-md border bg-surface-1 px-3 py-2 text-sm",
        stateStyles[state]
      )}
    >
      <div className="flex min-w-0 items-center gap-2">
        <StateIcon state={state} />
        <span className="truncate text-text">{label}</span>
      </div>
      <div className="flex items-center gap-2 text-xs text-text-muted">
        {error ? <span className="truncate text-brand-magenta-300">{error}</span> : null}
        {href ? (
          <Link
            href={href}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 font-mono hover:text-brand-amber-300"
          >
            {hash?.slice(0, 8)}…
            <ExternalLink className="h-3 w-3" />
          </Link>
        ) : null}
      </div>
    </div>
  );
}

/** A vertical list of transaction steps — drop-in for upload / training flows. */
export function TransactionStatus({ steps }: { steps: TxStepProps[] }) {
  return (
    <div className="space-y-2">
      {steps.map((s) => (
        <TxStep key={s.label} {...s} />
      ))}
    </div>
  );
}
