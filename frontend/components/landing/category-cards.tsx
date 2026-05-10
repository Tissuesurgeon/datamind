"use client";

import { motion } from "framer-motion";
import { Compass, Cpu, ScrollText, ShieldCheck } from "lucide-react";

import { SectionHeader } from "@/components/datamind/section-header";
import { LANDING } from "@/content/landing";

const ICONS = [Compass, Cpu, ScrollText, ShieldCheck];

export function CategoryCards() {
  const { eyebrow, title, description, items } = LANDING.capabilities;
  return (
    <section className="border-y border-border-subtle bg-surface-0">
      <div className="container py-24 md:py-28">
        <SectionHeader eyebrow={eyebrow} title={title} description={description} />

        <div className="mt-14 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {items.map((c, i) => {
            const Icon = ICONS[i] ?? Compass;
            return (
              <motion.div
                key={c.tag}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.06 }}
                className="group flex flex-col rounded-2xl border border-border-subtle bg-surface-1 p-6 transition-all hover:border-border-strong hover:bg-surface-2"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-medium uppercase tracking-[0.22em] text-brand-amber-300">
                    {c.tag}
                  </span>
                  <Icon className="h-4 w-4 text-text-dim transition-colors group-hover:text-brand-amber-300" />
                </div>
                <h3 className="mt-4 text-xl font-medium tracking-tight">{c.title}</h3>
                <p className="mt-2 text-sm text-text-muted">{c.body}</p>
                <div className="mt-6 border-t border-border-subtle pt-4 font-mono text-xs text-text-dim">
                  {c.stat}
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
