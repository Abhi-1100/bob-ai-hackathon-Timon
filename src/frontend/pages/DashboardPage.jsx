import React, { useEffect, useState } from 'react';
import {
  ShieldAlert,
  Flame,
  AlertTriangle,
  Network,
  Activity,
  Layers,
  ArrowUpRight,
  TrendingUp,
  Clock,
  ChevronRight,
  Upload,
  Globe,
  Database,
  RefreshCw
} from 'lucide-react';
import { api } from '../services/api';
import { SeverityBadge, MitreChip } from '../components/Common';
import { AreaTrendChart, FrequencyBarChart, RiskDistributionChart } from '../components/Charts';
import { DEFAULT_KPIS } from '../services/mockData';

export function DashboardPage({ navigate, onOpenChain }) {
  const [stats, setStats] = useState(DEFAULT_KPIS);
  const [loading, setLoading] = useState(true);

  const fetchStats = () => {
    setLoading(true);
    api.getStats()
      .then(res => {
        if (res && typeof res === 'object') {
          setStats(res);
        }
      })
      .catch(err => {
        console.error('Failed to load dashboard stats:', err);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const totalAlerts = Number(stats.total_alerts || 0);
  const totalChains = Number(stats.total_chains || 0);
  const criticalCount = Number(stats.critical_incidents || 0);
  const highCount = Number(stats.high_risk_incidents || 0);
  const mitreCount = Number(stats.mitre_techniques_count || 0);
  const avgRisk = Number(stats.avg_risk_score || 0);
  const noiseRed = Number(stats.noise_reduction || 0);

  const kpiList = [
    {
      label: 'Total Ingested Alerts',
      value: totalAlerts.toLocaleString(),
      trend: totalAlerts > 0 ? `${totalAlerts} logs` : '0 logs',
      icon: Activity,
      colorClass: 'kpi-cyan',
      footer: 'From user uploaded CSV'
    },
    {
      label: 'Correlated Chains',
      value: totalChains.toLocaleString(),
      trend: totalChains > 0 ? `${noiseRed}% reduction` : '0 chains',
      icon: Network,
      colorClass: 'kpi-blue',
      footer: 'Time & IP affinity clustering'
    },
    {
      label: 'Critical Incidents',
      value: criticalCount,
      trend: criticalCount > 0 ? 'Immediate action' : '0 active',
      icon: Flame,
      colorClass: 'kpi-critical',
      footer: 'Score ≥ 85 / 100'
    },
    {
      label: 'High Risk Incidents',
      value: highCount,
      trend: highCount > 0 ? 'Priority triage' : '0 active',
      icon: AlertTriangle,
      colorClass: 'kpi-high',
      footer: 'Score 70 - 84'
    },
    {
      label: 'MITRE Techniques',
      value: mitreCount,
      trend: mitreCount > 0 ? `${mitreCount} identified` : '0 mapped',
      icon: Layers,
      colorClass: 'kpi-cyan',
      footer: 'ATT&CK Knowledge Base'
    },
    {
      label: 'Average Risk Score',
      value: avgRisk > 0 ? `${avgRisk}` : '0',
      trend: avgRisk > 0 ? 'Dynamic multi-factor' : 'No scored data',
      icon: ShieldAlert,
      colorClass: 'kpi-high',
      footer: '0 - 100 Calibrated scale'
    },
  ];

  const recentIncidents = stats.recent_incidents || [];
  const timelineData = (stats.timeline || []).map(t => ({
    day: t.time,
    alerts: t.alerts,
    incidents: t.critical
  }));
  const riskDist = {
    critical: stats.critical_incidents || 0,
    high: stats.high_risk_incidents || 0,
    medium: stats.medium_risk_incidents || 0,
    low: stats.low_risk_incidents || 0,
  };
  const mitreFreq = stats.mitre_frequency || [];

  return (
    <div>
      {/* Top Banner if 0 data exists */}
      {totalAlerts === 0 && !loading && (
        <div style={{
          background: 'linear-gradient(90deg, rgba(6, 182, 212, 0.1) 0%, rgba(59, 130, 246, 0.05) 100%)',
          border: '1px solid rgba(6, 182, 212, 0.3)',
          borderRadius: 12,
          padding: '20px 24px',
          marginBottom: 24,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 16
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              <Database size={18} color="var(--cyan-bright)" />
              <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                Dynamic 0-State: No Security Logs Ingested Yet
              </h3>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: 13, margin: 0, maxWidth: 650 }}>
              All 12 SOC modules, charts, attack chains, and MITRE analytics operate strictly on dynamic data. Upload a raw security alert CSV to trigger the automated correlation and risk scoring engine.
            </p>
          </div>
          <button
            className="btn btn-primary"
            onClick={() => navigate('/upload')}
            style={{ padding: '10px 18px', fontSize: 13, fontWeight: 700 }}
          >
            <Upload size={16} />
            <span>Upload Alerts CSV</span>
          </button>
        </div>
      )}

      {/* Header bar with Refresh */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--cyan-bright)', textTransform: 'uppercase' }}>
            OPERATIONAL THREAT OVERVIEW
          </span>
          <h2 style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)', marginTop: 2 }}>
            Real-Time SOC Command Center
          </h2>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-secondary" onClick={fetchStats} title="Refresh Live DB Stats">
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
            <span>Refresh Telemetry</span>
          </button>
          <button className="btn btn-primary" onClick={() => navigate('/upload')}>
            <Upload size={14} />
            <span>Upload CSV</span>
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="kpi-grid">
        {kpiList.map((kpi, idx) => {
          const Icon = kpi.icon;
          return (
            <div key={idx} className={`kpi-card ${kpi.colorClass}`}>
              <div className="kpi-top">
                <span className="kpi-label">{kpi.label}</span>
                <div className="kpi-icon-wrap">
                  <Icon size={17} />
                </div>
              </div>
              <div className="kpi-value">{kpi.value}</div>
              <div className="kpi-footer">
                <span className="kpi-trend-positive">{kpi.trend}</span>
                <span className="kpi-footer-text">· {kpi.footer}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* 4 Interactive Charts Section */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(460px, 1fr))', gap: 20, marginBottom: 24 }}>
        {/* Chart 1: Ingestion & Incident Timeline */}
        <div className="soc-card">
          <div className="card-header">
            <div>
              <h3 className="card-title">
                <TrendingUp size={17} color="var(--cyan-bright)" />
                <span>Alert Ingestion & Incident Velocity Timeline</span>
              </h3>
              <p className="card-subtitle">Aggregated temporal volume from ingested CSV alerts</p>
            </div>
            <span className="badge-severity low">{totalAlerts > 0 ? 'Live Data' : '0 Events'}</span>
          </div>
          {timelineData.length > 0 ? (
            <AreaTrendChart data={timelineData} height={190} />
          ) : (
            <div style={{ height: 190, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
              <Clock size={32} style={{ opacity: 0.3, marginBottom: 8 }} />
              <span>No telemetry timeline available. Upload CSV alerts to render trend.</span>
            </div>
          )}
        </div>

        {/* Chart 2: Risk Distribution */}
        <div className="soc-card">
          <div className="card-header">
            <div>
              <h3 className="card-title">
                <Flame size={17} color="var(--high)" />
                <span>Attack Chain Risk Distribution</span>
              </h3>
              <p className="card-subtitle">Dynamic severity classification across correlated campaigns</p>
            </div>
            <button className="btn btn-secondary" onClick={() => navigate('/risk')} style={{ padding: '4px 10px', fontSize: 11 }}>
              Queue View <ArrowUpRight size={13} />
            </button>
          </div>
          {totalChains > 0 ? (
            <RiskDistributionChart distribution={riskDist} />
          ) : (
            <div style={{ height: 160, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
              <ShieldAlert size={32} style={{ opacity: 0.3, marginBottom: 8 }} />
              <span>0 Attack chains scored. Upload CSV alerts to correlate incidents.</span>
            </div>
          )}
        </div>

        {/* Chart 3: MITRE Frequency */}
        <div className="soc-card">
          <div className="card-header">
            <div>
              <h3 className="card-title">
                <Layers size={17} color="var(--cyan-bright)" />
                <span>Top Detected MITRE ATT&CK Techniques</span>
              </h3>
              <p className="card-subtitle">Observed adversary tactics mapped from correlated chains</p>
            </div>
            <button className="btn btn-secondary" onClick={() => navigate('/mitre')} style={{ padding: '4px 10px', fontSize: 11 }}>
              Full Matrix <ArrowUpRight size={13} />
            </button>
          </div>
          {mitreFreq.length > 0 ? (
            <FrequencyBarChart items={mitreFreq.slice(0, 5)} />
          ) : (
            <div style={{ height: 160, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
              <Layers size={32} style={{ opacity: 0.3, marginBottom: 8 }} />
              <span>0 MITRE techniques detected. Ingest alert logs to map ATT&CK tactics.</span>
            </div>
          )}
        </div>

        {/* Chart 4: Hourly / Granular Volume Breakdown */}
        <div className="soc-card">
          <div className="card-header">
            <div>
              <h3 className="card-title">
                <Clock size={17} color="var(--blue)" />
                <span>Alert Progression Distribution</span>
              </h3>
              <p className="card-subtitle">Chronological progression of security telemetry</p>
            </div>
            <span className="mono" style={{ fontSize: 11, color: 'var(--text-muted)' }}>Real-time DB</span>
          </div>
          {timelineData.length > 0 ? (
            <AreaTrendChart data={timelineData} height={190} />
          ) : (
            <div style={{ height: 190, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
              <Activity size={32} style={{ opacity: 0.3, marginBottom: 8 }} />
              <span>No active telemetry logs detected.</span>
            </div>
          )}
        </div>
      </div>

      {/* Recent Incidents Table */}
      <div className="soc-card">
        <div className="card-header">
          <div>
            <h3 className="card-title">
              <Network size={17} color="var(--cyan-bright)" />
              <span>Prioritized Correlated Attack Chains</span>
            </h3>
            <p className="card-subtitle">Dynamically correlated multi-stage campaigns from uploaded CSV</p>
          </div>
          <button className="btn btn-secondary" onClick={() => navigate('/attack-chains')}>
            <span>View All ({totalChains})</span>
            <ChevronRight size={15} />
          </button>
        </div>

        <div className="soc-table-wrap">
          {recentIncidents.length > 0 ? (
            <table className="soc-table">
              <thead>
                <tr>
                  <th>Chain ID</th>
                  <th>Source IP</th>
                  <th>Target IPs</th>
                  <th>Events</th>
                  <th>Risk Score</th>
                  <th>Severity</th>
                  <th>MITRE Techniques</th>
                  <th>Observed At</th>
                  <th style={{ textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {recentIncidents.map(c => {
                  const id = c.chain_id;
                  const score = c.risk_score || 0;
                  const sev = c.severity || 'Medium';
                  const techniques = c.mitre_techniques || [];

                  return (
                    <tr key={id} onClick={() => onOpenChain(id)}>
                      <td>
                        <code style={{ fontWeight: 700, color: 'var(--cyan-bright)', fontSize: 13 }}>{id}</code>
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <Globe size={13} color="var(--text-muted)" />
                          <code style={{ color: 'var(--text-primary)' }}>{c.source_ip}</code>
                        </div>
                      </td>
                      <td>
                        <span className="mono" style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                          {c.dest_ips?.slice(0, 2).join(', ') || 'Internal host'}
                          {c.dest_ips?.length > 2 ? ` (+${c.dest_ips.length - 2})` : ''}
                        </span>
                      </td>
                      <td>
                        <span className="mono" style={{ fontWeight: 600 }}>{c.alert_count || 1} alerts</span>
                      </td>
                      <td>
                        <span className="mono" style={{
                          fontWeight: 800,
                          color: score >= 85 ? 'var(--critical)' : score >= 70 ? 'var(--high)' : 'var(--medium)'
                        }}>
                          {score} / 100
                        </span>
                      </td>
                      <td>
                        <SeverityBadge value={sev} />
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                          {techniques.slice(0, 2).map((t, idx) => (
                            <MitreChip key={idx} id={t.technique_id || t.id} />
                          ))}
                          {techniques.length > 2 && (
                            <span style={{ fontSize: 11, color: 'var(--text-muted)', alignSelf: 'center' }}>
                              +{techniques.length - 2}
                            </span>
                          )}
                        </div>
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
                            onOpenChain(id);
                          }}
                          style={{ padding: '4px 10px', fontSize: 12 }}
                        >
                          <span>Investigate</span>
                          <ArrowUpRight size={13} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          ) : (
            <div style={{ padding: '48px 24px', textAlign: 'center' }}>
              <Network size={40} color="var(--text-muted)" style={{ opacity: 0.4, marginBottom: 12 }} />
              <h4 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 6 }}>
                No Attack Chains Found in Database
              </h4>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', maxWidth: 450, margin: '0 auto 20px' }}>
                The database currently contains 0 correlated attack chains. Ingest alert logs via CSV upload to correlate multi-stage adversary campaigns.
              </p>
              <button className="btn btn-primary" onClick={() => navigate('/upload')}>
                <Upload size={14} />
                <span>Upload Alert CSV</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
