import { CtaSection } from "./cta-section";
import { FaqSection } from "./faq-section";
import { FeaturesSection } from "./features-section";
import { HeroSection } from "./hero-section";
import { HomeFooter } from "./home-footer";
import { HomeNavbar } from "./home-navbar";
import { HowItWorksSection } from "./how-it-works-section";
import { ProblemSection } from "./problem-section";
import { SegmentsSection } from "./segments-section";
import { TrustSection } from "./trust-section";

export function HomePageContent() {
  return (
    <div className="home-marketing min-h-screen bg-white">
      <HomeNavbar />
      <main>
        <HeroSection />
        <ProblemSection />
        <HowItWorksSection />
        <FeaturesSection />
        <SegmentsSection />
        <TrustSection />
        <FaqSection />
        <CtaSection />
      </main>
      <HomeFooter />
    </div>
  );
}
