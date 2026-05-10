"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Search,
  Sparkles,
  Store,
  UploadCloud,
  Workflow,
} from "lucide-react";

import { WalletButton } from "@/components/datamind/wallet-button";
import { cn } from "@/lib/utils";

const tabs = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/marketplace", label: "Marketplace", icon: Store },
  { href: "/search", label: "Search", icon: Search },
  { href: "/upload", label: "Upload", icon: UploadCloud },
  { href: "/training", label: "Training", icon: Workflow },
];

export function AppNav() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-40 border-b border-border-subtle bg-surface-0/70 backdrop-blur-xl">
      <div className="container flex h-14 items-center justify-between gap-4">
        <Link href="/" className="flex items-center gap-2">
          <span className="grid h-7 w-7 place-items-center rounded-md bg-gradient-brand text-black">
            <Sparkles className="h-4 w-4" />
          </span>
          <span className="text-sm font-medium tracking-tight">DataMind</span>
        </Link>

        <nav className="hidden gap-1 md:flex">
          {tabs.map((t) => {
            const active = pathname?.startsWith(t.href);
            return (
              <Link
                key={t.href}
                href={t.href}
                className={cn(
                  "inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm transition-colors",
                  active
                    ? "bg-white/[0.06] text-text"
                    : "text-text-muted hover:text-text hover:bg-white/[0.04]"
                )}
              >
                <t.icon className="h-3.5 w-3.5" />
                {t.label}
              </Link>
            );
          })}
        </nav>

        <WalletButton size="sm" />
      </div>
    </header>
  );
}
