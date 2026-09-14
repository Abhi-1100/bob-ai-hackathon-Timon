import React from 'react';
import { motion } from 'framer-motion';
import {
  AlertOctagon,
  Clock4,
  FilterX,
  Hourglass,
  ArrowRight,
  CheckCircle2,
  TrendingDown,
  Layers,
  Flame,
  ShieldCheck
} from 'lucide-react';

export function ProblemSection() {
  const painPoints = [
    {
      icon: AlertOctagon,
      stat: '10,000+',
      title: 'Alert Volume Deluge',
      text: 'Thousands of repetitive, low-fidelity logs flood SIEM consoles every day, burying high-severity intrusions in deafening background noise.'
    },
    {
      icon: Clock4,
      stat: '42 Min',
      title: 'Manual Triage Drain',
      text: 'Tier-1 analysts spend 35–45 minutes per alert manually pivoting between IP lookups, firewall rules, and disparate log files.'
    },
    {
      icon: FilterX,
      stat: '74%',
      title: 'Lost Critical Threats',
      text: 'Multi-stage adversaries intentionally evade detection by spreading subtle signals across days and subnets, evading single-alert rules.'
    },
    {
      icon: Hourglass,
      stat: '277 Days',
      title: 'Slow Incident Response',
      text: 'Without correlated attack chains, incident response is reactive, dramatically elevating breach blast radiuses and business liability.'
    }
  ];

  return (
    <section className="landing-problem-section">
      <div className="landing-container">
        <div className="section-header-center">
          <span className="section-eyebrow" style={{ color: 'var(--critical)' }}>THE SOC CHALLENGE</span>
          <h2 className="section-title">Security Teams Are Drowning In Alerts</h2>
          <p className="section-description">
            Traditional SIEM and EDR rules dump raw notifications onto overworked analysts. THREATINTEL flips the paradigm by turning isolated logs into actionable campaigns.
          </p>
        </div>

        {/* 4 Pain Point Stats Cards */}
        <div className="problem-stats-grid">
          {painPoints.map((item, idx) => {
            const Icon = item.icon;
            return (
              <motion.div
                key={idx}
                className="problem-card"
                whileHover={{ y: -4, transition: { duration: 0.2 } }}
              >
                <div className="problem-card-top">
                  <div className="problem-icon-wrap">
                    <Icon size={20} />
                  </div>
                  <span className="problem-stat">{item.stat}</span>
                </div>
                <h4 className="problem-title">{item.title}</h4>
                <p className="problem-text">{item.text}</p>
              </motion.div>
            );
          })}
        </div>

        {/* Before vs After Interactive Comparison Showcase */}
        <div className="comparison-showcase">
          <div className="comparison-header">
            <h3>Automated Correlation & Compression in Action</h3>
            <span className="compression-badge">
              <TrendingDown size={14} />
              <span>99.2% Volume Reduction Factor</span>
            </span>
          </div>

          <div className="comparison-grid">
            {/* Before Card */}
            <div className="comparison-side before-side">
              <div className="side-label before-tag">
                <span className="dot" /> BEFORE: TRADITIONAL SIEM NOISE
              </div>
              <div className="side-metric">
                <strong>10,000</strong>
                <span>Disjointed Raw Alerts</span>
              </div>
              <p className="side-desc">
                Analyst fatigue, context switching, duplicate tickets, and invisible lateral movement lost across siloed event streams.
              </p>

              {/* Raw noisy feed representation */}
              <div className="noisy-log-feed">
                <div className="log-row"><code>10:42:01</code> <span>[WARN] Failed SSH password for root from 198.51.100.24</span></div>
                <div className="log-row"><code>10:42:04</code> <span>[WARN] Failed SSH password for admin from 198.51.100.24</span></div>
                <div className="log-row"><code>10:42:09</code> <span>[INFO] Port 22 connection reset by peer</span></div>
                <div className="log-row"><code>10:44:12</code> <span>[WARN] Sudo token elevated for user webapp</span></div>
                <div className="log-row"><code>10:46:18</code> <span>[CRIT] Outbound egress 4.2GB to unknown C2 server</span></div>
                <div className="log-overlay">... +9,995 unstructured alerts pending manual review</div>
              </div>
            </div>

            {/* Middle Transformation Arrow */}
            <div className="comparison-arrow-zone">
              <div className="arrow-circle">
                <ArrowRight size={20} />
              </div>
              <span className="arrow-sub">THREATINTEL Engine</span>
            </div>

            {/* After Card */}
            <div className="comparison-side after-side">
              <div className="side-label after-tag">
                <CheckCircle2 size={13} /> AFTER: THREATINTEL PRIORITISED ATTACK CHAINS
              </div>
              <div className="side-metric">
                <strong style={{ color: 'var(--blue)' }}>12</strong>
                <span>Correlated Attack Campaigns</span>
              </div>
              <p className="side-desc">
                Multi-stage incidents reconstructed chronologically with MITRE techniques, multi-factor risk scores, and one-click playbooks.
              </p>

              {/* Actionable Attack Chain Preview */}
              <div className="prioritised-chain-box">
                <div className="chain-box-top">
                  <div>
                    <span className="mono" style={{ fontWeight: 800, color: 'var(--blue)', fontSize: 13 }}>CAMPAIGN #AC-001</span>
                    <h5 style={{ margin: '2px 0 0', fontSize: 13.5, color: 'var(--text-primary)' }}>External Infiltration & Lateral Exfiltration</h5>
                  </div>
                  <span className="badge-critical-sm">Score 94 / 100</span>
                </div>
                <div className="chain-box-meta">
                  <span><strong>Source:</strong> 198.51.100.24</span>
                  <span><strong>Targets:</strong> 3 internal DB hosts</span>
                  <span><strong>Events:</strong> 28 correlated</span>
                </div>
                <div className="chain-box-tactics">
                  <span className="tactic-pill">Initial Access</span>
                  <span className="tactic-pill">Privilege Escalation</span>
                  <span className="tactic-pill">Exfiltration</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
