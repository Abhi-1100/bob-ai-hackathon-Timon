import React from 'react';
import { motion } from 'framer-motion';
import {
  TrendingDown,
  Zap,
  ShieldCheck,
  Eye,
  Layers,
  Sparkles,
  CheckCircle2
} from 'lucide-react';

export function BenefitsSection() {
  const benefits = [
    {
      title: 'Reduce Alert Fatigue by 99%',
      icon: TrendingDown,
      metric: '99.2%',
      metricLabel: 'Noise Reduction',
      desc: 'Compress thousands of repetitive SIEM and firewall notifications into a handful of high-fidelity, chronological attack campaigns.'
    },
    {
      title: 'Accelerate Threat Investigations',
      icon: Zap,
      metric: '10x Faster',
      metricLabel: 'Mean Time to Detect (MTTD)',
      desc: 'Eliminate hours spent manually cross-referencing IP logs, reverse DNS records, and firewall tables with instant automated correlation.'
    },
    {
      title: 'Improve Incident Response',
      icon: ShieldCheck,
      metric: '&lt; 15 Mins',
      metricLabel: 'Mean Time to Respond (MTTR)',
      desc: 'Deploy pre-calibrated containment playbooks immediately, blocking adversary command-and-control servers before data exfiltration occurs.'
    },
    {
      title: 'Executive C-Suite Visibility',
      icon: Eye,
      metric: '1-Click',
      metricLabel: 'Printable BLUF Briefings',
      desc: 'Bridge the communication gap between technical analysts and executive decision-makers with automated Bottom Line Up Front threat summaries.'
    },
    {
      title: 'Universal MITRE Alignment',
      icon: Layers,
      metric: '100%',
      metricLabel: 'Standardized ATT&CK Coverage',
      desc: 'Standardize threat terminology across enterprise security teams and auditors with automated matrix mapping across all 14 tactics.'
    },
    {
      title: 'Grounded AI Analysis',
      icon: Sparkles,
      metric: '0%',
      metricLabel: 'Hallucination Risk',
      desc: 'Empower junior analysts to conduct advanced forensics using natural language chat copilot grounded directly in real telemetry vectors.'
    }
  ];

  return (
    <section id="benefits" className="landing-benefits-section">
      <div className="landing-container">
        <div className="section-header-center">
          <span className="section-eyebrow">MEASURABLE IMPACT</span>
          <h2 className="section-title">Why Teams Choose D2</h2>
          <p className="section-description">
            Engineered from the ground up to supercharge SOC efficiency, accelerate threat containment, and protect enterprise infrastructure.
          </p>
        </div>

        <div className="benefits-grid">
          {benefits.map((b, idx) => {
            const Icon = b.icon;
            return (
              <motion.div
                key={idx}
                className="benefit-card"
                whileHover={{ y: -4, transition: { duration: 0.2 } }}
              >
                <div className="benefit-card-top">
                  <div className="benefit-icon-box">
                    <Icon size={20} />
                  </div>
                  <div className="benefit-metric-tag">
                    <strong>{b.metric}</strong>
                    <span>{b.metricLabel}</span>
                  </div>
                </div>

                <h3 className="benefit-title">{b.title}</h3>
                <p className="benefit-desc">{b.desc}</p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
