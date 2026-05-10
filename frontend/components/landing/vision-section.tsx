"use client";

import { motion } from "framer-motion";

import { SectionHeader } from "@/components/datamind/section-header";
import { LANDING } from "@/content/landing";

export function VisionSection() {
  const { eyebrow, title, description, pillars } = LANDING.vision;
  return (
    <section className="border-y border-border-subtle bg-surface-0">
      <div className="container py-24 md:py-28">
        <SectionHeader eyebrow={eyebrow} title={title} description={description} />

        <motion.ul
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="mt-12 grid gap-3 md:grid-cols-2 lg:grid-cols-5"
        >
          {pillars.map((p, i) => (
            <li
              key={p}
              className="rounded-2xl border border-border-subtle bg-surface-1 p-5 text-sm text-text-muted"
            >
              <span className="font-mono text-xs text-text-dim">0{i + 1}</span>
              <div className="mt-2 text-text">{p}</div>
            </li>
          ))}
        </motion.ul>
      </div>
    </section>
  );
}
