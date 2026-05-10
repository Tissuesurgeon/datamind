"use client";

import Link from "next/link";
import { Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { LANDING } from "@/content/landing";

export function LandingNav() {
  return (
    <header className="sticky top-0 z-40 border-b border-border-subtle bg-surface-0/70 backdrop-blur-xl">
      <div className="container flex h-14 items-center justify-between gap-4">
        <Link href="/" className="flex items-center gap-2">
          <span className="grid h-7 w-7 place-items-center rounded-md bg-gradient-brand text-black">
            <Sparkles className="h-4 w-4" />
          </span>
          <span className="text-sm font-medium tracking-tight">DataMind</span>
        </Link>
        <nav className="hidden items-center gap-1 md:flex">
          {LANDING.nav.links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              target={"external" in l && l.external ? "_blank" : undefined}
              className="rounded-lg px-3 py-1.5 text-sm text-text-muted transition-colors hover:bg-white/[0.04] hover:text-text"
            >
              {l.label}
            </Link>
          ))}
        </nav>
        <Button asChild size="sm">
          <Link href={LANDING.nav.primaryCta.href}>{LANDING.nav.primaryCta.label}</Link>
        </Button>
      </div>
    </header>
  );
}
