import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles, ArrowRight, ShieldCheck, Play, Lock, CheckCircle2 } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';

export function FinalCtaSection({ navigate, onRequestDemo }) {
  const { isAuthenticated } = useAuthStore();
  return (
    <section className="landing-final-cta-section">
      <div className="cta-cyber-grid-bg" />
      <div className="cta-glow-center" />

      <div className="landing-container">
        <motion.div
          className="final-cta-card"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <div className="final-cta-badge">
            <ShieldCheck size={14} color="var(--blue)" />
            <span>ENTERPRISE READY SOC PLATFORM</span>
          </div>

          <h2 className="final-cta-headline">
            Turn Security Alerts Into <br />
            <span className="text-gradient">Actionable Intelligence</span>
          </h2>

          <p className="final-cta-subheadline">
            Empower your SOC with AI-powered threat correlation, automated MITRE ATT&CK mapping,
            calibrated risk prioritisation, and grounded natural language investigation.
          </p>

          <div className="final-cta-buttons">
            <button onClick={onRequestDemo} className="btn btn-primary cta-btn-large">
              <Sparkles size={16} />
              <span>Request Enterprise Demo</span>
              <ArrowRight size={16} />
            </button>

            <button
              onClick={() => {
                if (isAuthenticated) {
                  navigate('/dashboard');
                } else {
                  navigate('/signup');
                }
              }}
              className="btn btn-secondary cta-btn-large"
            >
              <Play size={15} />
              <span>{isAuthenticated ? 'Open Threat Intelligence Console' : 'Get Started with Enterprise SOC'}</span>
            </button>
          </div>

          <div className="final-cta-perks">
            <div className="cta-perk">
              <CheckCircle2 size={14} color="var(--low)" />
              <span>Zero Static Data</span>
            </div>
            <div className="cta-perk">
              <CheckCircle2 size={14} color="var(--low)" />
              <span>100% Deterministic Correlation</span>
            </div>
            <div className="cta-perk">
              <CheckCircle2 size={14} color="var(--low)" />
              <span>SOC Analyst Grounded RAG</span>
            </div>
            <div className="cta-perk">
              <CheckCircle2 size={14} color="var(--low)" />
              <span>MITRE ATT&CK® v14.1 Aligned</span>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
