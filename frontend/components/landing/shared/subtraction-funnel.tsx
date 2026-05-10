import { compactNumber } from "@/lib/utils";

export function SubtractionFunnel({
  raw,
  filtered,
  verified,
}: {
  raw: { value: number; label: string };
  filtered: { value: number; label: string };
  verified: { value: number; label: string };
}) {
  return (
    <div className="rounded-2xl border border-border-subtle bg-surface-1 p-5 font-mono">
      <div>
        <div className="text-3xl font-medium text-text">
          {compactNumber(raw.value)}
        </div>
        <div className="text-xs text-text-dim">{raw.label}</div>
      </div>
      <div className="mt-4 flex items-center gap-2 text-sm">
        <span className="rounded-md bg-brand-magenta-500/15 px-2 py-0.5 text-brand-magenta-300">
          −{compactNumber(filtered.value)}
        </span>
        <span className="text-text-dim">{filtered.label}</span>
      </div>
      <div className="my-4 h-px bg-gradient-to-r from-brand-amber-500/40 via-brand-magenta-500/40 to-transparent" />
      <div>
        <div className="text-3xl font-medium gradient-text">
          {compactNumber(verified.value)}
        </div>
        <div className="text-xs text-text-dim">{verified.label}</div>
      </div>
    </div>
  );
}
