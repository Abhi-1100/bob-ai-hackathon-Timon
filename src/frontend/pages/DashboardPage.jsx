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
  TrendingDown,
  Clock,
  ChevronRight,
  Globe,
  Database,
  RefreshCw
} from 'lucide-react';
import { api } from '../services/api';
import { streamUrl } from '../services/api';
import { useToast } from '../components/auth/Toast';
import { SeverityBadge, MitreChip } from '../components/Common';
import { AreaTrendChart, FrequencyBarChart, RiskDistributionChart } from '../components/Charts';

const DEFAULT_KPIS = {
  total_alerts: 0,
  total_chains: 0,
  critical_incidents: 0,
  high_risk_incidents: 0,
  medium_risk_incidents: 0,
  low_risk_incidents: 0,
  mitre_techniques_count: 0,
  avg_risk_score: 0.0,
  noise_reduction: 0.0,
};

export function DashboardPage({ navigate, onOpenChain }) {
  const [stats, setStats] = useState(DEFAULT_KPIS);
  const [loading, setLoading] = useState(true);
  const [liveConnected, setLiveConnected] = useState(false);
  const { showToast } = useToast();

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

  useEffect(() => {
    const token = localStorage.getItem('d2_access_token');
    if (!token || typeof EventSource === 'undefined') return undefined;
    const stream = new EventSource(streamUrl(token));
    const refresh = (event) => {
      setLiveConnected(true);
      try {
        const payload = JSON.parse(event.data || '{}');
        if (payload.tier === 'Critical') {
          showToast(`Critical chain ${payload.chain_id} requires immediate triage.`, 'error');
        }
      } catch (error) {
        console.warn('Invalid live stream event', error);
      }
      api.getStats().then((next) => next && setStats(next)).catch(() => {});
    };
    stream.addEventListener('chain_updated', refresh);
    stream.addEventListener('chain_closed', refresh);
    stream.onopen = () => setLiveConnected(true);
    stream.onerror = () => setLiveConnected(false);
    return () => {
      stream.close();
      setLiveConnected(false);
    };
  }, [showToast]);

  const totalAlerts = Number(stats.total_alerts || 0);
  const totalChains = Number(stats.total_chains || 0);
  const criticalCount = Number(stats.critical_incidents || 0);
  const highCount = Number(stats.high_risk_incidents || 0);
  const mitreCount = Number(stats.mitre_techniques_count || 0);
  const avgRisk = Number(stats.avg_risk_score || 0);
  const noiseRed = Number(stats.noise_reduction || 0);

  const kpiList = [
    {
      id: 'alerts',
      label: 'Total Ingested Alerts',
      value: totalAlerts.toLocaleString(),
      theme: 'kpi-theme-alerts',
      icon: Activity,
      pillText: totalAlerts > 0 ? `${totalAlerts.toLocaleString()} Logs` : '0 Logs Ingested',
      pillClass: 'kpi-pill-cyan',
      hasDot: true,
      subtext: 'From user uploaded CSV'
    },
    {
      id: 'chains',
      label: 'Correlated Chains',
      value: totalChains.toLocaleString(),
      theme: 'kpi-theme-correlated',
      icon: Network,
      pillText: totalChains > 0 ? `${noiseRed}% Noise Red.` : '0 Chains Formed',
      pillClass: 'kpi-pill-indigo',
      hasDot: false,
      hasTrendDown: totalChains > 0,
      subtext: 'Time & IP affinity clustering'
    },
    {
      id: 'critical',
      label: 'Critical Incidents',
      value: criticalCount,
      theme: 'kpi-theme-critical',
      icon: Flame,
      pillText: criticalCount > 0 ? 'Immediate Action' : '0 Active Threats',
      pillClass: criticalCount > 0 ? 'kpi-pill-critical' : 'kpi-pill-neutral',
      hasDot: criticalCount > 0,
      subtext: 'Urgent tier (Score ≥ 85)'
    },
    {
      id: 'high',
      label: 'High Risk Incidents',
      value: highCount,
      theme: 'kpi-theme-high',
      icon: AlertTriangle,
      pillText: highCount > 0 ? 'Priority Triage' : '0 Active Threats',
      pillClass: highCount > 0 ? 'kpi-pill-high' : 'kpi-pill-neutral',
      hasDot: highCount > 0,
      subtext: 'High queue (Score 70–84)'
    },
    {
      id: 'mitre',
      label: 'MITRE Techniques',
      value: mitreCount,
      theme: 'kpi-theme-mitre',
      icon: Layers,
      pillText: mitreCount > 0 ? `${mitreCount} ATT&CK Mapped` : '0 Mapped',
      pillClass: 'kpi-pill-purple',
      hasDot: false,
      subtext: 'Enterprise Knowledge Base'
    },
    {
      id: 'risk',
      label: 'Average Risk Score',
      value: avgRisk > 0 ? `${avgRisk}` : '0',
      unit: '/ 100',
      theme: 'kpi-theme-score',
      icon: ShieldAlert,
      pillText: avgRisk >= 75 ? 'Critical Tier' : avgRisk >= 50 ? 'Elevated Tier' : avgRisk > 0 ? 'Calibrated Scale' : 'No Scored Data',
      pillClass: avgRisk >= 75 ? 'kpi-pill-critical' : avgRisk >= 50 ? 'kpi-pill-high' : avgRisk > 0 ? 'kpi-pill-cyan' : 'kpi-pill-neutral',
      hasDot: avgRisk > 0,
      subtext: '0 - 100 Multi-factor scale',
      showProgress: true,
      progressValue: Math.min(avgRisk, 100),
      progressColor: avgRisk >= 75 ? 'var(--critical)' : avgRisk >= 50 ? 'var(--high)' : 'var(--cyan-bright)'
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
      {/* Skeleton loading on first cold fetch */}
      {loading && (
        <div>
          <div className="skeleton-grid" style={{ marginBottom: 24 }}>
            {[1,2,3,4].map(i => <span key={i} className="skeleton skeleton-kpi" />)}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
            <span className="skeleton skeleton-chart" />
            <span className="skeleton skeleton-chart" />
          </div>
          <div>
            {[1,2,3,4,5].map(i => <span key={i} className="skeleton skeleton-row" style={{ display: 'block' }} />)}
          </div>
        </div>
      )}

      {/* All content hidden while loading */}
      {!loading && (
        <div>
          {/* Top Banner if 0 data exists */}
          {totalAlerts === 0 && (
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
                  All 12 SOC modules, charts, attack chains, and MITRE analytics operate strictly on dynamic data.
                </p>
              </div>
            </div>
          )}

          {/* Header bar with Live Status & Refresh */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <span className={`badge-severity ${liveConnected ? 'low' : 'medium'}`} style={{ padding: '2px 8px', fontSize: 10, display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                  <span className="badge-dot" style={{ background: liveConnected ? '#16A34A' : '#F59E0B', width: 6, height: 6, borderRadius: '50%', display: 'inline-block' }} />
                  {liveConnected ? 'LIVE TELEMETRY STREAM' : 'RECONNECTING STREAM'}
                </span>
                <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
                  SOC COMMAND CENTER
                </span>
              </div>
              <h2 style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)', margin: 0, letterSpacing: '-0.02em' }}>
                Operational Threat Overview
              </h2>
            </div>
            <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <button className="btn btn-secondary" onClick={fetchStats} title="Refresh Live DB Stats">
                <RefreshCw size={14} className={loading ? 'spin' : ''} />
                <span>Refresh Telemetry</span>
              </button>
            </div>
          </div>

          {/* KPI Cards Grid */}
          <div className="kpi-grid">
            {kpiList.map((kpi) => {
              const Icon = kpi.icon;
              return (
                <div key={kpi.id} className={`kpi-card ${kpi.theme}`}>
                  <div className="kpi-top">
                    <span className="kpi-label" title={kpi.label}>{kpi.label}</span>
                    <div className="kpi-icon-wrap">
                      <Icon size={16} />
                    </div>
                  </div>

                  <div className="kpi-value-row">
                    <span className="kpi-value">{kpi.value}</span>
                    {kpi.unit && <span className="kpi-unit">{kpi.unit}</span>}
                  </div>

                  {kpi.showProgress && (
                    <div className="kpi-progress-bar">
                      <div
                        className="kpi-progress-fill"
                        style={{
                          width: `${kpi.progressValue}%`,
                          background: kpi.progressColor
                        }}
                      />
                    </div>
                  )}

                  <div className="kpi-footer">
                    <span className={`kpi-pill ${kpi.pillClass}`}>
                      {kpi.hasDot && <span className="kpi-pill-dot" />}
                      {kpi.hasTrendDown && <TrendingDown size={11} style={{ marginRight: 2 }} />}
                      <span>{kpi.pillText}</span>
                    </span>
                    <span className="kpi-subtext" title={kpi.subtext}>{kpi.subtext}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* 4 Interactive Charts Section */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(460px, 1fr))', gap: 20, marginBottom: 24, marginTop: 24 }}>
            {/* Chart 1: Ingestion & Incident Timeline */}
            <div className="soc-card">
              <div className="card-header">
                <div>
                  <h3 className="card-title">
                    <TrendingUp size={17} color="var(--cyan-bright)" />
                    <span>Alert Ingestion &amp; Incident Velocity Timeline</span>
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
                    <span>Top Detected MITRE ATT&amp;CK Techniques</span>
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
                  <span>0 MITRE techniques detected. Ingest alert logs to map ATT&amp;CK tactics.</span>
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
                  <p style={{ fontSize: 13, color: 'var(--text-secondary)', maxWidth: 450, margin: '0 auto' }}>
                    The database currently contains 0 correlated attack chains. Ingest alert logs to correlate multi-stage adversary campaigns.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
