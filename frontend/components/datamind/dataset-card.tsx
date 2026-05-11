"use client";

import Link from "next/link";
import { BadgeCheck, Database, Sparkles, TrendingUp, Wallet2 } from "lucide-react";

import type { DatasetMarketplaceItem } from "@/types";
import { Badge } from "@/components/ui/badge";
import { QualityBadge } from "@/components/datamind/quality-badge";
import { cn, compactNumber, shortAddr } from "@/lib/utils";

export function DatasetCard({
  dataset,
  trending = false,
  className,
}: {
  dataset: DatasetMarketplaceItem;
  trending?: boolean;
  className?: string;
}) {
  return (
    <Link
      href={`/datasets/${dataset.id}`}
      className={cn(
        "group relative flex flex-col rounded-2xl border border-border-subtle bg-surface-1 p-5",
        "transition-all hover:border-border-strong hover:shadow-glow-brand hover:-translate-y-0.5",
        className
      )}
    >
      {trending && (
        <div className="absolute -top-2 right-4">
          <Badge variant="amber" className="gap-1">
            <TrendingUp className="h-3 w-3" /> Trending
          </Badge>
        </div>
      )}

      {dataset.onchain_id != null && (
        <div className="absolute -top-2 left-4">
          <Badge variant="magenta" className="gap-1" title="Dataset minted on-chain">
            <BadgeCheck className="h-3 w-3" /> NFT
          </Badge>
        </div>
      )}

      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <Badge variant="muted" className="mb-2 uppercase tracking-wider text-[10px]">
            {dataset.category}
          </Badge>
          <h3 className="truncate text-base font-medium tracking-tight">{dataset.title}</h3>
          <p className="mt-1 line-clamp-2 text-sm text-text-muted">
            {dataset.description || "Decentralized AI-ready dataset on DataMind."}
          </p>
        </div>
        <QualityBadge grade={dataset.quality_grade} />
      </div>

      <div className="mt-4 flex flex-wrap gap-1.5">
        {(dataset.tags || []).slice(0, 4).map((t) => (
          <span
            key={t}
            className="rounded-md border border-border-subtle bg-white/[0.02] px-2 py-0.5 text-[11px] text-text-muted"
          >
            {t}
          </span>
        ))}
      </div>

      <div className="mt-5 flex items-center justify-between gap-2 border-t border-border-subtle pt-4 text-xs text-text-muted">
        <span className="inline-flex items-center gap-1.5">
          <Database className="h-3.5 w-3.5" /> {compactNumber(dataset.rows)} rows
        </span>
        <span className="inline-flex items-center gap-1.5">
          <Sparkles className="h-3.5 w-3.5 text-brand-amber-300" />
          {compactNumber(dataset.embeddings_count)} vecs
        </span>
        <span className="inline-flex items-center gap-1.5">
          <Wallet2 className="h-3.5 w-3.5" /> {shortAddr(dataset.owner_wallet)}
        </span>
      </div>

      <div className="mt-4 flex items-center justify-between text-xs">
        <div className="font-mono text-text-muted">
          {dataset.price_amount != null
            ? `${dataset.price_amount} ${dataset.price_token || "OG"}`
            : "Free"}
        </div>
        <div className="text-text-dim">
          {compactNumber(dataset.downloads)} downloads
        </div>
      </div>
    </Link>
  );
}
