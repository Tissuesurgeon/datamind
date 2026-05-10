import { cn } from "@/lib/utils";

export function CodeSnippet({ code, className }: { code: string; className?: string }) {
  return (
    <pre
      className={cn(
        "overflow-x-auto rounded-2xl border border-border-subtle bg-surface-0 p-5 font-mono text-xs leading-relaxed text-text-muted",
        className
      )}
    >
      <code>{code}</code>
    </pre>
  );
}
