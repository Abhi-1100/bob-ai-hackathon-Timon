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
  BarChart3,
  Clock,
  ExternalLink,
  ChevronRight,
  Zap,
  Globe
} from 'lucide-react';
import { api, listFrom } from '../services/api';
import { SeverityBadge, MitreChip } from '../components/Common';
import { AreaTrendChart, FrequencyBarChart, RiskDistributionChart } from '../components/Charts';
import {
  MOCK_KPIS,
  MOCK_ATTACK_CHAINS,
  MOCK_TREND_DATA,
  MOCK_MITRE_FREQUENCY,
  MOCK_RISK_DISTRIBUTION,
  MOCK_HOURLY_VOLUME
} from '../services/mockData';

export function DashboardPage({ navigate, onOpenChain }) {
  const [chains, setChains] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api('/api/v1/chains/generate')
      .then(res => {
        const list = listFrom(res, ['chains', 'results', 'data']);
        setChains(list.length ? list : MOCK_ATTACK_CHAINS);
      })
      .catch(() => setChains(MOCK_ATTACK_CHAINS))
      .finally(() => setLoading(false));
  }, []);

  const kpiList = [
    {
      label: 'Total Ingested Alerts',
      value: MOCK_KPIS.total_alerts,
      trend: MOCK_KPIS.total_alerts_trend,
      icon: Activity,
      colorClass: 'kpi-cyan',
      footer: 'Across SIEM, Sensor & OSINT feeds'
    },
    {
      label: 'Correlated Chains',
      value: MOCK_KPIS.total_chains,
      trend: MOCK_KPIS.total_chains_trend,
      icon: Network,
      colorClass: 'kpi-blue',
      footer: 'Noise reduced by 98.7%'
    },
    {
      label: 'Critical Incidents',
      value: MOCK_KPIS.critical_incidents,
      trend: MOCK_KPIS.critical_trend,
      icon: Flame,
      colorClass: 'kpi-critical',
      footer: 'Active breach trajectory'
    },
    {
      label: 'High Risk Incidents',
      value: MOCK_KPIS.high_risk_incidents,
      trend: MOCK_KPIS.high_risk_trend,
      icon: AlertTriangle,
      colorClass: 'kpi-high',
      footer: 'SLA response < 1 hour'
    },
    {
      label: 'MITRE Techniques',
      value: MOCK_KPIS.mitre_techniques,
      trend: MOCK_KPIS.mitre_tactics,
      icon: Layers,
      colorClass: 'kpi-cyan',
      footer: 'Enterprise ATT&CK aligned'
    },
    {
      label: 'Average Risk Score',
      value: MOCK_KPIS.avg_risk_score,
      trend: MOCK_KPIS.avg_risk_trend,
      icon: ShieldAlert,
      colorClass: 'kpi-high',
      footer: '0 - 100 Calibrated scale'
    },
  ];

  return (
    <div>
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
        {/* Chart 1: Incident Trend */}
        <div className="soc-card">
          <div className="card-header">
            <div>
              <h3 className="card-title">
                <TrendingUp size={17} color="var(--cyan-bright)" />
                <span>7-Day Ingestion & Incident Trend</span>
              </h3>
              <p className="card-subtitle">Daily security event volume and correlated attack campaign velocity</p>
            </div>
            <span className="badge-severity low">Live Feed</span>
          </div>
          <AreaTrendChart data={MOCK_TREND_DATA} height={190} />
        </div>

        {/* Chart 2: Risk Distribution */}
        <div className="soc-card">
          <div className="card-header">
            <div>
              <h3 className="card-title">
                <Flame size={17} color="var(--high)" />
                <span>Campaign Risk Distribution</span>
              </h3>
              <p className="card-subtitle">Active incidents grouped by mathematical risk severity bands</p>
            </div>
            <button className="btn btn-secondary" onClick={() => navigate('/risk')} style={{ padding: '4px 10px', fontSize: 11 }}>
              Queue View <ArrowUpRight size={13} />
            </button>
          </div>
          <RiskDistributionChart distribution={MOCK_RISK_DISTRIBUTION} />
        </div>

        {/* Chart 3: MITRE Frequency */}
        <div className="soc-card">
          <div className="card-header">
            <div>
              <h3 className="card-title">
                <Layers size={17} color="var(--cyan-bright)" />
                <span>Top Detected MITRE ATT&CK Techniques</span>
              </h3>
              <p className="card-subtitle">Frequency of attacker tactics observed across correlated chains</p>
            </div>
            <button className="btn btn-secondary" onClick={() => navigate('/mitre')} style={{ padding: '4px 10px', fontSize: 11 }}>
              Full Matrix <ArrowUpRight size={13} />
            </button>
          </div>
          <FrequencyBarChart items={MOCK_MITRE_FREQUENCY.slice(0, 5)} />
        </div>

        {/* Chart 4: Hourly Alert Volume */}
        <div className="soc-card">
          <div className="card-header">
            <div>
              <h3 className="card-title">
                <Clock size={17} color="var(--blue)" />
                <span>24-Hour Alert Ingestion Timeline</span>
              </h3>
              <p className="card-subtitle">Aggregated multi-source telemetry intake distribution</p>
            </div>
            <span className="mono" style={{ fontSize: 11, color: 'var(--text-muted)' }}>UTC Standard</span>
          </div>
          <AreaTrendChart
            data={MOCK_HOURLY_VOLUME.map(v => ({ day: v.hour, alerts: v.volume }))}
            height={190}
          />
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
            <p className="card-subtitle">Machine-correlated multi-stage campaigns requiring SOC analyst triage</p>
          </div>
          <button className="btn btn-secondary" onClick={() => navigate('/attack-chains')}>
            <span>View All ({chains.length})</span>
            <ChevronRight size={15} />
          </button>
        </div>

        <div className="soc-table-wrap">
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
              {chains.slice(0, 5).map(c => {
                const id = c.chain_id || 'AC001';
                const score = c.risk_score || c.final_score || 85;
                const sev = c.severity || 'Critical';
                const techniques = c.mitre_techniques || [];

                return (
                  <tr key={id} onClick={() => onOpenChain(id)}>
                    <td>
                      <code style={{ fontWeight: 700, color: 'var(--cyan-bright)', fontSize: 13 }}>{id}</code>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <Globe size={13} color="var(--text-muted)" />
                        <code style={{ color: 'var(--text-primary)' }}>{c.source_ip || '198.51.100.24'}</code>
                      </div>
                    </td>
                    <td>
                      <span className="mono" style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                        {c.dest_ips?.slice(0, 2).join(', ') || '10.0.4.12, 10.0.4.15'}
                        {c.dest_ips?.length > 2 ? ` (+${c.dest_ips.length - 2})` : ''}
                      </span>
                    </td>
                    <td>
                      <span className="mono" style={{ fontWeight: 600 }}>{c.alert_count || 8} alerts</span>
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
        </div>
      </div>
    </div>
  );
}
