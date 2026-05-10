"use client";

import { useState } from "react";
import Link from "next/link";
import { Search as SearchIcon, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { QualityBadge } from "@/components/datamind/quality-badge";
import { useSearch } from "@/lib/queries";
import { cn, compactNumber } from "@/lib/utils";

export default function SearchPage() {
  const [query, setQuery] = useState("crypto sentiment trading");
  const [mode, setMode] = useState<"semantic" | "hybrid">("semantic");
  const [minScore, setMinScore] = useState(0.5);
  const search = useSearch();

  const submit = async () => {
    if (!query.trim()) return;
    await search.mutateAsync({ query, mode, min_score: minScore, limit: 20 });
  };

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-3xl font-medium tracking-tight">Semantic search</h1>
        <p className="mt-1 max-w-2xl text-sm text-text-muted">
          Find datasets by meaning, not just keywords. Hybrid mode reranks vector
          hits with a Postgres keyword pass.
        </p>
      </header>

      <div className="rounded-2xl border border-border-subtle bg-surface-1 p-5">
        <div className="flex flex-col gap-3 md:flex-row md:items-center">
          <div className="relative flex-1">
            <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-dim" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submit()}
              placeholder="Search the dataset economy…"
              className="pl-9 text-base"
            />
          </div>
          <Tabs value={mode} onValueChange={(v) => setMode(v as any)}>
            <TabsList>
              <TabsTrigger value="semantic">Semantic</TabsTrigger>
              <TabsTrigger value="hybrid">Hybrid</TabsTrigger>
            </TabsList>
          </Tabs>
          <Button onClick={submit} disabled={search.isPending} variant="gradient">
            <Sparkles className="h-4 w-4" />
            Search
          </Button>
        </div>
        <div className="mt-4 flex items-center gap-3 text-xs text-text-muted">
          <span className="text-text-dim">Min similarity</span>
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={minScore}
            onChange={(e) => setMinScore(parseFloat(e.target.value))}
            className="flex-1 accent-brand-amber-500"
          />
          <span className="w-12 font-mono">{minScore.toFixed(2)}</span>
        </div>
      </div>

      <div>
        {search.isPending && <p className="text-sm text-text-muted">Searching…</p>}
        {search.data && (
          <>
            <div className="mb-3 flex items-center gap-3 text-xs text-text-dim">
              <span>{search.data.results.length} results</span>
              <span>·</span>
              <span>{search.data.took_ms} ms</span>
              <span>·</span>
              <span className="font-mono">{search.data.mode}</span>
            </div>
            <ul className="grid gap-3">
              {search.data.results.map((r) => (
                <li
                  key={r.dataset_id}
                  className={cn(
                    "rounded-2xl border border-border-subtle bg-surface-1 p-4",
                    "transition-colors hover:border-border-strong"
                  )}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <Link
                        href={`/datasets/${r.dataset_id}`}
                        className="text-base font-medium hover:text-brand-amber-300"
                      >
                        {r.title}
                      </Link>
                      <div className="mt-1 text-xs text-text-dim">
                        {r.category} · {compactNumber(r.embeddings_count)} vectors
                      </div>
                      <p className="mt-2 line-clamp-2 text-sm text-text-muted">{r.snippet}</p>
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      <QualityBadge grade={r.quality_grade} size="sm" />
                      <span className="rounded-md bg-white/[0.04] px-2 py-0.5 font-mono text-xs">
                        {r.score.toFixed(3)}
                      </span>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
            {search.data.results.length === 0 && (
              <p className="mt-12 text-center text-sm text-text-dim">
                Nothing matches above your similarity threshold. Try lowering it
                or switching to hybrid mode.
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
