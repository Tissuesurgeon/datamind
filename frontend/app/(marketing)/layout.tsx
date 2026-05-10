import { LandingNav } from "@/components/landing/landing-nav";

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-dvh">
      <LandingNav />
      {children}
    </div>
  );
}
