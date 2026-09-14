import React from 'react';
import { motion } from 'framer-motion';
import {
  ShieldAlert,
  ArrowRight,
  Flame,
  Activity,
  Layers,
  Sparkles,
  CheckCircle2,
  Lock,
  Play,
  TrendingUp,
  Cpu,
  Bot
} from 'lucide-react';
import { useAuthStore } from '../../store/authStore';

export function HeroSection({ navigate, onRequestDemo }) {
  const { isAuthenticated } = useAuthStore();
  return (
    <section className="landing-hero-section">
      {/* Background Ambient Glows */}
      <div className="hero-glow hero-glow-1" />
      <div className="hero-glow hero-glow-2" />

      <div className="landing-container hero-grid">
        {/* Left Column: Headlines & Call to Actions */}
        <motion.div
          className="hero-content"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        >
          {/* Release Badge */}
          <div className="hero-badge">
            <span className="badge-pulse" />
            <Sparkles size={13} color="var(--blue)" />
            <span>Next-Gen Enterprise SOC Assistant · v2.4 Release</span>
          </div>

          <h1 className="hero-title">
            AI-Powered Threat Intelligence & <br />
            <span className="text-gradient">Alert Prioritisation Platform</span>
          </h1>

          <p className="hero-subtitle">
            Transform thousands of noisy security alerts into correlated attack chains,
            automated MITRE ATT&CK mappings, multi-factor risk assessments, actionable remediation playbooks,
            and executive-ready BLUF intelligence reports.
          </p>

          {/* Call to Actions */}
          <div className="hero-ctas">
            <button onClick={onRequestDemo} className="btn btn-primary hero-btn-primary">
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
              className="btn btn-secondary hero-btn-secondary"
            >
              <Play size={15} />
              <span>{isAuthenticated ? 'Open Threat Console' : 'Get Started with Live Platform'}</span>
            </button>
          </div>

          {/* Social Proof Stats */}
          <div className="hero-metrics-row">
            <div>
              <strong className="metric-num">99.2%</strong>
              <span className="metric-label">Alert Noise Reduction</span>
            </div>
            <div className="metric-divider" />
            <div>
              <strong className="metric-num">&lt; 3.2s</strong>
              <span className="metric-label">Correlation Latency</span>
            </div>
            <div className="metric-divider" />
            <div>
              <strong className="metric-num">100%</strong>
              <span className="metric-label">Dynamic Ingestion</span>
            </div>
          </div>
        </motion.div>

        {/* Right Column: High-Fidelity Interactive SOC Dashboard Mockup */}
        <motion.div
          className="hero-preview-wrapper"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.2, ease: 'easeOut' }}
        >
          {/* Main Dashboard Window Mockup */}
          <div className="dashboard-mockup-frame">
            {/* Window Top Controls */}
            <div className="mockup-window-header">
              <div className="window-dots">
                <span className="dot red" />
                <span className="dot yellow" />
                <span className="dot green" />
              </div>
              <div className="window-url-bar">
                <Lock size={11} />
                <span>d2-threatintel.enterprise.internal/command-center</span>
              </div>
              <div className="window-status-pill">
                <span className="live-dot" />
                <span>LIVE TELEMETRY</span>
              </div>
            </div>

            {/* Dashboard Content Canvas */}
            <div className="mockup-dashboard-content">
              {/* Mini KPI Bar */}
              <div className="mockup-kpi-grid">
                <div className="mockup-kpi">
                  <span className="mkpi-label">TOTAL ALERTS</span>
                  <div className="mkpi-val">10,482</div>
                  <span className="mkpi-sub positive">+1,240 / hr</span>
                </div>
                <div className="mockup-kpi">
                  <span className="mkpi-label">CORRELATED CHAINS</span>
                  <div className="mkpi-val" style={{ color: 'var(--blue)' }}>12 Active</div>
                  <span className="mkpi-sub">99.2% compressed</span>
                </div>
                <div className="mockup-kpi">
                  <span className="mkpi-label">CRITICAL THREATS</span>
                  <div className="mkpi-val" style={{ color: 'var(--critical)' }}>3 Urgent</div>
                  <span className="mkpi-sub" style={{ color: 'var(--critical)' }}>Score ≥ 85</span>
                </div>
              </div>

              {/* Correlated Chain Card Preview */}
              <div className="mockup-card-body">
                <div className="mockup-incident-head">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span className="incident-id-tag">AC-904</span>
                    <strong style={{ fontSize: 13, color: 'var(--text-primary)' }}>
                      Multi-Stage SSH Infiltration & Lateral Dump
                    </strong>
                  </div>
                  <span className="mockup-badge-critical">CRITICAL · RISK 94</span>
                </div>

                {/* Event timeline line */}
                <div className="mockup-timeline-nodes">
                  <div className="timeline-node active">
                    <span className="node-dot" />
                    <span>SSH Brute Force</span>
                  </div>
                  <div className="node-line" />
                  <div className="timeline-node active">
                    <span className="node-dot" />
                    <span>Privilege Escalation</span>
                  </div>
                  <div className="node-line" />
                  <div className="timeline-node active">
                    <span className="node-dot" />
                    <span>Data Exfiltration</span>
                  </div>
                </div>

                {/* MITRE Tags Row */}
                <div className="mockup-mitre-row">
                  <span className="mockup-chip">T1110.001 Brute Force</span>
                  <span className="mockup-chip">T1059 Command Script</span>
                  <span className="mockup-chip">T1003 Credential Dump</span>
                  <span className="mockup-chip">T1041 Exfil Over C2</span>
                </div>
              </div>

              {/* Chat Copilot Preview Row */}
              <div className="mockup-chat-preview">
                <div className="mockup-chat-avatar">
                  <Bot size={15} />
                </div>
                <div className="mockup-chat-bubble">
                  <strong>AI Analyst Copilot:</strong> Chain AC-904 verified high-confidence intrusion. Recommended: isolate target <code>10.0.4.12</code> and block IP <code>198.51.100.24</code> immediately.
                </div>
              </div>
            </div>
          </div>

          {/* Floating Cyber Badges with Framer Motion */}
          <motion.div
            className="floating-card floating-card-1"
            animate={{ y: [0, -8, 0] }}
            transition={{ duration: 4.5, repeat: Infinity, ease: 'easeInOut' }}
          >
            <div className="floating-icon-wrap" style={{ background: 'var(--critical-bg)', color: 'var(--critical)' }}>
              <Flame size={16} />
            </div>
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-primary)' }}>Risk Engine Calibrated</div>
              <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Multi-factor threat weight: 94/100</div>
            </div>
          </motion.div>

          <motion.div
            className="floating-card floating-card-2"
            animate={{ y: [0, 8, 0] }}
            transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut', delay: 1 }}
          >
            <div className="floating-icon-wrap" style={{ background: 'var(--low-bg)', color: 'var(--low)' }}>
              <CheckCircle2 size={16} />
            </div>
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-primary)' }}>Deterministic Correlation</div>
              <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>10,482 logs → 12 actionable chains</div>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
