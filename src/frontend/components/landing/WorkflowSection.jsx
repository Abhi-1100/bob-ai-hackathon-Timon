import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  UploadCloud,
  Network,
  ShieldAlert,
  Flame,
  Lightbulb,
  FileText,
  MessageSquare,
  ArrowRight,
  CheckCircle2,
  Cpu,
  ChevronRight
} from 'lucide-react';

export function WorkflowSection() {
  const [activeStep, setActiveStep] = useState(1);

  const steps = [
    {
      step: 1,
      title: 'CSV Upload / Telemetry Ingestion',
      short: 'Alert Intake',
      icon: UploadCloud,
      badge: 'Step 01',
      headline: 'Multi-Source Canonical Log Parsing',
      description: 'Ingest raw CSV security feeds, Syslog, or API streams. The canonical schema parser validates and normalizes timestamps, source IPs, target assets, and signature categories.',
      tech: 'FastAPI Streaming Parser · Canonical Normalizer'
    },
    {
      step: 2,
      title: 'Alert Correlation Engine',
      short: 'Correlation',
      icon: Network,
      badge: 'Step 02',
      headline: 'Temporal & Topology Affinity Clustering',
      description: 'Clusters isolated security alerts into unified attack chains using IP affinity windows and multi-target lateral progression heuristics, slashing false positives by over 99%.',
      tech: 'Deterministic Affinity Graph Engine'
    },
    {
      step: 3,
      title: 'MITRE ATT&CK® Mapping',
      short: 'MITRE Mapping',
      icon: ShieldAlert,
      badge: 'Step 03',
      headline: 'Automated Matrix Alignment',
      description: 'Maps observed adversary behavioral signatures directly to MITRE ATT&CK enterprise tactics and sub-techniques (T1110, T1059, T1003, T1021) to expose the intrusion lifecycle.',
      tech: 'MITRE ATT&CK Framework v14.1 Knowledge Base'
    },
    {
      step: 4,
      title: 'Multi-Factor Risk Scoring',
      short: 'Risk Scoring',
      icon: Flame,
      badge: 'Step 04',
      headline: 'Calibrated 0–100 Severity Prioritisation',
      description: 'Evaluates baseline severity, attack progression stages, target asset criticality, and MITRE technique weights to compute a dynamic priority score for immediate SOC triage.',
      tech: 'Multi-Variable Calibrated Risk Algorithm'
    },
    {
      step: 5,
      title: 'AI Recommendation Agent',
      short: 'Playbooks',
      icon: Lightbulb,
      badge: 'Step 05',
      headline: 'Actionable Containment Playbooks',
      description: 'Synthesizes immediate containment measures, firewall block rules, infected host isolation scripts, and long-term hardening tasks tailored to the specific attacker vectors.',
      tech: 'LLaMA 3.3 70B & IBM watsonx.ai Agent'
    },
    {
      step: 6,
      title: 'BLUF Intelligence Reports',
      short: 'Executive BLUF',
      icon: FileText,
      badge: 'Step 06',
      headline: 'Commander Bottom Line Up Front Briefings',
      description: 'Automatically compiles executive threat briefings detailing the incident context, affected assets, financial risk, and command recommendations ready for one-click PDF dissemination.',
      tech: 'Executive BLUF Synthesis Agent · PDF Exporter'
    },
    {
      step: 7,
      title: 'AI Analyst Chat Copilot',
      short: 'Chat Copilot',
      icon: MessageSquare,
      badge: 'Step 07',
      headline: 'Grounded RAG Conversational Investigation',
      description: 'Interact directly with your live incident corpus in natural language. Powered by Qdrant vector embeddings to guarantee 100% factual citations and zero hallucination.',
      tech: 'Qdrant Vector DB · BAAI/bge-small RAG'
    }
  ];

  const current = steps[activeStep - 1];
  const CurrentIcon = current.icon;

  return (
    <section id="how-it-works" className="landing-workflow-section">
      <div className="landing-container">
        <div className="section-header-center">
          <span className="section-eyebrow">SEAMLESS END-TO-END PIPELINE</span>
          <h2 className="section-title">From Raw Alerts To Actionable Intelligence</h2>
          <p className="section-description">
            Experience an automated 7-stage pipeline that transforms unstructured security chaos into executive decision confidence in seconds.
          </p>
        </div>

        {/* Interactive Step Navigator Pills */}
        <div className="workflow-steps-nav">
          {steps.map((s) => {
            const Icon = s.icon;
            const isActive = activeStep === s.step;
            return (
              <button
                key={s.step}
                onClick={() => setActiveStep(s.step)}
                className={`step-pill-btn ${isActive ? 'active' : ''}`}
              >
                <div className="step-pill-icon">
                  <Icon size={15} />
                </div>
                <div className="step-pill-meta">
                  <span className="step-num">{s.badge}</span>
                  <span className="step-label">{s.short}</span>
                </div>
                {s.step < 7 && <ChevronRight size={13} className="step-arrow" />}
              </button>
            );
          })}
        </div>

        {/* Selected Step Detailed Feature Card */}
        <motion.div
          key={activeStep}
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="workflow-detail-card"
        >
          <div className="workflow-detail-grid">
            {/* Left description */}
            <div>
              <div className="workflow-step-tag">
                <CurrentIcon size={16} />
                <span>{current.badge} · {current.title}</span>
              </div>
              <h3 className="workflow-headline">{current.headline}</h3>
              <p className="workflow-description">{current.description}</p>
              
              <div className="workflow-tech-pill">
                <Cpu size={14} color="var(--blue)" />
                <span>Engine: {current.tech}</span>
              </div>
            </div>

            {/* Right interactive visual stage */}
            <div className="workflow-visual-stage">
              <div className="stage-mini-box">
                <div className="stage-header">
                  <span className="stage-indicator" />
                  <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)' }}>
                    AUTOMATED STAGE EXECUTION
                  </span>
                </div>

                <div className="stage-flow-visual">
                  <div className="flow-step prev">
                    <span className="flow-node" />
                    <span>Raw Input</span>
                  </div>
                  <div className="flow-connector" />
                  <div className="flow-step current">
                    <CurrentIcon size={18} />
                    <strong>{current.short}</strong>
                  </div>
                  <div className="flow-connector" />
                  <div className="flow-step next">
                    <span className="flow-node" />
                    <span>Prioritised Response</span>
                  </div>
                </div>

                <div className="stage-metrics-row">
                  <div>
                    <span className="sm-label">Execution Time</span>
                    <strong className="sm-val">&lt; 450ms</strong>
                  </div>
                  <div>
                    <span className="sm-label">Factual Grounding</span>
                    <strong className="sm-val" style={{ color: 'var(--low)' }}>100% Grounded</strong>
                  </div>
                  <div>
                    <span className="sm-label">Automation Level</span>
                    <strong className="sm-val" style={{ color: 'var(--blue)' }}>Deterministic</strong>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
