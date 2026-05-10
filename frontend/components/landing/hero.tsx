"use client";

import Link from "next/link";
import { ArrowRight, ShieldCheck } from "lucide-react";
import { motion } from "framer-motion";

import { Button } from "@/components/ui/button";
import { GlowOrb } from "@/components/datamind/glow-orb";
import { QualityBadge } from "@/components/datamind/quality-badge";
import { LANDING } from "@/content/landing";
import { compactNumber } from "@/lib/utils";

const fakeRows = [
  { title: "Crypto Twitter Sentiment", grade: "A", rows: 10847, price: "12 OG" },
  { title: "DeFi Protocol Documentation Corpus", grade: "A", rows: 26544, price: "24 OG" },
  { title: "Onchain Anomaly Events", grade: "B", rows: 8120, price: "18 OG" },
];

export function Hero() {
  const { eyebrow, headlineLine1, headlineLine2, gradientWord, sub, primary, secondary, trust } =
    LANDING.hero;

  // Render `headlineLine2` substituting the gradient word with a span.
  const idx = headlineLine2.indexOf(gradientWord);
  const before = idx >= 0 ? headlineLine2.slice(0, idx) : headlineLine2;
  const after = idx >= 0 ? headlineLine2.slice(idx + gradientWord.length) : "";

  return (
    <section className="relative overflow-hidden">
      <GlowOrb className="-top-40 left-1/4" size={900} />
      <div className="absolute inset-0 dot-grid-bg opacity-40 [mask-image:radial-gradient(ellipse_at_top,black_10%,transparent_70%)]" />

      <div className="container relative grid items-center gap-12 py-24 md:py-32 lg:grid-cols-[1.1fr_1fr]">
        <div>
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="inline-flex items-center gap-2 rounded-full border border-border-subtle bg-white/[0.03] px-3 py-1 text-[11px] uppercase tracking-[0.2em] text-text-muted"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-brand-amber-500" />
            {eyebrow}
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.05 }}
            className="mt-5 text-balance text-5xl font-medium leading-[1.05] tracking-tight md:text-7xl"
          >
            {headlineLine1}
            <br />
            {before}
            <span className="gradient-text">{gradientWord}</span>
            {after}
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="mt-6 max-w-xl text-pretty text-base text-text-muted md:text-lg"
          >
            {sub}
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.25 }}
            className="mt-8 flex flex-wrap items-center gap-3"
          >
            <Button asChild size="lg" variant="gradient">
              <Link href={primary.href}>
                {primary.label} <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="ghost">
              <Link href={secondary.href}>{secondary.label}</Link>
            </Button>
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="mt-8 inline-flex items-center gap-2 text-xs text-text-dim"
          >
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>{trust}</span>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="relative"
        >
          <div className="relative mx-auto max-w-md rotate-[-2deg]">
            <div className="rounded-2xl border border-border-strong bg-surface-1 p-5 shadow-glow-brand">
              <div className="mb-3 flex items-center justify-between">
                <span className="text-xs uppercase tracking-wider text-text-dim">
                  /dashboard · datasets
                </span>
                <span className="rounded-full border border-brand-amber-500/30 bg-brand-amber-500/10 px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-brand-amber-300">
                  live
                </span>
              </div>
              <ul className="space-y-2">
                {fakeRows.map((r) => (
                  <li
                    key={r.title}
                    className="flex items-center gap-3 rounded-xl border border-border-subtle bg-surface-2 px-3 py-2.5"
                  >
                    <QualityBadge grade={r.grade} size="sm" />
                    <div className="flex-1 truncate">
                      <div className="truncate text-sm font-medium">{r.title}</div>
                      <div className="font-mono text-[11px] text-text-dim">
                        {compactNumber(r.rows)} rows
                      </div>
                    </div>
                    <div className="font-mono text-xs text-text-muted">{r.price}</div>
                  </li>
                ))}
              </ul>
              <div className="mt-4 grid grid-cols-3 gap-2 text-[11px]">
                <Stat label="Datasets" value="32" />
                <Stat label="Embeddings" value="1.4M" />
                <Stat label="On-chain" value="100%" />
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border-subtle bg-surface-2 px-3 py-2">
      <div className="font-mono text-base text-text">{value}</div>
      <div className="text-text-dim">{label}</div>
    </div>
  );
}
