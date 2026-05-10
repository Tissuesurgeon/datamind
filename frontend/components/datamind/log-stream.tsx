"use client";

import { useEffect, useRef } from "react";

import type { RealtimeEvent } from "@/types";
import { cn } from "@/lib/utils";

export function LogStream({
  events,
  className,
}: {
  events: RealtimeEvent[];
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!ref.current) return;
    ref.current.scrollTop = ref.current.scrollHeight;
  }, [events.length]);

  return (
    <div
      ref={ref}
      className={cn(
        "max-h-[300px] overflow-y-auto rounded-2xl border border-border-subtle bg-surface-1 p-4 font-mono text-xs leading-relaxed",
        className
      )}
    >
      {events.length === 0 && (
        <div className="text-text-dim">Waiting for events…</div>
      )}
      {events.map((e, i) => (
        <div key={i} className="flex gap-3 text-text-muted">
          <span className="text-text-dim">{new Date(e.ts * 1000).toLocaleTimeString()}</span>
          <span className="text-brand-amber-300">{e.type}</span>
          <span className="truncate">{JSON.stringify(e.payload)}</span>
        </div>
      ))}
    </div>
  );
}
