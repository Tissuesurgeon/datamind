"use client";

import { motion } from "framer-motion";

import { SectionHeader } from "@/components/datamind/section-header";
import { LANDING } from "@/content/landing";

export function ProblemSection() {
  const { eyebrow, title, description, items } = LANDING.problem;
  return (
    <section className="container py-24 md:py-28">
      <SectionHeader eyebrow={eyebrow} title={title} description={description} />

      <div className="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        {items.map((it, i) => (
          <motion.div
            key={it.n}
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.5, delay: i * 0.05 }}
            className="rounded-2xl border border-border-subtle bg-surface-1 p-6"
          >
            <div className="font-mono text-sm text-text-dim">{it.n}</div>
            <h3 className="mt-3 text-lg font-medium tracking-tight">{it.title}</h3>
            <p className="mt-2 text-sm text-text-muted">{it.body}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
