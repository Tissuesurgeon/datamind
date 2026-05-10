"use client";

import Link from "next/link";
import { ArrowUpRight, Database, Layers, Sparkles, Workflow } from "lucide-react";

import { DatasetTable } from "@/components/datamind/dataset-table";
import { Button } from "@/components/ui/button";
import { useDatasets, useTrainingJobs } from "@/lib/queries";
import { cn, compactNumber } from "@/lib/utils";

const KPIS = [
  { key: "datasets", label: "Datasets", icon: Database, hint: "yours + public seeds" },
  { key: "embeddings", label: "Embeddings", icon: Sparkles, hint: "stored in Qdrant" },
  { key: "training", label: "Training jobs", icon: Workflow, hint: "lifetime runs" },
  { key: "anchored", label: "Anchored on 0G", icon: Layers, hint: "datasets w/ storage_root" },
];

export default function DashboardPage() {
  const { data: datasetsPage } = useDatasets({});
  const { data: jobs } = useTrainingJobs();

  const datasets = datasetsPage?.items || [];
  const totalEmbeddings = datasets.reduce((s, d) => s + (d.embeddings_count || 0), 0);
  const anchored = datasets.filter((d) => d.storage_root).length;

  const kpiValues: Record<string, string> = {
    datasets: compactNumber(datasets.length),
    embeddings: compactNumber(totalEmbeddings),
    training: compactNumber((jobs || []).length),
    anchored: compactNumber(anchored),
  };

  return (
    <div className="space-y-8">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-medium tracking-tight">Dashboard</h1>
          <p className="mt-1 text-sm text-text-muted">
            Your decentralized AI data control plane.
          </p>
        </div>
        <div className="flex gap-2">
          <Button asChild variant="ghost">
            <Link href="/marketplace">
              Marketplace <ArrowUpRight className="h-3.5 w-3.5" />
            </Link>
          </Button>
          <Button asChild variant="gradient">
            <Link href="/upload">Upload dataset</Link>
          </Button>
        </div>
      </header>

      <section className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
        {KPIS.map((k) => (
          <div
            key={k.key}
            className="rounded-2xl border border-border-subtle bg-surface-1 p-5"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase tracking-wider text-text-dim">
                {k.label}
              </span>
              <k.icon className="h-4 w-4 text-text-dim" />
            </div>
            <div className="mt-3 font-mono text-3xl font-medium">{kpiValues[k.key]}</div>
            <div className="mt-1 text-xs text-text-dim">{k.hint}</div>
          </div>
        ))}
      </section>

      <section className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <div>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-medium tracking-tight">Recent datasets</h2>
            <Link href="/marketplace" className="text-sm text-text-muted hover:text-text">
              View all
            </Link>
          </div>
          <DatasetTable rows={(datasets as any).slice(0, 8)} />
        </div>

        <div>
          <h2 className="mb-3 text-lg font-medium tracking-tight">Training jobs</h2>
          <div className="rounded-2xl border border-border-subtle bg-surface-1 p-1">
            <ul className="divide-y divide-border-subtle">
              {(jobs || []).slice(0, 6).map((j) => (
                <li key={j.id} className="flex items-center justify-between gap-3 p-3 text-sm">
                  <div className="min-w-0">
                    <Link
                      href={`/training?id=${j.id}`}
                      className="block truncate font-medium hover:text-brand-amber-300"
                    >
                      {j.name}
                    </Link>
                    <div className="text-xs text-text-dim">{j.base_model}</div>
                  </div>
                  <StatusPill status={j.status} />
                </li>
              ))}
              {(!jobs || jobs.length === 0) && (
                <li className="p-6 text-center text-sm text-text-dim">
                  No jobs yet.{" "}
                  <Link href="/training" className="text-brand-amber-300">
                    Launch one →
                  </Link>
                </li>
              )}
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const palette: Record<string, string> = {
    pending: "border-border-subtle text-text-muted",
    running: "border-brand-amber-500/40 text-brand-amber-300",
    succeeded: "border-emerald-500/40 text-emerald-300",
    failed: "border-red-500/40 text-red-300",
    cancelled: "border-border-subtle text-text-dim",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border bg-white/[0.02] px-2 py-0.5 text-[10px] uppercase tracking-wider",
        palette[status] || palette.pending
      )}
    >
      {status}
    </span>
  );
}
