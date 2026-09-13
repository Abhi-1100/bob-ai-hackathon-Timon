import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Network,
  ShieldAlert,
  Flame,
  FileText,
  MessageSquare,
  Lock,
  ArrowUpRight,
  Sparkles,
  Layers,
  CheckCircle2,
  Globe,
  Clock,
  ExternalLink
} from 'lucide-react';

export function PlatformScreenshotsSection({ navigate }) {
  const [activeTab, setActiveTab] = useState('chains');

  const tabs = [
    { id: 'chains', label: 'Attack Chain View', icon: Network, route: '/attack-chains' },
    { id: 'mitre', label: 'MITRE Mapping View', icon: ShieldAlert, route: '/mitre' },
    { id: 'risk', label: 'Risk Prioritisation Queue', icon: Flame, route: '/risk' },
    { id: 'reports', label: 'BLUF Intelligence Report', icon: FileText, route: '/reports' },
    { id: 'chat', label: 'AI Chat Assistant', icon: MessageSquare, route: '/chat' }
  ];

  return (
    <section id="platform" className="landing-screenshots-section">
      <div className="landing-container">
        <div className="section-header-center">
          <span className="section-eyebrow">INTERACTIVE OPERATIONAL PREVIEWS</span>
          <h2 className="section-title">Unified Security Operations Dashboard</h2>
          <p className="section-description">
            Experience the actual screens security analysts use daily to inspect campaigns, navigate the ATT&CK matrix, and execute containment.
          </p>
        </div>

        {/* Tab Selection Bar */}
        <div className="screenshot-tabs-bar">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`screenshot-tab-btn ${isActive ? 'active' : ''}`}
              >
                <Icon size={16} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Browser Mockup Canvas */}
        <div className="browser-mockup-frame">
          {/* Top Browser Chrome */}
          <div className="browser-chrome">
            <div className="chrome-dots">
              <span className="dot red" />
              <span className="dot yellow" />
              <span className="dot green" />
            </div>
            <div className="chrome-address-bar">
              <Lock size={12} color="var(--low)" />
              <span className="chrome-url">https://soc.d2-intel.internal/{activeTab === 'chains' ? 'attack-chains' : activeTab}</span>
            </div>
            <button
              onClick={() => navigate(tabs.find(t => t.id === activeTab)?.route || '/dashboard')}
              className="chrome-launch-btn"
              title="Launch this view live"
            >
              <span>Live Console</span>
              <ExternalLink size={12} />
            </button>
          </div>

          {/* Browser Screen Body */}
          <div className="browser-body">
            <AnimatePresence mode="wait">
              {activeTab === 'chains' && (
                <motion.div
                  key="chains"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.25 }}
                  className="mockup-view-content"
                >
                  <div className="mockup-view-header">
                    <div>
                      <span className="mono" style={{ fontSize: 11, color: 'var(--blue)', fontWeight: 700 }}>MODULE: ATTACK CHAINS</span>
                      <h4 style={{ fontSize: 18, fontWeight: 800, margin: '2px 0 0', color: 'var(--text-primary)' }}>
                        Correlated Adversary Campaigns (12 Active Clusters)
                      </h4>
                    </div>
                    <span className="badge-severity high">High Priority Queue</span>
                  </div>

                  <table className="soc-table" style={{ width: '100%', marginTop: 16 }}>
                    <thead>
                      <tr>
                        <th>Chain ID</th>
                        <th>Source IP</th>
                        <th>Target Subnet</th>
                        <th>Events</th>
                        <th>Risk Score</th>
                        <th>MITRE Techniques</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td><code style={{ fontWeight: 800, color: 'var(--blue)' }}>AC-001</code></td>
                        <td><code>198.51.100.24</code> (RU / Bulletproof)</td>
                        <td>10.0.4.12, 10.0.4.15 (+2)</td>
                        <td>28 alerts</td>
                        <td><strong style={{ color: 'var(--critical)' }}>94 / 100</strong></td>
                        <td>
                          <span className="mockup-chip">T1110</span>
                          <span className="mockup-chip">T1059</span>
                          <span className="mockup-chip">T1041</span>
                        </td>
                        <td><span className="badge-severity critical">Active Containment</span></td>
                      </tr>
                      <tr>
                        <td><code style={{ fontWeight: 800, color: 'var(--blue)' }}>AC-002</code></td>
                        <td><code>203.0.113.88</code> (Tor Relay)</td>
                        <td>192.168.1.55 (Domain Controller)</td>
                        <td>14 alerts</td>
                        <td><strong style={{ color: 'var(--high)' }}>78 / 100</strong></td>
                        <td>
                          <span className="mockup-chip">T1003</span>
                          <span className="mockup-chip">T1021</span>
                        </td>
                        <td><span className="badge-severity high">Triage Pending</span></td>
                      </tr>
                      <tr>
                        <td><code style={{ fontWeight: 800, color: 'var(--blue)' }}>AC-003</code></td>
                        <td><code>192.0.2.140</code> (Cloud Proxy)</td>
                        <td>10.0.8.20 (Payment Gateway)</td>
                        <td>9 alerts</td>
                        <td><strong style={{ color: 'var(--medium)' }}>62 / 100</strong></td>
                        <td>
                          <span className="mockup-chip">T1190</span>
                        </td>
                        <td><span className="badge-severity medium">Monitoring</span></td>
                      </tr>
                    </tbody>
                  </table>
                </motion.div>
              )}

              {activeTab === 'mitre' && (
                <motion.div
                  key="mitre"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.25 }}
                  className="mockup-view-content"
                >
                  <div className="mockup-view-header">
                    <div>
                      <span className="mono" style={{ fontSize: 11, color: 'var(--blue)', fontWeight: 700 }}>FRAMEWORK MATRIX</span>
                      <h4 style={{ fontSize: 18, fontWeight: 800, margin: '2px 0 0', color: 'var(--text-primary)' }}>
                        MITRE ATT&CK® Enterprise Coverage & Detections
                      </h4>
                    </div>
                    <span className="badge-severity low">v14.1 Matrix Synced</span>
                  </div>

                  <div className="mitre-matrix-preview-grid">
                    <div className="mitre-col-card">
                      <div className="mitre-col-head">Initial Access (3)</div>
                      <div className="mitre-cell active">
                        <code>T1110.001</code>
                        <span>Password Spraying</span>
                        <div className="mitre-badge-count">18 alerts</div>
                      </div>
                      <div className="mitre-cell">
                        <code>T1190</code>
                        <span>Exploit Public Facing</span>
                      </div>
                    </div>

                    <div className="mitre-col-card">
                      <div className="mitre-col-head">Execution (2)</div>
                      <div className="mitre-cell active">
                        <code>T1059.004</code>
                        <span>Unix Shell Script</span>
                        <div className="mitre-badge-count">9 alerts</div>
                      </div>
                    </div>

                    <div className="mitre-col-card">
                      <div className="mitre-col-head">Privilege Escalation (2)</div>
                      <div className="mitre-cell active">
                        <code>T1068</code>
                        <span>Exploitation for Privs</span>
                        <div className="mitre-badge-count">6 alerts</div>
                      </div>
                    </div>

                    <div className="mitre-col-card">
                      <div className="mitre-col-head">Exfiltration (1)</div>
                      <div className="mitre-cell active critical">
                        <code>T1041</code>
                        <span>Exfil Over C2 Channel</span>
                        <div className="mitre-badge-count">4 alerts</div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}

              {activeTab === 'risk' && (
                <motion.div
                  key="risk"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.25 }}
                  className="mockup-view-content"
                >
                  <div className="mockup-view-header">
                    <div>
                      <span className="mono" style={{ fontSize: 11, color: 'var(--blue)', fontWeight: 700 }}>TRIAGE QUEUE</span>
                      <h4 style={{ fontSize: 18, fontWeight: 800, margin: '2px 0 0', color: 'var(--text-primary)' }}>
                        Prioritised Attack Chain Incident Queue
                      </h4>
                    </div>
                    <span className="badge-severity critical">3 Critical Actions</span>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 16 }}>
                    <div className="risk-queue-card critical">
                      <div className="risk-score-pill">94</div>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <strong style={{ color: 'var(--text-primary)' }}>AC-001: Multi-Host Sudo Escalation & Data Egress</strong>
                          <span className="badge-severity critical">Immediate Action</span>
                        </div>
                        <p style={{ fontSize: 12.5, color: 'var(--text-secondary)', margin: '4px 0 0' }}>
                          Attacker Origin: <code>198.51.100.24</code> · Target: Database Cluster (3 Assets) · Progression: 4 Tactics Mapped
                        </p>
                      </div>
                    </div>

                    <div className="risk-queue-card high">
                      <div className="risk-score-pill" style={{ background: 'var(--high-bg)', color: 'var(--high-text)' }}>78</div>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <strong style={{ color: 'var(--text-primary)' }}>AC-002: Domain Controller NTDS Credential Dump</strong>
                          <span className="badge-severity high">High Priority</span>
                        </div>
                        <p style={{ fontSize: 12.5, color: 'var(--text-secondary)', margin: '4px 0 0' }}>
                          Attacker Origin: <code>203.0.113.88</code> · Target: Primary DC · Progression: Credential Theft
                        </p>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}

              {activeTab === 'reports' && (
                <motion.div
                  key="reports"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.25 }}
                  className="mockup-view-content"
                >
                  <div className="mockup-view-header">
                    <div>
                      <span className="mono" style={{ fontSize: 11, color: 'var(--critical)', fontWeight: 800 }}>TLP:AMBER // EXECUTIVE DISSEMINATION</span>
                      <h4 style={{ fontSize: 18, fontWeight: 900, margin: '2px 0 0', color: 'var(--text-primary)' }}>
                        Commander Threat Briefing (BLUF) — Incident AC-001
                      </h4>
                    </div>
                    <span className="badge-severity critical">Threat Level: Critical</span>
                  </div>

                  <div className="bluf-paper-preview">
                    <div className="bluf-section">
                      <span className="bluf-heading">1.0 BOTTOM LINE UP FRONT (BLUF)</span>
                      <p className="bluf-text">
                        A persistent external threat actor originating from <code>198.51.100.24</code> successfully gained perimeter access via SSH credential brute-force, elevated privileges on staging server <code>10.0.4.12</code>, and attempted 4.2GB encrypted exfiltration to remote command-and-control infrastructure.
                      </p>
                    </div>

                    <div className="bluf-section">
                      <span className="bluf-heading">2.0 RECOMMENDED COMMAND ACTIONS</span>
                      <div className="bluf-action-box">
                        ✓ Isolate host <code>10.0.4.12</code> from internal VLAN · ✓ Block adversary IP at edge firewall · ✓ Revoke active SSH keys
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}

              {activeTab === 'chat' && (
                <motion.div
                  key="chat"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.25 }}
                  className="mockup-view-content"
                >
                  <div className="mockup-view-header">
                    <div>
                      <span className="mono" style={{ fontSize: 11, color: 'var(--blue)', fontWeight: 700 }}>AI THREAT COPILOT</span>
                      <h4 style={{ fontSize: 18, fontWeight: 800, margin: '2px 0 0', color: 'var(--text-primary)' }}>
                        Conversational SOC Telemetry Query
                      </h4>
                    </div>
                    <span className="badge-severity low">Vector RAG Active</span>
                  </div>

                  <div className="chat-dialogue-preview">
                    <div className="chat-row user">
                      <div className="chat-bubble user">
                        What is the highest risk attack chain currently active, and what hosts are compromised?
                      </div>
                    </div>

                    <div className="chat-row ai">
                      <div className="chat-bubble ai">
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4, color: 'var(--blue)', fontWeight: 700, fontSize: 11 }}>
                          <Sparkles size={12} />
                          <span>AI ANALYST COPILOT</span>
                        </div>
                        The highest risk incident is <strong>Campaign AC-001 (Risk Score 94/100, Critical)</strong>.
                        <br />
                        • <strong>Adversary IP:</strong> <code>198.51.100.24</code>
                        <br />
                        • <strong>Impacted Targets:</strong> <code>10.0.4.12</code> (Staging DB), <code>10.0.4.15</code> (Application Worker).
                        <br />
                        • <strong>Observed Tactics:</strong> T1110.001 (Password Spray) followed by T1059.004 and C2 egress.
                        <div className="chat-citations-row">
                          <span className="citation-tag">Grounded Source: threat_intel.db</span>
                          <span className="citation-tag">Qdrant Cosine Similarity: 0.94</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
}
