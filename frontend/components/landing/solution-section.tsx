"use client";

import { motion } from "framer-motion";
import { ArrowRight, Check } from "lucide-react";

import { SectionHeader } from "@/components/datamind/section-header";
import { LANDING } from "@/content/landing";

export function SolutionSection() {
  const { eyebrow, title, description, pipeline, capabilities } = LANDING.solution;
  return (
    <section className="border-y border-border-subtle bg-surface-0">
      <div className="container py-24 md:py-28">
        <SectionHeader eyebrow={eyebrow} title={title} description={description} />

        <div className="mt-14 grid gap-12 lg:grid-cols-2">
          {/* Pipeline diagram */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="rounded-2xl border border-border-subtle bg-surface-1 p-6"
          >
            <div className="text-xs uppercase tracking-wider text-text-dim">
              Ingest pipeline
            </div>
            <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-3 font-mono text-sm">
              {pipeline.map((step, i) => (
                <div key={step} className="inline-flex items-center gap-3">
                  <span className="rounded-md border border-border-subtle bg-surface-2 px-2.5 py-1 text-text">
                    {step}
                  </span>
                  {i < pipeline.length - 1 && (
                    <ArrowRight className="h-3.5 w-3.5 text-brand-amber-300/70" />
                  )}
                </div>
              ))}
            </div>

            <div className="mt-8 grid grid-cols-3 gap-3 text-xs">
              <Mini label="Embed model" value="bge-small-en-v1.5" />
              <Mini label="Vector dim" value="384" />
              <Mini label="Anchor chain" value="Galileo · 16602" />
            </div>
          </motion.div>

          <motion.ul
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.05 }}
            className="grid gap-3 self-center"
          >
            {capabilities.map((c) => (
              <li
                key={c}
                className="flex items-start gap-3 rounded-xl border border-border-subtle bg-surface-1 px-4 py-3"
              >
                <span className="mt-0.5 grid h-5 w-5 place-items-center rounded-full bg-brand-amber-500/15 text-brand-amber-300">
                  <Check className="h-3 w-3" />
                </span>
                <span className="text-sm text-text">{c}</span>
              </li>
            ))}
          </motion.ul>
        </div>
      </div>
    </section>
  );
}

function Mini({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border-subtle bg-surface-2 px-3 py-2">
      <div className="font-mono text-xs text-text">{value}</div>
      <div className="text-text-dim">{label}</div>
    </div>
  );
}
