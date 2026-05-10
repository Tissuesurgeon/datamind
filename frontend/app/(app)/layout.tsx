import { AppNav } from "@/components/datamind/app-nav";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-dvh">
      <AppNav />
      <main className="container py-8 md:py-10">{children}</main>
    </div>
  );
}
