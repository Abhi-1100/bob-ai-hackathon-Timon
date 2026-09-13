import React from 'react';
import { motion } from 'framer-motion';
import {
  Network,
  ShieldAlert,
  Flame,
  Lightbulb,
  FileText,
  MessageSquare,
  ArrowUpRight,
  Check,
  Zap,
  ShieldCheck,
  Sparkles
} from 'lucide-react';

export function CoreFeaturesSection({ navigate }) {
  const features = [
    {
      id: 'correlation',
      title: 'Alert Correlation Engine',
      icon: Network,
      tag: 'Affinity Graph',
      route: '/attack-chains',
      desc: 'Converts thousands of fragmented alert logs into coherent, multi-stage attack chains. Automatically identifies lateral movement across subnets and groups correlated campaigns by adversary origin.',
      highlights: ['Time-windowed IP clustering', 'Multi-target lateral tracking', 'False-positive elimination']
    },
    {
      id: 'mitre',
      title: 'MITRE ATT&CK® Mapping',
      icon: ShieldAlert,
      tag: 'Enterprise Matrix',
      route: '/mitre',
      desc: 'Automatically maps observed security telemetry to the global standard MITRE ATT&CK knowledge base. Instantly exposes adversary tactics from initial access through credential dumping to data exfiltration.',
      highlights: ['Technique frequency analytics', 'Tactical progression view', 'Cross-chain technique pivot']
    },
    {
      id: 'risk',
      title: 'Dynamic Risk Prioritisation',
      icon: Flame,
      tag: '0–100 Calibrated',
      route: '/risk',
      desc: 'Ranks incidents dynamically using a multi-factor mathematical scoring model. Factors in raw event severity, progression depth, target asset criticality, and MITRE severity weights.',
      highlights: ['Transparent score breakdown', 'Triage queue ordering', 'Asset impact calibration']
    },
    {
      id: 'recommendations',
      title: 'AI Response Recommendations',
      icon: Lightbulb,
      tag: 'Playbooks',
      route: '/recommendations',
      desc: 'Generates analyst-grade response guidance partitioned into Immediate Containment, Forensic Investigation, and Long-Term Hardening tasks tailored to the specific intrusion vectors.',
      highlights: ['Interactive task checklists', 'Firewall block rule presets', 'Remediation verification']
    },
    {
      id: 'reports',
      title: 'Executive BLUF Intelligence Reports',
      icon: FileText,
      tag: 'Executive Ready',
      route: '/reports',
      desc: 'Synthesizes Bottom Line Up Front (BLUF) briefings summarizing attacker origin, compromised targets, financial/regulatory risk, and recommended command actions ready for printable PDF export.',
      highlights: ['One-click PDF briefing export', 'C-suite executive summaries', 'Legal & compliance dissemination']
    },
    {
      id: 'chat',
      title: 'Grounded AI Analyst Copilot',
      icon: MessageSquare,
      tag: 'Qdrant RAG',
      route: '/chat',
      desc: 'Enables interactive conversational threat hunting in plain English. Powered by high-dimensional vector embeddings with strict factual grounding against your uploaded telemetry.',
      highlights: ['100% Zero-hallucination RAG', 'Direct chain inspection links', 'Pre-configured pivot queries']
    }
  ];

  return (
    <section id="features" className="landing-features-section">
      <div className="landing-container">
        <div className="section-header-center">
          <span className="section-eyebrow">CORE CAPABILITIES</span>
          <h2 className="section-title">Everything Security Teams Need</h2>
          <p className="section-description">
            A unified suite of intelligent automation modules engineered specifically to empower Tier-1 to Tier-3 SOC operators.
          </p>
        </div>

        {/* 6 Feature Cards Grid */}
        <div className="features-grid">
          {features.map((f, idx) => {
            const Icon = f.icon;
            return (
              <motion.div
                key={f.id}
                className="feature-card"
                whileHover={{ y: -6, transition: { duration: 0.2 } }}
              >
                <div className="feature-card-header">
                  <div className="feature-icon-wrap">
                    <Icon size={22} />
                  </div>
                  <span className="feature-tag">{f.tag}</span>
                </div>

                <h3 className="feature-title">{f.title}</h3>
                <p className="feature-desc">{f.desc}</p>

                <div className="feature-highlights">
                  {f.highlights.map((h, i) => (
                    <div key={i} className="highlight-item">
                      <Check size={13} color="var(--blue)" />
                      <span>{h}</span>
                    </div>
                  ))}
                </div>

                <div className="feature-card-footer">
                  <button onClick={() => navigate(f.route)} className="feature-link-btn">
                    <span>Explore Module in Live SOC</span>
                    <ArrowUpRight size={14} />
                  </button>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
