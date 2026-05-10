import { Hero } from "@/components/landing/hero";
import { TransformationStrip } from "@/components/landing/transformation-strip";
import { ProblemSection } from "@/components/landing/problem-section";
import { SolutionSection } from "@/components/landing/solution-section";
import { NumberedSteps } from "@/components/landing/numbered-steps";
import { CategoryCards } from "@/components/landing/category-cards";
import { DashboardPreview } from "@/components/landing/dashboard-preview";
import { ZeroGSpotlight } from "@/components/landing/zerog-spotlight";
import { MarketplacePreview } from "@/components/landing/marketplace-preview";
import { VisionSection } from "@/components/landing/vision-section";
import { FAQSection } from "@/components/landing/faq-section";
import { CtaFooter } from "@/components/landing/cta-footer";

export default function LandingPage() {
  return (
    <>
      <Hero />
      <TransformationStrip />
      <ProblemSection />
      <SolutionSection />
      <NumberedSteps />
      <CategoryCards />
      <DashboardPreview />
      <ZeroGSpotlight />
      <MarketplacePreview />
      <VisionSection />
      <FAQSection />
      <CtaFooter />
    </>
  );
}
