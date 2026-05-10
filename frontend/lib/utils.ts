import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(n: number, opts?: Intl.NumberFormatOptions) {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 1, ...opts }).format(n);
}

export function compactNumber(n: number) {
  if (n < 1000) return String(n);
  if (n < 1_000_000) return `${(n / 1000).toFixed(n < 10_000 ? 1 : 0)}K`;
  if (n < 1_000_000_000) return `${(n / 1_000_000).toFixed(n < 10_000_000 ? 2 : 0)}M`;
  return `${(n / 1_000_000_000).toFixed(2)}B`;
}

export function shortAddr(addr: string | null | undefined, n = 4) {
  if (!addr) return "";
  if (addr.length <= 2 * n + 2) return addr;
  return `${addr.slice(0, n + 2)}…${addr.slice(-n)}`;
}

export function shortHash(hash: string | null | undefined, n = 8) {
  if (!hash) return "";
  if (hash.length <= 2 * n + 2) return hash;
  return `${hash.slice(0, n + 2)}…${hash.slice(-n)}`;
}

export function formatDate(value: string | Date | undefined) {
  if (!value) return "";
  const d = typeof value === "string" ? new Date(value) : value;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

export function gradeColor(grade: string | null | undefined) {
  if (grade === "A") return "text-grade-a";
  if (grade === "B") return "text-grade-b";
  return "text-grade-c";
}
