"use client";

import { motion } from "framer-motion";

import { SectionHeader } from "@/components/datamind/section-header";
import { DatasetTable } from "@/components/datamind/dataset-table";
import { SubtractionFunnel } from "@/components/landing/shared/subtraction-funnel";
import { LANDING } from "@/content/landing";
import type { DatasetMarketplaceItem } from "@/types";

const SAMPLE_ROWS: DatasetMarketplaceItem[] = [
  {
    id: "preview-1",
    title: "Crypto Twitter Sentiment",
    category: "Web3",
    tags: ["sentiment", "twitter", "crypto"],
    quality_score: 0.91,
    quality_grade: "A",
    ai_readiness: 0.94,
    rows: 10847,
    embeddings_count: 9644,
    downloads: 2140,
    visibility: "public",
    status: "ready",
    progress: 100,
    storage_root: "0x9a3c…b1e0",
    onchain_id: 1,
    owner_wallet: "0xdemo000000000000000000000000000000000001",
    created_at: new Date().toISOString(),
    description: null,
    price_amount: 12,
    price_token: "OG",
    license_kind: "commercial",
  },
  {
    id: "preview-2",
    title: "DeFi Protocol Documentation",
    category: "NLP",
    tags: ["defi", "rag", "docs"],
    quality_score: 0.87,
    quality_grade: "A",
    ai_readiness: 0.9,
    rows: 26544,
    embeddings_count: 18450,
    downloads: 1504,
    visibility: "public",
    status: "ready",
    progress: 100,
    storage_root: "0x412e…77a1",
    onchain_id: 2,
    owner_wallet: "0xdemo000000000000000000000000000000000001",
    created_at: new Date().toISOString(),
    description: null,
    price_amount: 24,
    price_token: "OG",
    license_kind: "commercial",
  },
  {
    id: "preview-3",
    title: "Onchain Anomaly Events",
    category: "Web3",
    tags: ["mev", "anomalies", "exploits"],
    quality_score: 0.78,
    quality_grade: "B",
    ai_readiness: 0.83,
    rows: 8120,
    embeddings_count: 6010,
    downloads: 906,
    visibility: "public",
    status: "ready",
    progress: 100,
    storage_root: "0x1ab9…d3f4",
    onchain_id: 3,
    owner_wallet: "0xdemo000000000000000000000000000000000001",
    created_at: new Date().toISOString(),
    description: null,
    price_amount: 18,
    price_token: "OG",
    license_kind: "academic",
  },
  {
    id: "preview-4",
    title: "Solana DEX Trades — 30d",
    category: "Finance",
    tags: ["solana", "dex", "trades"],
    quality_score: 0.81,
    quality_grade: "B",
    ai_readiness: 0.85,
    rows: 1240006,
    embeddings_count: 89412,
    downloads: 612,
    visibility: "public",
    status: "ready",
    progress: 100,
    storage_root: "0x5e83…aa90",
    onchain_id: 4,
    owner_wallet: "0xdemo000000000000000000000000000000000001",
    created_at: new Date().toISOString(),
    description: null,
    price_amount: 30,
    price_token: "OG",
    license_kind: "commercial",
  },
  {
    id: "preview-5",
    title: "Ethereum NFT Metadata",
    category: "Vision",
    tags: ["nft", "ethereum", "metadata"],
    quality_score: 0.71,
    quality_grade: "B",
    ai_readiness: 0.74,
    rows: 4012300,
    embeddings_count: 220000,
    downloads: 488,
    visibility: "public",
    status: "ready",
    progress: 100,
    storage_root: "0xa7c2…0b1d",
    onchain_id: 5,
    owner_wallet: "0xdemo000000000000000000000000000000000001",
    created_at: new Date().toISOString(),
    description: null,
    price_amount: 9,
    price_token: "OG",
    license_kind: "personal",
  },
  {
    id: "preview-6",
    title: "Lending Liquidations",
    category: "Finance",
    tags: ["liquidations", "lending", "risk"],
    quality_score: 0.66,
    quality_grade: "C",
    ai_readiness: 0.68,
    rows: 41902,
    embeddings_count: 32500,
    downloads: 214,
    visibility: "public",
    status: "ready",
    progress: 100,
    storage_root: "0x33d9…f01a",
    onchain_id: 6,
    owner_wallet: "0xdemo000000000000000000000000000000000001",
    created_at: new Date().toISOString(),
    description: null,
    price_amount: 6,
    price_token: "OG",
    license_kind: "academic",
  },
];

export function DashboardPreview() {
  const { eyebrow, title, description, sideTitle, sideBody, funnel, subCard } = LANDING.preview;
  return (
    <section className="container py-24 md:py-28">
      <SectionHeader eyebrow={eyebrow} title={title} description={description} />

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.7 }}
        className="mt-12 grid gap-6 lg:grid-cols-[1.6fr_1fr]"
      >
        <DatasetTable rows={SAMPLE_ROWS} />
        <div className="flex flex-col gap-4">
          <div>
            <h3 className="text-xl font-medium tracking-tight">{sideTitle}</h3>
            <p className="mt-2 text-sm text-text-muted">{sideBody}</p>
          </div>
          <SubtractionFunnel
            raw={funnel.raw}
            filtered={funnel.filtered}
            verified={funnel.verified}
          />
          <div className="rounded-2xl border border-border-subtle bg-surface-1 p-5">
            <div className="text-xs uppercase tracking-wider text-text-dim">
              {subCard.title}
            </div>
            <ul className="mt-3 space-y-1.5 text-sm text-text-muted">
              {subCard.bullets.map((b) => (
                <li key={b} className="flex items-start gap-2">
                  <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-brand-magenta-500" />
                  {b}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </motion.div>
    </section>
  );
}
