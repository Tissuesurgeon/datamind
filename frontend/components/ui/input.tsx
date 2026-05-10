import * as React from "react";
import { cn } from "@/lib/utils";

export const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className, type, ...props }, ref) => (
  <input
    ref={ref}
    type={type}
    className={cn(
      "flex h-10 w-full rounded-lg border border-border-subtle bg-surface-1 px-3 py-2 text-sm text-text placeholder:text-text-dim",
      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-amber-500/40 focus-visible:border-brand-amber-500/40",
      "disabled:cursor-not-allowed disabled:opacity-50",
      className
    )}
    {...props}
  />
));
Input.displayName = "Input";
