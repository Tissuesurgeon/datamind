"use client";

import { useState } from "react";
import { motion } from "framer-motion";

import { SectionHeader } from "@/components/datamind/section-header";
import { DatasetCard } from "@/components/datamind/dataset-card";
import { Button } from "@/components/ui/button";
import { LANDING } from "@/content/landing";
import { useTrending } from "@/lib/queries";
import type { DatasetMarketplaceItem } from "@/types";
import { cn } from "@/lib/utils";

const FALLBACK_ITEMS: DatasetMarketplaceItem[] = [
  // We embed the same demo set so the section renders even without the backend up.
  ...[
    { title: "Crypto Twitter Sentiment", category: "Web3", grade: "A", price: 12, rows: 10847, tags: ["sentiment", "twitter"] },
    { title: "DeFi Protocol Documentation", category: "NLP", grade: "A", price: 24, rows: 26544, tags: ["defi", "rag"] },
    { title: "Onchain Anomaly Events", category: "Web3", grade: "B", price: 18, rows: 8120, tags: ["mev", "anomalies"] },
    { title: "Solana DEX Trades — 30d", category: "Finance", grade: "B", price: 30, rows: 1240006, tags: ["solana", "dex"] },
    { title: "Ethereum NFT Metadata", category: "Vision", grade: "B", price: 9, rows: 4012300, tags: ["nft", "eth"] },
    { title: "Lending Liquidations", category: "Finance", grade: "C", price: 6, rows: 41902, tags: ["lending", "risk"] },
  ].map((d, i) => ({
    id: `fallback-${i}`,
    title: d.title,
    category: d.category,
    tags: d.tags,
    quality_score: 0.85,
    quality_grade: d.grade as "A" | "B" | "C",
    ai_readiness: 0.85,
    rows: d.rows,
    embeddings_count: Math.floor(d.rows * 0.5),
    downloads: 800 - i * 80,
    visibility: "public" as const,
    status: "ready" as const,
    progress: 100,
    storage_root: `0x${"0".repeat(8)}…${i.toString(16).padStart(4, "0")}`,
    onchain_id: i + 1,
    owner_wallet: "0xdemo000000000000000000000000000000000001",
    created_at: new Date().toISOString(),
    description: null,
    price_amount: d.price,
    price_token: "OG",
    license_kind: i % 2 === 0 ? "commercial" : "personal",
  })),
];

export function MarketplacePreview() {
  const { eyebrow, title, description, chips } = LANDING.marketplacePreview;
  const [active, setActive] = useState<string>(chips[0]);
  const { data, isLoading } = useTrending(6);
  const items = (data && data.length > 0 ? data : FALLBACK_ITEMS).filter((i) => {
    if (active === "All") return true;
    return i.category === active;
  });

  return (
    <section className="container py-24 md:py-28">
      <SectionHeader eyebrow={eyebrow} title={title} description={description} />

      <div className="mt-10 flex flex-wrap items-center gap-2">
        {chips.map((c) => (
          <Button
            key={c}
            variant={c === active ? "default" : "ghost"}
            size="sm"
            onClick={() => setActive(c)}
            className={cn(c === active ? "" : "text-text-muted")}
          >
            {c}
          </Button>
        ))}
        {isLoading && <span className="ml-2 text-xs text-text-dim">loading…</span>}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-60px" }}
        transition={{ duration: 0.6 }}
        className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-3"
      >
        {items.slice(0, 6).map((d, i) => (
          <DatasetCard key={d.id} dataset={d} trending={i === 0} />
        ))}
      </motion.div>
    </section>
  );
}
