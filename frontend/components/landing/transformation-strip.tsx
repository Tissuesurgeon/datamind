"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

import { LANDING } from "@/content/landing";

export function TransformationStrip() {
  const { from, to, pillars } = LANDING.transformation;
  return (
    <section className="border-y border-border-subtle bg-surface-0/60">
      <div className="container py-10">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5 }}
          className="flex flex-col items-center gap-6 md:flex-row md:justify-between"
        >
          <div className="flex items-center gap-4 font-mono text-lg md:text-xl">
            <span className="text-text-muted">{from}</span>
            <ArrowRight className="h-5 w-5 text-brand-amber-300" />
            <span className="gradient-text font-medium">{to}</span>
          </div>
          <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-text-muted">
            {pillars.map((p, i) => (
              <span key={p} className="inline-flex items-center gap-3">
                {p}
                {i < pillars.length - 1 && <span className="text-text-dim">·</span>}
              </span>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
