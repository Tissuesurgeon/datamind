"use client";

import { motion } from "framer-motion";

import { SectionHeader } from "@/components/datamind/section-header";
import { LANDING } from "@/content/landing";

export function NumberedSteps() {
  const { eyebrow, title, items } = LANDING.steps;
  return (
    <section className="container py-24 md:py-28">
      <SectionHeader eyebrow={eyebrow} title={title} />

      <div className="mt-14 grid gap-8 md:grid-cols-2 lg:grid-cols-4">
        {items.map((s, i) => (
          <motion.div
            key={s.n}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.6, delay: i * 0.08 }}
            className="relative overflow-hidden rounded-2xl border border-border-subtle bg-surface-1 p-6"
          >
            <div
              className="pointer-events-none absolute -right-3 -top-2 select-none font-mono text-[120px] font-medium leading-none text-white/[0.04]"
              aria-hidden
            >
              {s.n}
            </div>
            <div className="relative">
              <div className="font-mono text-xs uppercase tracking-[0.2em] text-brand-amber-300">
                step {s.n}
              </div>
              <h3 className="mt-3 text-xl font-medium tracking-tight">{s.title}</h3>
              <p className="mt-3 text-sm text-text-muted">{s.body}</p>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
