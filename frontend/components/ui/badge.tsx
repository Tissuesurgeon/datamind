import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "border-border-subtle bg-white/[0.04] text-text",
        amber: "border-brand-amber-500/30 bg-brand-amber-500/10 text-brand-amber-300",
        magenta: "border-brand-magenta-500/30 bg-brand-magenta-500/10 text-brand-magenta-300",
        outline: "border-border-strong bg-transparent text-text",
        muted: "border-transparent bg-white/[0.06] text-text-muted",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
