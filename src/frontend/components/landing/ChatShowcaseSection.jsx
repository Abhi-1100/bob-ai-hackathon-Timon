import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bot,
  User,
  Send,
  Sparkles,
  ShieldCheck,
  ExternalLink,
  ChevronRight,
  Database,
  CheckCircle2
} from 'lucide-react';

export function ChatShowcaseSection({ navigate }) {
  const exampleQueries = [
    {
      q: 'What is the highest risk attack?',
      a: 'The highest risk campaign is **AC-001** with a calibrated score of **94/100 (Critical)**.\n\n• **Threat Actor:** Originating from `198.51.100.24`\n• **Compromised Target:** `10.0.4.12`\n• **Progression:** Initial SSH brute force escalated into root access and 4.2GB data exfiltration.\n• **Immediate Action:** Containment playbook triggered; firewall block rule staged.',
      sources: ['threat_intel.db alerts table', 'RiskScoringEngine (Score: 94)', 'MITRE T1110.001 & T1041']
    },
    {
      q: 'Which incidents involve credential theft?',
      a: 'Found **2 attack chains** matching credential theft techniques:\n\n1. **AC-001:** Features `T1110.001` (Password Spraying) against staging infrastructure.\n2. **AC-002:** Features `T1003.002` (NTDS SAM credential dumping) targeting internal domain controller `192.168.1.55`.\n\nBoth incidents have credential revocation tickets generated in the recommendation queue.',
      sources: ['MitreMappingService', 'Technique T1003 / T1110', 'Active Session DB']
    },
    {
      q: 'Show attacks mapped to T1110.',
      a: 'Technique **T1110 (Brute Force)** is mapped across **3 distinct attack campaigns** comprising **38 total alerts**:\n\n• **AC-001:** 18 failed SSH password attempts within a 4-minute window from `198.51.100.24`.\n• **AC-004:** Distributed HTTP basic auth spray across public API endpoints.\n• **AC-007:** Kerberos pre-authentication failure burst.\n\nAggregated frequency rank: #1 most observed initial access vector.',
      sources: ['MITRE ATT&CK Matrix Index', 'Telemetry Time-Series Table']
    },
    {
      q: "Summarize today's incidents.",
      a: "Daily Incident Synthesis:\n\n• **Total Ingested Alerts:** 10,482 logs\n• **Correlated Chains:** 12 active campaigns (99.2% noise reduction)\n• **Critical Priority:** 3 incidents require immediate analyst sign-off (AC-001, AC-002, AC-005)\n• **Dominant Adversary Tactic:** Credential Dumping and Lateral SSH Infiltration\n• **Executive BLUF Briefing:** Available for one-click PDF export.",
      sources: ['Dashboard Overview Stats', 'Incident Correlation Engine', 'BLUF Report Generator']
    }
  ];

  const [selectedIdx, setSelectedIdx] = useState(0);
  const activeChat = exampleQueries[selectedIdx];

  return (
    <section id="chat-copilot" className="landing-chat-section">
      <div className="landing-container">
        <div className="section-header-center">
          <span className="section-eyebrow">GROUNDED INTELLIGENCE COPILOT</span>
          <h2 className="section-title">Talk To Your Security Data</h2>
          <p className="section-description">
            Ask complex threat hunting questions in natural language. Powered by high-speed vector retrieval with zero hallucination.
          </p>
        </div>

        {/* Clickable Quick Prompts */}
        <div className="chat-prompts-bar">
          <span className="prompts-label">SELECT A SOC INVESTIGATION PROMPT:</span>
          <div className="prompts-pills">
            {exampleQueries.map((item, idx) => (
              <button
                key={idx}
                onClick={() => setSelectedIdx(idx)}
                className={`prompt-chip-btn ${selectedIdx === idx ? 'active' : ''}`}
              >
                <Sparkles size={13} color={selectedIdx === idx ? '#fff' : 'var(--blue)'} />
                <span>"{item.q}"</span>
              </button>
            ))}
          </div>
        </div>

        {/* Realistic Chat Window Mockup */}
        <div className="chat-mockup-frame">
          <div className="chat-mockup-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div className="copilot-avatar">
                <Bot size={18} />
              </div>
              <div>
                <strong style={{ fontSize: 13.5, color: 'var(--text-primary)' }}>D2 Threat Intelligence Copilot</strong>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Grounded via Qdrant Vector Engine & LLaMA 3.3 70B</div>
              </div>
            </div>
            <span className="badge-severity low">
              <ShieldCheck size={13} />
              <span>100% Zero-Hallucination RAG</span>
            </span>
          </div>

          <div className="chat-mockup-body">
            <AnimatePresence mode="wait">
              <motion.div
                key={selectedIdx}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.2 }}
                className="chat-mockup-dialogue"
              >
                {/* User message */}
                <div className="chat-entry user">
                  <div className="avatar user">
                    <User size={15} />
                  </div>
                  <div className="bubble user">
                    {activeChat.q}
                  </div>
                </div>

                {/* AI response */}
                <div className="chat-entry ai">
                  <div className="avatar ai">
                    <Bot size={16} />
                  </div>
                  <div className="bubble ai">
                    <div className="ai-bubble-text" style={{ whiteSpace: 'pre-line' }}>
                      {activeChat.a}
                    </div>

                    {/* Factual Citations & Sources */}
                    <div className="bubble-citations">
                      <span className="citations-title">
                        <Database size={11} /> GROUNDED SOURCES:
                      </span>
                      <div className="citation-pills">
                        {activeChat.sources.map((s, i) => (
                          <span key={i} className="citation-pill">
                            <CheckCircle2 size={11} color="var(--low)" />
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>

          {/* Interactive Chat Input Bar */}
          <div className="chat-mockup-input">
            <input
              type="text"
              readOnly
              value={activeChat.q}
              className="copilot-input-field"
            />
            <button onClick={() => navigate('/chat')} className="btn btn-primary" style={{ padding: '8px 18px', fontSize: 13 }}>
              <span>Try in Live Chat</span>
              <Send size={14} />
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
