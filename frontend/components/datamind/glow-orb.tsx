import { cn } from "@/lib/utils";

/** Slow-rotating amber→magenta conic gradient orb used as a backdrop. */
export function GlowOrb({
  className,
  size = 800,
}: {
  className?: string;
  size?: number;
}) {
  return (
    <div
      aria-hidden
      className={cn(
        "pointer-events-none absolute -z-10 select-none rounded-full blur-3xl opacity-50",
        "[background:conic-gradient(from_90deg_at_50%_50%,rgba(245,165,36,0.55),rgba(229,36,122,0.45),rgba(245,165,36,0.55))]",
        className
      )}
      style={{ width: size, height: size }}
    />
  );
}
