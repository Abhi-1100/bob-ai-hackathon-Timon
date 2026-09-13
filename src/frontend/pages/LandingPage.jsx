import React, { useState } from 'react';
import { LandingNavbar } from '../components/landing/LandingNavbar';
import { HeroSection } from '../components/landing/HeroSection';
import { TrustSection } from '../components/landing/TrustSection';
import { ProblemSection } from '../components/landing/ProblemSection';
import { WorkflowSection } from '../components/landing/WorkflowSection';
import { CoreFeaturesSection } from '../components/landing/CoreFeaturesSection';
import { PlatformScreenshotsSection } from '../components/landing/PlatformScreenshotsSection';
import { ChatShowcaseSection } from '../components/landing/ChatShowcaseSection';
import { BenefitsSection } from '../components/landing/BenefitsSection';
import { ArchitectureSection } from '../components/landing/ArchitectureSection';
import { FinalCtaSection } from '../components/landing/FinalCtaSection';
import { LandingFooter } from '../components/landing/LandingFooter';
import { DemoModal } from '../components/landing/DemoModal';

export function LandingPage({ navigate, theme, toggleTheme }) {
  const [demoOpen, setDemoOpen] = useState(false);

  return (
    <div className="landing-page-root">
      {/* Navigation Header */}
      <LandingNavbar
        navigate={navigate}
        theme={theme}
        toggleTheme={toggleTheme}
        onRequestDemo={() => setDemoOpen(true)}
      />

      <main>
        {/* Section 1: Hero */}
        <HeroSection
          navigate={navigate}
          onRequestDemo={() => setDemoOpen(true)}
        />

        {/* Section 2: Trust & Frameworks */}
        <TrustSection />

        {/* Section 3: The SOC Problem (Alert Deluge & Before/After) */}
        <ProblemSection />

        {/* Section 4: End-to-End Workflow */}
        <WorkflowSection />

        {/* Section 5: Core Features */}
        <CoreFeaturesSection navigate={navigate} />

        {/* Section 6: Unified Platform Screenshots */}
        <PlatformScreenshotsSection navigate={navigate} />

        {/* Section 7: AI Analyst Chat Showcase */}
        <ChatShowcaseSection navigate={navigate} />

        {/* Section 8: Measurable Benefits */}
        <BenefitsSection />

        {/* Section 9: Architecture Diagram */}
        <ArchitectureSection />

        {/* Section 10: Final CTA */}
        <FinalCtaSection
          navigate={navigate}
          onRequestDemo={() => setDemoOpen(true)}
        />
      </main>

      {/* Section 11: Enterprise Footer */}
      <LandingFooter navigate={navigate} />

      {/* Interactive Enterprise Demo Modal */}
      <DemoModal
        isOpen={demoOpen}
        onClose={() => setDemoOpen(false)}
        navigate={navigate}
      />
    </div>
  );
}
