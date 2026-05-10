import * as React from "react";
import { cn } from "@/lib/utils";

export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(
      "flex min-h-[88px] w-full rounded-lg border border-border-subtle bg-surface-1 px-3 py-2 text-sm text-text placeholder:text-text-dim",
      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-amber-500/40 focus-visible:border-brand-amber-500/40",
      "disabled:cursor-not-allowed disabled:opacity-50",
      className
    )}
    {...props}
  />
));
Textarea.displayName = "Textarea";
