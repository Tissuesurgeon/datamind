import { cn } from "@/lib/utils";

export function MarqueeRow({
  items,
  className,
  reverse = false,
}: {
  items: readonly string[];
  className?: string;
  reverse?: boolean;
}) {
  const repeated = [...items, ...items];
  return (
    <div className={cn("relative overflow-hidden", className)}>
      <div className="pointer-events-none absolute inset-y-0 left-0 z-10 w-24 bg-gradient-to-r from-surface-0 to-transparent" />
      <div className="pointer-events-none absolute inset-y-0 right-0 z-10 w-24 bg-gradient-to-l from-surface-0 to-transparent" />
      <div
        className={cn("flex gap-4 whitespace-nowrap will-change-transform", "animate-marquee")}
        style={{ animationDirection: reverse ? "reverse" : "normal" }}
      >
        {repeated.map((it, i) => (
          <span
            key={`${it}-${i}`}
            className="inline-flex items-center gap-2 rounded-full border border-border-subtle bg-white/[0.03] px-4 py-1.5 text-sm text-text-muted"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-brand-amber-500/70" />
            {it}
          </span>
        ))}
      </div>
    </div>
  );
}
