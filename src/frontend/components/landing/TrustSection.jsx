import React from 'react';
import { motion } from 'framer-motion';
import {
  Network,
  ShieldAlert,
  Flame,
  Globe2,
  Bot,
  FileCheck2,
  Database,
  Cpu,
  Layers,
  Terminal
} from 'lucide-react';

export function TrustSection() {
  const badges = [
    { title: 'Threat Correlation', icon: Network, desc: 'Time & IP affinity clustering' },
    { title: 'MITRE ATT&CK® Mapping', icon: ShieldAlert, desc: 'Enterprise tactics & techniques' },
    { title: 'Risk Prioritisation', icon: Flame, desc: 'Dynamic 0–100 scoring model' },
    { title: 'Threat Intelligence', icon: Globe2, desc: 'Real-time telemetry ingestion' },
    { title: 'AI-Powered Analysis', icon: Bot, desc: 'Grounded RAG vector reasoning' },
    { title: 'Executive Reporting', icon: FileCheck2, desc: 'Automated BLUF briefings' }
  ];

  const standards = [
    'MITRE ATT&CK® Matrix v14.1',
    'NIST SP 800-61 Rev 2',
    'CISA Known Exploited (KEV)',
    'TLP 2.0 Protocol Dissemination',
    'Qdrant Vector Cosine RAG',
    'FastAPI Asynchronous Pipelines'
  ];

  return (
    <section className="landing-trust-section">
      <div className="landing-container">
        <div className="section-header-center">
          <span className="section-eyebrow">ENTERPRISE SOC ARCHITECTURE</span>
          <h2 className="section-title">Built for Modern Security Operations</h2>
          <p className="section-description">
            Trusted by security architects, incident responders, and CISOs to deliver automated triage with zero hallucination.
          </p>
        </div>

        {/* 6 Core Enterprise Badges */}
        <div className="trust-badges-grid">
          {badges.map((b, idx) => {
            const Icon = b.icon;
            return (
              <motion.div
                key={idx}
                className="trust-badge-card"
                whileHover={{ y: -4, transition: { duration: 0.2 } }}
              >
                <div className="badge-icon-box">
                  <Icon size={20} />
                </div>
                <div>
                  <h4 className="badge-title">{b.title}</h4>
                  <p className="badge-desc">{b.desc}</p>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Industry Compliance & Protocol Standards Banner */}
        <div className="standards-banner">
          <span className="standards-label">COMPLIANT WITH INDUSTRY FRAMEWORKS:</span>
          <div className="standards-pills">
            {standards.map((st, i) => (
              <span key={i} className="standard-pill">
                <span className="check-dot" />
                {st}
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
