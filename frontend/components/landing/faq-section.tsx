"use client";

import { useState } from "react";
import { Plus, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

import { SectionHeader } from "@/components/datamind/section-header";
import { LANDING } from "@/content/landing";
import { cn } from "@/lib/utils";

export function FAQSection() {
  const { eyebrow, title, items } = LANDING.faq;
  const [open, setOpen] = useState<number | null>(0);

  return (
    <section className="container py-24 md:py-28">
      <SectionHeader eyebrow={eyebrow} title={title} />

      <div className="mt-12 mx-auto max-w-3xl divide-y divide-border-subtle border-y border-border-subtle">
        {items.map((it, i) => {
          const isOpen = open === i;
          return (
            <div key={it.q}>
              <button
                onClick={() => setOpen(isOpen ? null : i)}
                className={cn(
                  "flex w-full items-center justify-between gap-4 py-5 text-left transition-colors",
                  isOpen ? "text-text" : "text-text-muted hover:text-text"
                )}
              >
                <span className="text-base font-medium md:text-lg">{it.q}</span>
                <span
                  className={cn(
                    "grid h-7 w-7 shrink-0 place-items-center rounded-full border border-border-subtle transition-all",
                    isOpen && "bg-brand-amber-500/15 border-brand-amber-500/40 text-brand-amber-300"
                  )}
                >
                  {isOpen ? <X className="h-3.5 w-3.5" /> : <Plus className="h-3.5 w-3.5" />}
                </span>
              </button>
              <AnimatePresence initial={false}>
                {isOpen && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.25, ease: "easeOut" }}
                    className="overflow-hidden"
                  >
                    <p className="pb-6 pr-12 text-sm text-text-muted">{it.a}</p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>
    </section>
  );
}
