import { cn } from "@/lib/utils";

const styles: Record<string, string> = {
  A: "bg-brand-amber-500/15 text-brand-amber-300 border-brand-amber-500/40 shadow-[0_0_24px_-8px_rgba(245,165,36,0.6)]",
  B: "bg-brand-magenta-500/15 text-brand-magenta-300 border-brand-magenta-500/40 shadow-[0_0_24px_-8px_rgba(229,36,122,0.6)]",
  C: "bg-white/[0.05] text-text-muted border-border-subtle",
};

export function QualityBadge({
  grade,
  size = "default",
  className,
}: {
  grade: "A" | "B" | "C" | string | null | undefined;
  size?: "sm" | "default" | "lg";
  className?: string;
}) {
  const g = grade && (grade === "A" || grade === "B" || grade === "C") ? grade : "C";
  const dim =
    size === "sm" ? "h-6 w-6 text-[11px]" : size === "lg" ? "h-10 w-10 text-base" : "h-8 w-8 text-sm";
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center justify-center rounded-full border font-mono font-medium",
        dim,
        styles[g],
        className
      )}
    >
      {g}
    </span>
  );
}
