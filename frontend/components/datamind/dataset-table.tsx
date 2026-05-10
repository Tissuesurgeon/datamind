"use client";

import Link from "next/link";

import type { DatasetMarketplaceItem } from "@/types";
import { QualityBadge } from "@/components/datamind/quality-badge";
import { Badge } from "@/components/ui/badge";
import { cn, compactNumber, shortAddr } from "@/lib/utils";

export function DatasetTable({
  rows,
  className,
}: {
  rows: DatasetMarketplaceItem[];
  className?: string;
}) {
  return (
    <div
      className={cn(
        "overflow-hidden rounded-2xl border border-border-subtle bg-surface-1",
        className
      )}
    >
      <table className="w-full text-sm">
        <thead className="bg-white/[0.02] text-xs uppercase tracking-wider text-text-dim">
          <tr>
            <th className="px-5 py-3 text-left font-medium">Dataset</th>
            <th className="px-3 py-3 text-left font-medium">Category</th>
            <th className="px-3 py-3 text-right font-medium">Rows</th>
            <th className="px-3 py-3 text-right font-medium">Embeddings</th>
            <th className="px-3 py-3 text-center font-medium">Quality</th>
            <th className="px-3 py-3 text-right font-medium">Price</th>
            <th className="px-5 py-3 text-left font-medium">Owner</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border-subtle">
          {rows.map((d) => (
            <tr
              key={d.id}
              className="group transition-colors hover:bg-white/[0.02]"
            >
              <td className="max-w-[260px] px-5 py-3.5">
                <Link
                  href={`/datasets/${d.id}`}
                  className="block truncate font-medium text-text group-hover:text-brand-amber-300"
                >
                  {d.title}
                </Link>
                <p className="mt-0.5 line-clamp-1 text-xs text-text-muted">
                  {(d.tags || []).slice(0, 3).join(" · ")}
                </p>
              </td>
              <td className="px-3 py-3.5">
                <Badge variant="muted">{d.category}</Badge>
              </td>
              <td className="px-3 py-3.5 text-right font-mono text-text-muted">
                {compactNumber(d.rows)}
              </td>
              <td className="px-3 py-3.5 text-right font-mono text-text-muted">
                {compactNumber(d.embeddings_count)}
              </td>
              <td className="px-3 py-3.5">
                <div className="flex items-center justify-center">
                  <QualityBadge grade={d.quality_grade} size="sm" />
                </div>
              </td>
              <td className="px-3 py-3.5 text-right font-mono text-text-muted">
                {d.price_amount != null
                  ? `${d.price_amount} ${d.price_token || "OG"}`
                  : "Free"}
              </td>
              <td className="px-5 py-3.5 font-mono text-xs text-text-muted">
                {shortAddr(d.owner_wallet)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
