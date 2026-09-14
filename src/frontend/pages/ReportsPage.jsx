import React, { useEffect, useState } from 'react';
import {
  FileText,
  Printer,
  ArrowLeft,
  Download,
  FileDown,
  ShieldAlert,
  Clock,
  ChevronRight,
  Upload,
  Search,
  Filter,
  AlertTriangle,
  CheckCircle2,
  Eye,
  RefreshCw,
  Archive,
} from 'lucide-react';
import { SeverityBadge } from '../components/Common';
import { api, listFrom } from '../services/api';

/* â”€â”€ helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
const SEV_COLOR = {
  critical: 'var(--critical)',
  high: 'var(--high)',
  medium: 'var(--medium)',
  low: 'var(--low)',
};
const SEV_BG = {
  critical: 'var(--critical-bg)',
  high: 'var(--high-bg)',
  medium: 'var(--medium-bg)',
  low: 'var(--low-bg)',
};

function downloadCSV(reports) {
  const headers = ['Chain ID', 'Threat Level', 'BLUF Summary', 'Affected Assets', 'MITRE Summary', 'Recommended Actions'];
  const rows = reports.map(r => [
    r.chain_id,
    r.threat_level || 'Medium',
    (r.executive_summary || '').replace(/,/g, ';'),
    (r.affected_assets || '').replace(/,/g, ';'),
    (r.mitre_summary || '').replace(/,/g, ';'),
    (r.recommended_actions || '').replace(/,/g, ';'),
  ]);
  const csv = [headers, ...rows].map(row => row.map(c => `"${c}"`).join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `threat_intel_reports_${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(a.href);
}

function downloadJSON(reports) {
  const blob = new Blob([JSON.stringify(reports, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `threat_intel_reports_${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
  URL.revokeObjectURL(a.href);
}

/* â”€â”€ Detail view â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
function ReportDetail({ report, onBack }) {
  const sev = (report.threat_level || 'medium').toLowerCase();
  return (
    <div>
      {/* Top toolbar */}
      <div className="no-print" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <button className="btn btn-secondary" onClick={onBack}>
          <ArrowLeft size={15} />
          <span>Back to Reports</span>
        </button>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-secondary" onClick={() => {
            const el = document.getElementById('report-detail');
            const blob = new Blob([el.innerText], { type: 'text/plain' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = `BLUF_${report.chain_id}.txt`;
            a.click();
          }}>
            <FileDown size={14} />
            <span>Download TXT</span>
          </button>
          <button className="btn btn-primary" onClick={() => window.print()}>
            <Printer size={14} />
            <span>Export PDF</span>
          </button>
        </div>
      </div>

      {/* Report document */}
      <article id="report-detail" style={{
        background: 'var(--card)',
        border: '1px solid var(--card-border)',
        borderRadius: 16,
        padding: '40px 44px',
        maxWidth: 900,
        margin: '0 auto',
        boxShadow: '0 4px 32px rgba(0,0,0,0.06)',
      }}>
        {/* Classification banner */}
        <div style={{
          background: 'rgba(239,68,68,0.08)',
          border: '1px solid rgba(239,68,68,0.3)',
          borderRadius: 8,
          padding: '8px 16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 24,
        }}>
          <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--critical)', letterSpacing: '0.12em', textTransform: 'uppercase' }}>
            âš  TLP:AMBER â€” Strict SOC Dissemination Only
          </span>
          <span className="mono" style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            Ref: {report.chain_id}
          </span>
        </div>

        {/* Title row */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 28, gap: 16, flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--cyan-bright)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6 }}>
              Commander BLUF Intelligence Briefing
            </div>
            <h1 style={{ fontSize: 26, fontWeight: 900, color: 'var(--text-primary)', margin: 0, letterSpacing: '-0.02em', lineHeight: 1.3 }}>
              {report.chain_id}: Threat Briefing Report
            </h1>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6, flexShrink: 0 }}>
            <SeverityBadge value={report.threat_level || 'Medium'} />
            <span className="mono" style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              Generated: {new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}
            </span>
          </div>
        </div>

        <div style={{ borderTop: '2px solid var(--card-border)', marginBottom: 28 }} />

        {/* Section 1 â€” BLUF */}
        <Section num="1.0" title="Bottom Line Up Front (BLUF)" accent="var(--blue)">
          <div style={{
            background: 'var(--bg-tertiary)',
            borderLeft: '4px solid var(--blue)',
            padding: '16px 20px',
            borderRadius: '0 10px 10px 0',
          }}>
            <p style={{ color: 'var(--text-primary)', fontSize: 14.5, lineHeight: 1.7, fontWeight: 500, margin: 0 }}>
              {report.executive_summary || 'No executive summary available.'}
            </p>
          </div>
        </Section>

        {/* Section 2 â€” Attack Progression */}
        <Section num="2.0" title="Attack Progression Overview" accent="var(--blue)">
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, lineHeight: 1.7, margin: 0 }}>
            {report.attack_overview || 'Attack chain details are being synthesized.'}
          </p>
        </Section>

        {/* Section 3 â€” Assets + MITRE */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16, marginBottom: 28 }}>
          <InfoBox label="Affected Assets & Targets" value={report.affected_assets || 'Internal network telemetry'} />
          <InfoBox label="MITRE ATT&CK Alignment" value={report.mitre_summary || 'Multi-stage adversary techniques'} />
        </div>

        {/* Section 4 â€” Recommended Actions */}
        <Section num="3.0" title="Recommended Command Actions" accent="var(--critical)">
          <div style={{
            background: 'var(--critical-bg)',
            border: '1px solid var(--critical-border)',
            borderLeft: '4px solid var(--critical)',
            padding: '16px 20px',
            borderRadius: '0 10px 10px 0',
          }}>
            <p style={{ color: 'var(--critical-text)', fontSize: 14, lineHeight: 1.7, margin: 0, fontWeight: 500 }}>
              {report.recommended_actions || 'Isolate compromised hosts and block attacker origin at edge firewalls.'}
            </p>
          </div>
        </Section>

        {/* Section 5 â€” Conclusion */}
        <Section num="4.0" title="Conclusion & Disposition" accent="var(--text-muted)" last>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, lineHeight: 1.7, margin: 0 }}>
            {report.conclusion || 'Ongoing monitoring enabled across perimeter and endpoint telemetry. Threat intelligence shared with upstream SOC tiers.'}
          </p>
        </Section>

        {/* Footer */}
        <div style={{ borderTop: '1px solid var(--card-border)', paddingTop: 16, marginTop: 8, display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-muted)' }}>
          <span>Sentinel Forge SOC Intelligence Platform</span>
          <span className="mono">{report.chain_id} Â· AUTO-GENERATED Â· DO NOT DISTRIBUTE EXTERNALLY</span>
        </div>
      </article>
    </div>
  );
}

function Section({ num, title, accent, children, last }) {
  return (
    <div style={{ marginBottom: last ? 0 : 28 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
        <span style={{ fontSize: 10, fontWeight: 800, color: accent, letterSpacing: '0.1em', textTransform: 'uppercase', background: `${accent}18`, padding: '2px 8px', borderRadius: 4 }}>
          {num}
        </span>
        <span style={{ fontSize: 12, fontWeight: 800, color: 'var(--text-secondary)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
          {title}
        </span>
      </div>
      {children}
    </div>
  );
}

function InfoBox({ label, value }) {
  return (
    <div style={{ background: 'var(--bg-tertiary)', padding: '14px 16px', borderRadius: 10, border: '1px solid var(--card-border)' }}>
      <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>{label}</div>
      <p style={{ color: 'var(--text-primary)', fontSize: 13, margin: 0, fontWeight: 600, lineHeight: 1.5 }}>{value}</p>
    </div>
  );
}

/* â”€â”€ Main list view â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
export function ReportsPage({ selectedReportId, onSelectReport, onBack, navigate }) {
  const [reports, setReports] = useState([]);
  const [activeId, setActiveId] = useState(selectedReportId || null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterSev, setFilterSev] = useState('all');
  const [showDownloadMenu, setShowDownloadMenu] = useState(false);

  const fetchReports = () => {
    setLoading(true);
    api.getReports()
      .then(res => {
        const list = listFrom(res, ['reports', 'results', 'data']);
        setReports(list);
        if (selectedReportId) setActiveId(selectedReportId);
      })
      .catch(() => setReports([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchReports(); }, [selectedReportId]);

  const activeReport = activeId ? (reports.find(r => r.chain_id === activeId) || reports[0]) : null;

  if (activeReport) {
    return <ReportDetail report={activeReport} onBack={() => { setActiveId(null); if (onBack) onBack(); }} />;
  }

  // Filter + search
  const filtered = reports.filter(r => {
    const matchSev = filterSev === 'all' || (r.threat_level || '').toLowerCase() === filterSev;
    const matchSearch = !search || r.chain_id.toLowerCase().includes(search.toLowerCase()) ||
      (r.executive_summary || '').toLowerCase().includes(search.toLowerCase());
    return matchSev && matchSearch;
  });

  const stats = {
    total: reports.length,
    critical: reports.filter(r => (r.threat_level || '').toLowerCase() === 'critical').length,
    high: reports.filter(r => (r.threat_level || '').toLowerCase() === 'high').length,
    medium: reports.filter(r => (r.threat_level || '').toLowerCase() === 'medium').length,
  };

  return (
    <div>
      {/* â”€â”€ Page Header â”€â”€ */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--cyan-bright)', textTransform: 'uppercase' }}>
            Executive Intelligence Synthesis
          </span>
          <h2 style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)', marginTop: 4, marginBottom: 4 }}>
            Intelligence Briefing Reports
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: 13, margin: 0 }}>
            {reports.length} BLUF briefings Â· Printable PDF export Â· Legal triage ready
          </p>
        </div>

        {/* Action buttons */}
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <button className="btn btn-secondary" onClick={fetchReports} title="Refresh">
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
            <span>Refresh</span>
          </button>

          {reports.length > 0 && (
            <div style={{ position: 'relative' }}>
              <button
                className="btn btn-primary"
                onClick={() => setShowDownloadMenu(v => !v)}
                style={{ gap: 8 }}
              >
                <Download size={14} />
                <span>Download All Reports</span>
                <span style={{ marginLeft: 2, fontSize: 10 }}>â–¾</span>
              </button>
              {showDownloadMenu && (
                <div style={{
                  position: 'absolute',
                  top: '110%',
                  right: 0,
                  background: 'var(--card)',
                  border: '1px solid var(--card-border)',
                  borderRadius: 10,
                  boxShadow: '0 8px 32px rgba(0,0,0,0.14)',
                  minWidth: 200,
                  zIndex: 50,
                  overflow: 'hidden',
                }}>
                  <button
                    style={{ display: 'flex', alignItems: 'center', gap: 10, width: '100%', padding: '12px 16px', background: 'transparent', border: 'none', cursor: 'pointer', fontSize: 13, color: 'var(--text-primary)', textAlign: 'left' }}
                    onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-tertiary)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                    onClick={() => { downloadCSV(reports); setShowDownloadMenu(false); }}
                  >
                    <FileDown size={14} color="var(--cyan-bright)" />
                    Download as CSV
                  </button>
                  <button
                    style={{ display: 'flex', alignItems: 'center', gap: 10, width: '100%', padding: '12px 16px', background: 'transparent', border: 'none', cursor: 'pointer', fontSize: 13, color: 'var(--text-primary)', textAlign: 'left', borderTop: '1px solid var(--card-border)' }}
                    onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-tertiary)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                    onClick={() => { downloadJSON(reports); setShowDownloadMenu(false); }}
                  >
                    <Archive size={14} color="var(--blue)" />
                    Download as JSON
                  </button>
                  <button
                    style={{ display: 'flex', alignItems: 'center', gap: 10, width: '100%', padding: '12px 16px', background: 'transparent', border: 'none', cursor: 'pointer', fontSize: 13, color: 'var(--text-primary)', textAlign: 'left', borderTop: '1px solid var(--card-border)' }}
                    onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-tertiary)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                    onClick={() => { window.print(); setShowDownloadMenu(false); }}
                  >
                    <Printer size={14} color="var(--text-muted)" />
                    Print / Export PDF
                  </button>
                </div>
              )}
            </div>
          )}

          {reports.length === 0 && !loading && (
            <button className="btn btn-primary" onClick={() => navigate('/upload')}>
              <Upload size={14} />
              <span>Upload Alerts CSV</span>
            </button>
          )}
        </div>
      </div>

      {/* â”€â”€ Stats Strip â”€â”€ */}
      {reports.length > 0 && (
        <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
          {[
            { label: 'Total Reports', value: stats.total, color: 'var(--cyan-bright)', icon: FileText },
            { label: 'Critical', value: stats.critical, color: 'var(--critical)', icon: ShieldAlert },
            { label: 'High', value: stats.high, color: 'var(--high)', icon: AlertTriangle },
            { label: 'Medium', value: stats.medium, color: 'var(--medium)', icon: Clock },
          ].map(({ label, value, color, icon: Icon }) => (
            <div key={label} style={{
              background: 'var(--card)',
              border: '1px solid var(--card-border)',
              borderRadius: 12,
              padding: '12px 20px',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              flex: 1,
              minWidth: 120,
            }}>
              <div style={{ width: 34, height: 34, borderRadius: 8, background: `${color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Icon size={16} color={color} />
              </div>
              <div>
                <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1 }}>{value}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{label}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* â”€â”€ Filters & Search â”€â”€ */}
      {reports.length > 0 && (
        <div style={{ display: 'flex', gap: 12, marginBottom: 20, alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Search */}
          <div style={{ position: 'relative', flex: 1, minWidth: 200 }}>
            <Search size={14} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search by Chain ID or summaryâ€¦"
              style={{
                width: '100%',
                paddingLeft: 36,
                paddingRight: 12,
                paddingTop: 9,
                paddingBottom: 9,
                border: '1px solid var(--card-border)',
                borderRadius: 8,
                background: 'var(--card)',
                color: 'var(--text-primary)',
                fontSize: 13,
                outline: 'none',
                boxSizing: 'border-box',
              }}
            />
          </div>

          {/* Severity filter pills */}
          <div style={{ display: 'flex', gap: 6 }}>
            {['all', 'critical', 'high', 'medium', 'low'].map(sev => (
              <button
                key={sev}
                onClick={() => setFilterSev(sev)}
                style={{
                  padding: '6px 14px',
                  borderRadius: 20,
                  border: filterSev === sev ? 'none' : '1px solid var(--card-border)',
                  background: filterSev === sev
                    ? (sev === 'all' ? 'var(--cyan-bright)' : SEV_COLOR[sev])
                    : 'var(--card)',
                  color: filterSev === sev ? '#fff' : 'var(--text-secondary)',
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                  textTransform: 'capitalize',
                  transition: 'all 0.15s',
                }}
              >
                {sev === 'all' ? 'All' : sev.charAt(0).toUpperCase() + sev.slice(1)}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* â”€â”€ Empty state â”€â”€ */}
      {!loading && reports.length === 0 && (
        <div className="soc-card" style={{ padding: '60px 24px', textAlign: 'center' }}>
          <FileText size={48} color="var(--text-muted)" style={{ opacity: 0.3, marginBottom: 16 }} />
          <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
            No Intelligence Reports Available
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: 13, maxWidth: 460, margin: '0 auto 20px' }}>
            BLUF briefings are generated dynamically from correlated attack chains. Ingest CSV alerts to begin.
          </p>
          <button className="btn btn-primary" onClick={() => navigate('/upload')}>
            <Upload size={14} />
            <span>Upload Alerts CSV</span>
          </button>
        </div>
      )}

      {/* â”€â”€ Skeleton â”€â”€ */}
      {loading && (
        <div>
          {[1,2,3,4].map(i => <div key={i} className="skeleton skeleton-row" style={{ marginBottom: 12, height: 72 }} />)}
        </div>
      )}

      {/* â”€â”€ Reports Table â”€â”€ */}
      {!loading && filtered.length > 0 && (
        <div className="soc-card" style={{ padding: 0, overflow: 'hidden' }}>
          {/* Table header */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '140px 100px 1fr 180px 130px',
            padding: '12px 20px',
            background: 'var(--bg-tertiary)',
            borderBottom: '1px solid var(--card-border)',
            gap: 16,
          }}>
            {['Chain ID', 'Severity', 'BLUF Summary', 'Affected Assets', 'Actions'].map(h => (
              <span key={h} style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{h}</span>
            ))}
          </div>

          {/* Table rows */}
          {filtered.map((r, idx) => {
            const sev = (r.threat_level || 'medium').toLowerCase();
            const sevColor = SEV_COLOR[sev] || 'var(--medium)';
            return (
              <div
                key={r.chain_id}
                onClick={() => setActiveId(r.chain_id)}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '140px 100px 1fr 180px 130px',
                  padding: '16px 20px',
                  gap: 16,
                  borderBottom: idx < filtered.length - 1 ? '1px solid var(--card-border)' : 'none',
                  cursor: 'pointer',
                  alignItems: 'center',
                  borderLeft: `3px solid ${sevColor}`,
                  transition: 'background 0.15s',
                }}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-tertiary)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              >
                {/* Chain ID */}
                <div>
                  <code style={{ fontSize: 13, fontWeight: 800, color: 'var(--cyan-bright)' }}>{r.chain_id}</code>
                </div>

                {/* Severity badge */}
                <div>
                  <SeverityBadge value={r.threat_level || 'Medium'} />
                </div>

                {/* BLUF excerpt */}
                <div style={{ fontSize: 12.5, color: 'var(--text-secondary)', lineHeight: 1.5, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                  {r.executive_summary || 'No summary available.'}
                </div>

                {/* Affected assets */}
                <div style={{ fontSize: 12, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  {(r.affected_assets || 'Internal subnet').slice(0, 40)}
                </div>

                {/* Actions */}
                <div style={{ display: 'flex', gap: 6 }}>
                  <button
                    className="btn btn-secondary"
                    onClick={e => { e.stopPropagation(); setActiveId(r.chain_id); }}
                    style={{ padding: '5px 10px', fontSize: 11 }}
                  >
                    <Eye size={12} />
                    <span>View</span>
                  </button>
                  <button
                    className="btn btn-secondary"
                    title="Download this report as TXT"
                    onClick={e => {
                      e.stopPropagation();
                      const text = `CHAIN: ${r.chain_id}\nSEVERITY: ${r.threat_level}\n\nBLUF:\n${r.executive_summary}\n\nATTACK OVERVIEW:\n${r.attack_overview}\n\nAFFECTED ASSETS:\n${r.affected_assets}\n\nMITRE SUMMARY:\n${r.mitre_summary}\n\nRECOMMENDED ACTIONS:\n${r.recommended_actions}\n\nCONCLUSION:\n${r.conclusion}`;
                      const blob = new Blob([text], { type: 'text/plain' });
                      const a = document.createElement('a');
                      a.href = URL.createObjectURL(blob);
                      a.download = `BLUF_${r.chain_id}.txt`;
                      a.click();
                    }}
                    style={{ padding: '5px 8px', fontSize: 11 }}
                  >
                    <FileDown size={12} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* No match for filter */}
      {!loading && reports.length > 0 && filtered.length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
          <Search size={32} style={{ opacity: 0.3, marginBottom: 12 }} />
          <p>No reports match your search or filter.</p>
        </div>
      )}
    </div>
  );
}
