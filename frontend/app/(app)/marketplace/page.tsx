"use client";

import { useState } from "react";
import { motion } from "framer-motion";

import { DatasetCard } from "@/components/datamind/dataset-card";
import { Button } from "@/components/ui/button";
import { useMarketplace, useTrending } from "@/lib/queries";
import { cn } from "@/lib/utils";

const CHIPS = ["All", "Finance", "NLP", "Web3", "Tabular", "Vision"];
const SORTS = [
  { key: "trending", label: "Trending" },
  { key: "recent", label: "Newest" },
  { key: "quality", label: "Quality" },
  { key: "downloads", label: "Most downloaded" },
];

export default function MarketplacePage() {
  const [category, setCategory] = useState("All");
  const [sort, setSort] = useState("trending");
  const { data, isLoading } = useMarketplace({ category, sort, limit: 30 });
  const { data: trending } = useTrending(3);

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-3xl font-medium tracking-tight">Dataset marketplace</h1>
        <p className="mt-1 max-w-2xl text-sm text-text-muted">
          Discover, license and train on AI-ready datasets — every record
          anchored on 0G with verifiable provenance.
        </p>
      </header>

      {trending && trending.length > 0 && (
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm uppercase tracking-[0.2em] text-text-dim">
              Trending
            </h2>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            {trending.map((d, i) => (
              <DatasetCard key={d.id} dataset={d} trending={i === 0} />
            ))}
          </div>
        </section>
      )}

      <section>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            {CHIPS.map((c) => (
              <Button
                key={c}
                size="sm"
                variant={c === category ? "default" : "ghost"}
                className={cn(c === category ? "" : "text-text-muted")}
                onClick={() => setCategory(c)}
              >
                {c}
              </Button>
            ))}
          </div>
          <div className="flex items-center gap-1">
            {SORTS.map((s) => (
              <Button
                key={s.key}
                size="sm"
                variant={s.key === sort ? "muted" : "ghost"}
                className="text-text-muted"
                onClick={() => setSort(s.key)}
              >
                {s.label}
              </Button>
            ))}
          </div>
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-5 grid gap-4 md:grid-cols-2 lg:grid-cols-3"
        >
          {(data?.items || []).map((d) => (
            <DatasetCard key={d.id} dataset={d} />
          ))}
        </motion.div>
        {!isLoading && (data?.items || []).length === 0 && (
          <div className="mt-12 text-center text-sm text-text-dim">
            No datasets in this category yet — try uploading one.
          </div>
        )}
      </section>
    </div>
  );
}
