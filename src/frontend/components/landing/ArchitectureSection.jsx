import React from 'react';
import { motion } from 'framer-motion';
import {
  UploadCloud,
  Network,
  ShieldAlert,
  Flame,
  Lightbulb,
  FileText,
  Database,
  MessageSquare,
  ArrowDown,
  Cpu,
  Server,
  Layers,
  CheckCircle2
} from 'lucide-react';

export function ArchitectureSection() {
  const nodes = [
    {
      level: 1,
      title: 'Alert Ingestion Layer',
      subtitle: 'Raw Security Telemetry & Syslogs',
      icon: UploadCloud,
      tech: 'FastAPI Streaming Parser · Canonical Normalizer',
      color: 'var(--cyan)'
    },
    {
      level: 2,
      title: 'Correlation Engine',
      subtitle: 'Temporal & Topology Affinity Clustering',
      icon: Network,
      tech: 'Affinity Graph Algorithm · Subnet Grouping',
      color: 'var(--blue)'
    },
    {
      level: 3,
      title: 'MITRE ATT&CK® Knowledge Engine',
      subtitle: 'Automated Matrix Behavioral Alignment',
      icon: ShieldAlert,
      tech: 'MITRE ATT&CK v14.1 Enterprise Mappings',
      color: 'var(--blue)'
    },
    {
      level: 4,
      title: 'Multi-Factor Risk Scoring Engine',
      subtitle: 'Dynamic 0–100 Impact Calibration',
      icon: Flame,
      tech: 'Asset Value · Severity · Progression Depth',
      color: 'var(--high)'
    },
    {
      level: 5,
      title: 'Recommendation & Mitigation Agent',
      subtitle: 'Actionable Containment Playbooks',
      icon: Lightbulb,
      tech: 'LLaMA 3.3 70B & watsonx.ai Orchestration',
      color: 'var(--blue)'
    },
    {
      level: 6,
      title: 'BLUF Intelligence Synthesis',
      subtitle: 'Commander Bottom Line Up Front Briefings',
      icon: FileText,
      tech: 'TLP:AMBER Executive PDF Export Engine',
      color: 'var(--critical)'
    },
    {
      level: 7,
      title: 'Qdrant Vector Database Storage',
      subtitle: 'High-Dimensional Embeddings & Context Index',
      icon: Database,
      tech: 'Cosine Similarity · In-Memory / Distributed HNSW',
      color: 'var(--cyan)'
    },
    {
      level: 8,
      title: 'AI Analyst Chat Copilot Interface',
      subtitle: 'Natural Language Threat Hunting',
      icon: MessageSquare,
      tech: 'Zero-Hallucination Grounded RAG Pipeline',
      color: 'var(--low)'
    }
  ];

  return (
    <section id="architecture" className="landing-architecture-section">
      <div className="landing-container">
        <div className="section-header-center">
          <span className="section-eyebrow">ENTERPRISE PIPELINE TOPOLOGY</span>
          <h2 className="section-title">Built On Modern Security & AI Infrastructure</h2>
          <p className="section-description">
            A resilient, zero-trust decoupled micro-architecture engineered for high throughput, sub-second correlation, and deterministic execution.
          </p>
        </div>

        {/* Vertical Flow Architecture Pipeline */}
        <div className="architecture-flow-container">
          {nodes.map((node, idx) => {
            const Icon = node.icon;
            return (
              <React.Fragment key={node.level}>
                <motion.div
                  className="arch-node-card"
                  whileHover={{ scale: 1.02, transition: { duration: 0.2 } }}
                >
                  <div className="arch-node-left">
                    <div className="arch-node-num">0{node.level}</div>
                    <div className="arch-node-icon" style={{ borderColor: node.color, color: node.color }}>
                      <Icon size={20} />
                    </div>
                  </div>

                  <div className="arch-node-center">
                    <h4 className="arch-node-title">{node.title}</h4>
                    <p className="arch-node-sub">{node.subtitle}</p>
                  </div>

                  <div className="arch-node-right">
                    <span className="arch-tech-badge">
                      <Cpu size={12} />
                      {node.tech}
                    </span>
                  </div>
                </motion.div>

                {idx < nodes.length - 1 && (
                  <div className="arch-flow-connector">
                    <div className="connector-line" />
                    <div className="connector-arrow">
                      <ArrowDown size={14} />
                    </div>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* Infrastructure Highlights Bar */}
        <div className="infra-stats-card">
          <div className="infra-stat-item">
            <Server size={18} color="var(--blue)" />
            <div>
              <strong>FastAPI Async ASGI</strong>
              <span>Sub-5ms route execution</span>
            </div>
          </div>
          <div className="infra-stat-item">
            <Database size={18} color="var(--blue)" />
            <div>
              <strong>Qdrant Vector Database</strong>
              <span>384-dim dense cosine embeddings</span>
            </div>
          </div>
          <div className="infra-stat-item">
            <Cpu size={18} color="var(--blue)" />
            <div>
              <strong>Groq Cloud & watsonx</strong>
              <span>Llama 3.3 70B & Granite 13B</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
