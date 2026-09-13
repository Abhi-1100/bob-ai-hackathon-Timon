import React, { useState } from 'react';
import {
  FileText,
  Download,
  Printer,
  ArrowLeft,
  ShieldAlert,
  Clock,
  CheckCircle2,
  AlertOctagon,
  ExternalLink,
  ChevronRight
} from 'lucide-react';
import { SeverityBadge } from '../components/Common';
import { MOCK_ATTACK_CHAINS } from '../services/mockData';

export function ReportsPage({ selectedReportId, onSelectReport, onBack }) {
  const [activeId, setActiveId] = useState(selectedReportId || null);

  const activeChain = activeId
    ? MOCK_ATTACK_CHAINS.find(c => c.chain_id === activeId) || MOCK_ATTACK_CHAINS[0]
    : null;

  if (activeChain) {
    const r = activeChain.report || {};
    const recs = activeChain.recommendations?.immediate_actions || [];

    return (
      <div style={{ maxWidth: 900, margin: '0 auto' }}>
        {/* Toolbar */}
        <div className="no-print" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <button
            className="btn btn-secondary"
            onClick={() => {
              setActiveId(null);
              if (onBack) onBack();
            }}
          >
            <ArrowLeft size={15} />
            <span>Back to Intelligence Reports</span>
          </button>
          <button className="btn btn-primary" onClick={() => window.print()}>
            <Printer size={15} />
            <span>Export PDF / Print Briefing</span>
          </button>
        </div>

        {/* Printable Executive Briefing Document */}
        <article className="soc-card" style={{ padding: '36px 40px', background: '#0D1527', border: '1px solid #1E293B' }}>
          {/* Top Classified Header */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderBottom: '2px solid rgba(239, 68, 68, 0.4)',
            paddingBottom: 16,
            marginBottom: 24
          }}>
            <div>
              <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--critical)', letterSpacing: '0.12em', textTransform: 'uppercase' }}>
                DEFENSE INTELLIGENCE BRIEFING // BLUF
              </span>
              <h2 style={{ fontSize: 22, fontWeight: 800, color: '#fff', marginTop: 2 }}>
                Incident Commander Briefing: {activeChain.chain_id}
              </h2>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                DTG: 2026-09-13 20:00:00 UTC
              </div>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--cyan-bright)' }}>
                SENTINEL FORGE AI CO-PILOT
              </div>
            </div>
          </div>

          {/* Threat Level Banner */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px 20px',
            borderRadius: 8,
            background: 'var(--critical-bg)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            marginBottom: 24
          }}>
            <div>
              <span style={{ fontSize: 11, fontWeight: 700, color: '#FCA5A5', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                EVALUATED THREAT SEVERITY
              </span>
              <h3 style={{ fontSize: 22, fontWeight: 900, color: '#EF4444', margin: '2px 0' }}>
                {activeChain.severity} (Score: {activeChain.risk_score} / 100)
              </h3>
            </div>
            <AlertOctagon size={42} color="var(--critical)" />
          </div>

          {/* 1. Executive Summary (BLUF) */}
          <section style={{ marginBottom: 24 }}>
            <h4 style={{ fontSize: 13, fontWeight: 800, color: 'var(--cyan-bright)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>
              1. Executive Summary (BLUF)
            </h4>
            <p style={{ fontSize: 14, lineHeight: 1.7, color: 'var(--text-primary)' }}>
              {r.executive_summary || 'Cross-domain threat campaign actively propagating across network segments.'}
            </p>
          </section>

          {/* 2. Attack Overview */}
          <section style={{ marginBottom: 24 }}>
            <h4 style={{ fontSize: 13, fontWeight: 800, color: 'var(--cyan-bright)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>
              2. Attack Overview & Campaign Vector
            </h4>
            <p style={{ fontSize: 13.5, lineHeight: 1.7, color: 'var(--text-secondary)' }}>
              {r.attack_overview || 'Adversary leveraged external reconnaissance to locate open ports, subsequently executing brute-force credential attacks.'}
            </p>
          </section>

          {/* 3. Affected Infrastructure */}
          <section style={{ marginBottom: 24 }}>
            <h4 style={{ fontSize: 13, fontWeight: 800, color: 'var(--cyan-bright)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>
              3. Affected Critical Infrastructure
            </h4>
            <p style={{ fontSize: 13.5, lineHeight: 1.7, color: 'var(--text-secondary)' }}>
              {r.affected_assets || `Primary Host: ${activeChain.dest_ips?.[0] || '10.0.4.12'}, Database Core: 10.0.2.8`}
            </p>
          </section>

          {/* 4. MITRE Mapping Summary */}
          <section style={{ marginBottom: 24 }}>
            <h4 style={{ fontSize: 13, fontWeight: 800, color: 'var(--cyan-bright)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>
              4. MITRE ATT&CK Framework Correlation
            </h4>
            <p style={{ fontSize: 13.5, lineHeight: 1.7, color: 'var(--text-secondary)', marginBottom: 10 }}>
              {r.mitre_summary || 'Mapped across Reconnaissance, Credential Access, and Lateral Movement stages.'}
            </p>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {(activeChain.mitre_techniques || []).map((t, idx) => (
                <span
                  key={idx}
                  style={{
                    padding: '3px 10px',
                    borderRadius: 4,
                    background: 'rgba(255, 255, 255, 0.04)',
                    border: '1px solid var(--card-border)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 12,
                    color: 'var(--cyan-bright)'
                  }}
                >
                  {t.technique_id || t.id}: {t.name}
                </span>
              ))}
            </div>
          </section>

          {/* 5. Recommended Actions */}
          <section style={{ marginBottom: 24 }}>
            <h4 style={{ fontSize: 13, fontWeight: 800, color: 'var(--cyan-bright)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>
              5. Priority Tactical Remediation
            </h4>
            <ul style={{ paddingLeft: 20, display: 'flex', flexDirection: 'column', gap: 6, fontSize: 13.5, color: 'var(--text-secondary)' }}>
              {recs.map((item, idx) => (
                <li key={idx} style={{ lineHeight: 1.6 }}>{item}</li>
              ))}
            </ul>
          </section>

          {/* 6. Strategic Conclusion */}
          <section style={{ paddingTop: 16, borderTop: '1px solid var(--card-border)' }}>
            <h4 style={{ fontSize: 13, fontWeight: 800, color: 'var(--cyan-bright)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>
              6. Conclusion & Defense Posture Status
            </h4>
            <p style={{ fontSize: 13.5, lineHeight: 1.7, color: 'var(--text-secondary)' }}>
              {r.conclusion || 'Containment commands queued for execution. Security posture escalated to DEFCON 2 across affected subnets.'}
            </p>
          </section>
        </article>
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--cyan-bright)', textTransform: 'uppercase' }}>
          COMMANDER INTELLIGENCE ARCHIVE
        </span>
        <h2 style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)', marginTop: 4 }}>
          Executive BLUF Intelligence Reports
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginTop: 4 }}>
          Structured Bottom-Line-Up-Front briefings synthesized for leadership, summarizing technical kill-chains into tactical decision assets.
        </p>
      </div>

      <div className="soc-card">
        <div className="soc-table-wrap">
          <table className="soc-table">
            <thead>
              <tr>
                <th>Report ID / Chain</th>
                <th>Threat Level</th>
                <th>Risk Score</th>
                <th>Executive BLUF Summary</th>
                <th>Source Model</th>
                <th>Generated At</th>
                <th style={{ textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {MOCK_ATTACK_CHAINS.map(c => (
                <tr key={c.chain_id} onClick={() => setActiveId(c.chain_id)}>
                  <td>
                    <code style={{ fontSize: 13.5, fontWeight: 800, color: 'var(--cyan-bright)' }}>
                      RPT-{c.chain_id}
                    </code>
                  </td>
                  <td>
                    <SeverityBadge value={c.severity} />
                  </td>
                  <td>
                    <span className="mono" style={{ fontWeight: 800, color: '#fff' }}>
                      {c.risk_score} / 100
                    </span>
                  </td>
                  <td style={{ maxWidth: 380 }}>
                    <div style={{
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      color: 'var(--text-secondary)',
                      fontSize: 12.5
                    }}>
                      {c.report?.executive_summary || 'Automated multi-vector threat brief.'}
                    </div>
                  </td>
                  <td>
                    <span style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>
                      Llama 3.3 70B (watsonx)
                    </span>
                  </td>
                  <td>
                    <span className="mono" style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      {c.created_at || 'Just now'}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button
                      className="btn btn-secondary"
                      onClick={(e) => {
                        e.stopPropagation();
                        setActiveId(c.chain_id);
                      }}
                      style={{ padding: '5px 12px', fontSize: 12 }}
                    >
                      <span>Read Brief</span>
                      <ChevronRight size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
