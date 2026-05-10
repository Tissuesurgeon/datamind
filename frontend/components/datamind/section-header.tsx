import { cn } from "@/lib/utils";

export function SectionHeader({
  eyebrow,
  title,
  description,
  align = "left",
  className,
}: {
  eyebrow?: string;
  title: string | React.ReactNode;
  description?: string | React.ReactNode;
  align?: "left" | "center";
  className?: string;
}) {
  return (
    <div className={cn(align === "center" && "text-center mx-auto", "max-w-3xl", className)}>
      {eyebrow && (
        <div
          className={cn(
            "inline-flex items-center gap-2 rounded-full border border-border-subtle bg-white/[0.03] px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-text-muted",
            align === "center" && "justify-center"
          )}
        >
          <span className="h-1.5 w-1.5 rounded-full bg-brand-amber-500" />
          {eyebrow}
        </div>
      )}
      <h2 className="mt-4 text-balance text-3xl font-medium tracking-tight md:text-5xl">
        {title}
      </h2>
      {description && (
        <p className="mt-4 text-pretty text-base text-text-muted md:text-lg">{description}</p>
      )}
    </div>
  );
}
