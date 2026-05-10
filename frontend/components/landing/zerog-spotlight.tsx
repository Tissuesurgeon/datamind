"use client";

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { motion } from "framer-motion";

import { SectionHeader } from "@/components/datamind/section-header";
import { CodeSnippet } from "@/components/landing/shared/code-snippet";
import { LANDING } from "@/content/landing";

export function ZeroGSpotlight() {
  const { eyebrow, title, description, columns, snippet, docsUrl } = LANDING.zerog;
  return (
    <section className="border-y border-border-subtle bg-surface-0">
      <div className="container py-24 md:py-28">
        <SectionHeader eyebrow={eyebrow} title={title} description={description} />

        <div className="mt-14 grid gap-6 lg:grid-cols-3">
          {columns.map((c, i) => (
            <motion.div
              key={c.title}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.06 }}
              className="rounded-2xl border border-border-subtle bg-surface-1 p-6"
            >
              <div className="text-xs uppercase tracking-[0.18em] text-brand-magenta-300">
                {c.title}
              </div>
              <p className="mt-4 text-sm text-text-muted">{c.body}</p>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="mt-8"
        >
          <CodeSnippet code={snippet} />
        </motion.div>

        <div className="mt-6 text-right">
          <Link
            href={docsUrl}
            target="_blank"
            className="inline-flex items-center gap-1 text-sm text-text-muted hover:text-brand-amber-300"
          >
            Read 0G docs <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>
    </section>
  );
}
