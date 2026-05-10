"use client";

import { use } from "react";
import Link from "next/link";
import { ArrowLeft, ExternalLink, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { QualityBadge } from "@/components/datamind/quality-badge";
import { useDataset } from "@/lib/queries";
import { compactNumber, shortHash } from "@/lib/utils";

export default function DatasetDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data, isLoading } = useDataset(id);

  if (isLoading) {
    return <div className="text-text-muted">Loading…</div>;
  }
  if (!data) {
    return (
      <div className="text-text-muted">
        Dataset not found.{" "}
        <Link href="/marketplace" className="text-brand-amber-300">
          Back to marketplace
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <Link
        href="/marketplace"
        className="inline-flex items-center gap-1.5 text-sm text-text-muted hover:text-text"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back
      </Link>

      <header className="flex flex-wrap items-start justify-between gap-6">
        <div>
          <div className="flex items-center gap-2">
            <Badge variant="muted">{data.category}</Badge>
            {data.tags.slice(0, 4).map((t) => (
              <Badge key={t} variant="outline">
                {t}
              </Badge>
            ))}
          </div>
          <h1 className="mt-3 max-w-3xl text-3xl font-medium tracking-tight md:text-4xl">
            {data.title}
          </h1>
          <p className="mt-3 max-w-2xl text-sm text-text-muted">{data.description}</p>
        </div>
        <div className="flex items-center gap-3">
          <QualityBadge grade={data.quality_grade} size="lg" />
          <Button asChild variant="gradient">
            <Link href={`/training?dataset=${data.id}`}>
              <Sparkles className="h-4 w-4" /> Launch fine-tune
            </Link>
          </Button>
        </div>
      </header>

      <section className="grid gap-3 md:grid-cols-4">
        <Stat label="Rows" value={compactNumber(data.rows)} />
        <Stat label="Columns" value={compactNumber(data.columns)} />
        <Stat label="Embeddings" value={compactNumber(data.embeddings_count)} />
        <Stat label="Quality" value={`${(data.quality_score ?? 0).toFixed(2)}`} />
      </section>

      <section className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <div className="space-y-6">
          <Card title="Summary">
            <p className="text-sm text-text-muted">
              {data.summary || "Awaiting AI summary…"}
            </p>
          </Card>

          {data.semantic_tags && data.semantic_tags.length > 0 && (
            <Card title="Semantic tags">
              <div className="flex flex-wrap gap-1.5">
                {data.semantic_tags.map((t) => (
                  <Badge key={t} variant="amber">
                    {t}
                  </Badge>
                ))}
              </div>
            </Card>
          )}

          {data.topics && data.topics.length > 0 && (
            <Card title="Topics">
              <ul className="space-y-2">
                {data.topics.slice(0, 6).map((t) => (
                  <li key={t.label} className="flex items-center justify-between gap-3">
                    <span className="text-sm">{t.label}</span>
                    <div className="flex items-center gap-2 text-xs text-text-muted">
                      <span className="h-2 w-32 overflow-hidden rounded-full bg-white/[0.06]">
                        <span
                          className="block h-full bg-gradient-brand"
                          style={{ width: `${Math.round(t.weight * 100)}%` }}
                        />
                      </span>
                      <span className="font-mono">{(t.weight * 100).toFixed(0)}%</span>
                    </div>
                  </li>
                ))}
              </ul>
            </Card>
          )}

          {data.sample_rows && data.sample_rows.length > 0 && (
            <Card title="Sample rows">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <tbody className="divide-y divide-border-subtle">
                    {data.sample_rows.slice(0, 8).map((r, i) => (
                      <tr key={i}>
                        {Object.entries(r).slice(0, 4).map(([k, v]) => (
                          <td
                            key={k}
                            className="max-w-[260px] truncate px-3 py-2 align-top text-xs text-text-muted"
                          >
                            <span className="text-text-dim">{k}=</span>
                            {String(v)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </div>

        <div className="space-y-6">
          <Card title="Provenance">
            <Row label="Owner" value={data.owner_wallet} mono />
            <Row label="Storage root" value={shortHash(data.storage_root || "—")} mono />
            <Row label="Tx hash" value={shortHash(data.storage_tx_hash || "—")} mono />
            <Row label="Chain id" value={"16602"} mono />
            <Row label="On-chain id" value={data.onchain_id ? `#${data.onchain_id}` : "—"} mono />
            <Row label="Metadata URI" value={shortHash(data.metadata_uri || "—")} mono />
          </Card>

          <Card title="Marketplace">
            <Row
              label="Price"
              value={
                data.price_amount != null
                  ? `${data.price_amount} ${data.price_token || "OG"}`
                  : "Free"
              }
            />
            <Row label="License" value={data.license_kind || "—"} />
            <Row label="Downloads" value={compactNumber(data.downloads)} />
            {data.storage_root && (
              <a
                href={`/api/v1/storage/${data.storage_root}`}
                target="_blank"
                rel="noreferrer"
                className="mt-3 inline-flex items-center gap-1.5 text-sm text-brand-amber-300 hover:underline"
              >
                Fetch from 0G <ExternalLink className="h-3.5 w-3.5" />
              </a>
            )}
          </Card>
        </div>
      </section>
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-border-subtle bg-surface-1 p-5">
      <div className="mb-3 text-xs uppercase tracking-[0.18em] text-text-dim">
        {title}
      </div>
      {children}
    </div>
  );
}

function Row({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between border-b border-border-subtle py-2 last:border-0">
      <span className="text-xs text-text-dim">{label}</span>
      <span className={"text-xs " + (mono ? "font-mono " : "") + "text-text"}>{value}</span>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border-subtle bg-surface-1 p-5">
      <div className="text-xs uppercase tracking-wider text-text-dim">{label}</div>
      <div className="mt-2 font-mono text-2xl text-text">{value}</div>
    </div>
  );
}
