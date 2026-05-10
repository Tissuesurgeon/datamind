"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowUpRight, Github } from "lucide-react";

import { Button } from "@/components/ui/button";
import { GlowOrb } from "@/components/datamind/glow-orb";
import { MarqueeRow } from "@/components/landing/shared/marquee-row";
import { LANDING } from "@/content/landing";

export function CtaFooter() {
  const { marquee, cta, footer } = LANDING;
  return (
    <section className="relative overflow-hidden border-t border-border-subtle">
      <GlowOrb className="-top-32 left-1/2 -translate-x-1/2 opacity-30" size={1100} />
      <div className="container py-20">
        {/* Marquee social-proof row */}
        <div className="mb-16 text-center">
          <p className="text-xs uppercase tracking-[0.22em] text-text-dim">
            {marquee.label}
          </p>
        </div>
        <MarqueeRow items={marquee.items} className="mb-20" />
        <MarqueeRow items={[...marquee.items].reverse()} className="mb-24" reverse />

        {/* CTA card */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
          className="relative overflow-hidden rounded-3xl border border-border-strong bg-surface-1 p-10 md:p-14 shadow-glow-brand"
        >
          <div className="absolute inset-0 dot-grid-bg opacity-30" />
          <div className="relative flex flex-col items-center text-center">
            <h2 className="max-w-2xl text-balance text-3xl font-medium tracking-tight md:text-5xl">
              {cta.title}
            </h2>
            <p className="mt-4 max-w-xl text-text-muted">{cta.sub}</p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <Button asChild size="lg" variant="gradient">
                <Link href={cta.primary.href}>{cta.primary.label}</Link>
              </Button>
              <Button asChild size="lg" variant="ghost">
                <Link href={cta.secondary.href} target="_blank">
                  {cta.secondary.label}
                  <ArrowUpRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <Link href={cta.tertiary.href} target="_blank">
                  <Github className="h-4 w-4" />
                  {cta.tertiary.label}
                </Link>
              </Button>
            </div>
          </div>
        </motion.div>

        {/* Footer columns */}
        <footer className="mt-20 grid gap-8 border-t border-border-subtle pt-10 md:grid-cols-2 lg:grid-cols-5">
          <div className="lg:col-span-1">
            <div className="text-sm font-medium tracking-tight">DataMind</div>
            <p className="mt-2 max-w-xs text-xs text-text-muted">
              The decentralized economy for AI data. Built on 0G Galileo Testnet.
            </p>
            <Link
              href={footer.builtOn.href}
              target="_blank"
              className="mt-4 inline-flex items-center gap-1.5 rounded-full border border-border-subtle bg-white/[0.03] px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-text-muted hover:text-brand-amber-300"
            >
              {footer.builtOn.label}
              <ArrowUpRight className="h-3 w-3" />
            </Link>
          </div>
          {footer.columns.map((col) => (
            <div key={col.title}>
              <div className="text-xs uppercase tracking-[0.18em] text-text-dim">
                {col.title}
              </div>
              <ul className="mt-4 space-y-2 text-sm">
                {col.links.map((l) => (
                  <li key={l.href}>
                    <Link
                      href={l.href}
                      target={"external" in l && l.external ? "_blank" : undefined}
                      className="text-text-muted transition-colors hover:text-text"
                    >
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </footer>
        <div className="mt-10 flex items-center justify-between border-t border-border-subtle pt-6 text-xs text-text-dim">
          <span>© {new Date().getFullYear()} DataMind contributors</span>
          <span>MIT licensed</span>
        </div>
      </div>
    </section>
  );
}
