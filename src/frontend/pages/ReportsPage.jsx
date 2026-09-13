import React, { useEffect, useState } from 'react';
import {
  FileText,
  Printer,
  ArrowLeft,
  ShieldAlert,
  Clock,
  CheckCircle2,
  AlertOctagon,
  ExternalLink,
  ChevronRight,
  Upload
} from 'lucide-react';
import { SeverityBadge } from '../components/Common';
import { api, listFrom } from '../services/api';

export function ReportsPage({ selectedReportId, onSelectReport, onBack, navigate }) {
  const [reports, setReports] = useState([]);
  const [activeId, setActiveId] = useState(selectedReportId || null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getReports()
      .then(res => {
        const list = listFrom(res, ['reports', 'results', 'data']);
        setReports(list);
        if (selectedReportId) {
          setActiveId(selectedReportId);
        }
      })
      .catch(() => setReports([]))
      .finally(() => setLoading(false));
  }, [selectedReportId]);

  const activeReport = activeId
    ? reports.find(r => r.chain_id === activeId) || reports[0]
    : null;

  if (activeReport) {
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
        <article className="soc-card" style={{ padding: '36px 40px', background: 'var(--card)', border: '1px solid var(--card-border)' }}>
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
                // TLP:AMBER // STRICT SOC DISSEMINATION
              </span>
              <h1 style={{ fontSize: 22, fontWeight: 900, color: 'var(--text-primary)', marginTop: 4, letterSpacing: '-0.02em' }}>
                COMMANDER THREAT BRIEFING (BLUF)
              </h1>
              <span className="mono" style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                Target Incident Reference: {activeReport.chain_id}
              </span>
            </div>
            <div style={{ textAlign: 'right' }}>
              <SeverityBadge value={activeReport.threat_level || 'Medium'} />
              <div className="mono" style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                Generated: Live Dynamic
              </div>
            </div>
          </div>

          {/* Section 1: Bottom Line Up Front */}
          <div style={{ marginBottom: 28 }}>
            <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--blue)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              1.0 BOTTOM LINE UP FRONT (BLUF)
            </span>
            <div style={{
              background: 'var(--bg-tertiary)',
              borderLeft: '4px solid var(--blue)',
              padding: '16px 20px',
              borderRadius: '0 8px 8px 0',
              marginTop: 8
            }}>
              <p style={{ color: 'var(--text-primary)', fontSize: 14.5, lineHeight: 1.6, fontWeight: 500, margin: 0 }}>
                {activeReport.executive_summary}
              </p>
            </div>
          </div>

          {/* Section 2: Attack Progression Overview */}
          <div style={{ marginBottom: 28 }}>
            <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--blue)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              2.0 ATTACK PROGRESSION OVERVIEW
            </span>
            <p style={{ color: 'var(--text-secondary)', fontSize: 13.5, lineHeight: 1.6, marginTop: 8 }}>
              {activeReport.attack_overview}
            </p>
          </div>

          {/* Section 3: Affected Assets & MITRE */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 28 }}>
            <div style={{ background: 'var(--bg-tertiary)', padding: 16, borderRadius: 8, border: '1px solid var(--card-border)' }}>
              <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Affected Assets & Targets
              </span>
              <p style={{ color: 'var(--text-primary)', fontSize: 13, marginTop: 6, margin: 0, fontWeight: 600 }}>
                {activeReport.affected_assets || 'Internal network telemetry'}
              </p>
            </div>
            <div style={{ background: 'var(--bg-tertiary)', padding: 16, borderRadius: 8, border: '1px solid var(--card-border)' }}>
              <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                MITRE ATT&CK Matrix Alignment
              </span>
              <p style={{ color: 'var(--text-primary)', fontSize: 13, marginTop: 6, margin: 0, fontWeight: 600 }}>
                {activeReport.mitre_summary || 'Multi-stage techniques'}
              </p>
            </div>
          </div>

          {/* Section 4: Recommended Commander Actions */}
          <div style={{ marginBottom: 28 }}>
            <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--blue)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              3.0 RECOMMENDED COMMAND ACTIONS
            </span>
            <div style={{ marginTop: 10, padding: 16, background: 'var(--critical-bg)', borderRadius: 8, border: '1px solid var(--critical-border)' }}>
              <p style={{ color: 'var(--critical-text)', fontSize: 13.5, lineHeight: 1.5, margin: 0, fontWeight: 500 }}>
                {activeReport.recommended_actions || 'Isolate compromised hosts and block attacker origin at edge firewalls.'}
              </p>
            </div>
          </div>

          {/* Section 5: Conclusion */}
          <div style={{ borderTop: '1px solid var(--card-border)', paddingTop: 16 }}>
            <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              4.0 CONCLUSION
            </span>
            <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginTop: 6, lineHeight: 1.5 }}>
              {activeReport.conclusion || 'Ongoing monitoring enabled across perimeter and endpoint telemetry.'}
            </p>
          </div>
        </article>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
        <div>
          <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--cyan-bright)', textTransform: 'uppercase' }}>
            EXECUTIVE INTELLIGENCE SYNTHESIS
          </span>
          <h2 style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)', marginTop: 4 }}>
            Commander BLUF Intelligence Briefings ({reports.length} Reports)
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginTop: 4 }}>
            Synthesized Bottom Line Up Front (BLUF) briefings ready for executive briefing, printable PDF export, and legal triage.
          </p>
        </div>

        {reports.length === 0 && !loading && (
          <button className="btn btn-primary" onClick={() => navigate('/upload')}>
            <Upload size={14} />
            <span>Upload Alerts CSV</span>
          </button>
        )}
      </div>

      {reports.length === 0 && !loading ? (
        <div className="soc-card" style={{ padding: '60px 24px', textAlign: 'center' }}>
          <FileText size={48} color="var(--text-muted)" style={{ opacity: 0.4, marginBottom: 16 }} />
          <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
            0 Intelligence Reports Available
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: 13, maxWidth: 460, margin: '0 auto 20px' }}>
            Executive BLUF briefings are generated dynamically from correlated attack chains. Ingest alert CSV logs to evaluate incidents.
          </p>
          <button className="btn btn-primary" onClick={() => navigate('/upload')}>
            <Upload size={14} />
            <span>Upload Alerts CSV</span>
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: 20 }}>
          {reports.map(r => (
            <div
              key={r.chain_id}
              className="soc-card hover-glow"
              onClick={() => setActiveId(r.chain_id)}
              style={{
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                borderLeft: `4px solid ${
                  (r.threat_level || '').toLowerCase() === 'critical' ? 'var(--critical)' :
                  (r.threat_level || '').toLowerCase() === 'high' ? 'var(--high)' : 'var(--medium)'
                }`
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <code style={{ fontSize: 14, fontWeight: 800, color: 'var(--cyan-bright)' }}>{r.chain_id}</code>
                  <SeverityBadge value={r.threat_level || 'Medium'} />
                </div>
                <h4 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.4, marginBottom: 8 }}>
                  {r.chain_id}: Commander Threat Briefing
                </h4>
                <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
                  {r.executive_summary?.slice(0, 160)}…
                </p>
              </div>

              <div style={{
                marginTop: 20,
                paddingTop: 14,
                borderTop: '1px solid var(--card-border)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <span className="mono" style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                  Target: {r.affected_assets?.slice(0, 20) || 'Internal subnet'}
                </span>
                <button
                  className="btn btn-secondary"
                  onClick={(e) => {
                    e.stopPropagation();
                    setActiveId(r.chain_id);
                  }}
                  style={{ padding: '4px 10px', fontSize: 12 }}
                >
                  <span>Read BLUF Briefing</span>
                  <ChevronRight size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
