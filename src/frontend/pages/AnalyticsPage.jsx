import React, { useEffect, useState } from 'react';
import {
  BarChart3,
  TrendingUp,
  Clock,
  ShieldAlert,
  Layers,
  Activity,
  Zap,
  Target,
  Globe,
  Upload,
  Network
} from 'lucide-react';
import { AreaTrendChart, FrequencyBarChart, RiskDistributionChart } from '../components/Charts';
import { api } from '../services/api';

export function AnalyticsPage({ navigate }) {
  const [analytics, setAnalytics] = useState({
    total_alerts: 0,
    total_chains: 0,
    unique_sources: 0,
    unique_destinations: 0,
    attack_types: [],
    severity_breakdown: [],
    top_sources: [],
    top_targets: [],
    mitre_frequency: [],
    trend_data: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getAnalytics()
      .then(res => {
        if (res && typeof res === 'object') {
          setAnalytics(res);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const totalAlerts = analytics.total_alerts || 0;
  const attackTypes = analytics.attack_types || [];
  const topSources = analytics.top_sources || [];
  const topTargets = analytics.top_targets || [];
  const trendData = (analytics.trend_data || []).map(t => ({
    day: t.time,
    alerts: t.alerts,
    incidents: t.critical
  }));

  return (
    <div>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--cyan-bright)', textTransform: 'uppercase' }}>
            STRATEGIC SOC TELEMETRY
          </span>
          <h2 style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)', marginTop: 4 }}>
            Security Operations Analytics & Telemetry
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginTop: 4 }}>
            Dynamic volume distribution, adversary technique prevalence, and attack stage progression computed from ingested logs.
          </p>
        </div>

        {totalAlerts === 0 && !loading && (
          <button className="btn btn-primary" onClick={() => navigate('/upload')}>
            <Upload size={14} />
            <span>Upload Alerts CSV</span>
          </button>
        )}
      </div>

      {totalAlerts === 0 && !loading ? (
        <div className="soc-card" style={{ padding: '60px 24px', textAlign: 'center' }}>
          <BarChart3 size={48} color="var(--text-muted)" style={{ opacity: 0.4, marginBottom: 16 }} />
          <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
            0 Telemetry Logs Recorded
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: 13, maxWidth: 460, margin: '0 auto 20px' }}>
            Analytics charts and adversary IP metrics are computed dynamically from user uploaded CSV alerts. Upload alert logs to view SOC analytics.
          </p>
          <button className="btn btn-primary" onClick={() => navigate('/upload')}>
            <Upload size={14} />
            <span>Upload Alerts CSV</span>
          </button>
        </div>
      ) : (
        <>
          {/* Analytics KPI Row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14, marginBottom: 24 }}>
            <div className="kpi-card kpi-theme-alerts">
              <div className="kpi-top">
                <span className="kpi-label">Ingested Alert Events</span>
                <div className="kpi-icon-wrap">
                  <Activity size={16} />
                </div>
              </div>
              <div className="kpi-value-row">
                <span className="kpi-value">{totalAlerts.toLocaleString()}</span>
              </div>
              <div className="kpi-footer">
                <span className="kpi-pill kpi-pill-cyan">
                  <span className="kpi-pill-dot" />
                  Live Records
                </span>
                <span className="kpi-subtext">Dynamic database telemetry</span>
              </div>
            </div>

            <div className="kpi-card kpi-theme-correlated">
              <div className="kpi-top">
                <span className="kpi-label">Correlated Campaigns</span>
                <div className="kpi-icon-wrap">
                  <Network size={16} />
                </div>
              </div>
              <div className="kpi-value-row">
                <span className="kpi-value">{(analytics.total_chains || 0).toLocaleString()}</span>
              </div>
              <div className="kpi-footer">
                <span className="kpi-pill kpi-pill-indigo">
                  Affinity Clustered
                </span>
                <span className="kpi-subtext">Multi-stage incident chains</span>
              </div>
            </div>

            <div className="kpi-card kpi-theme-high">
              <div className="kpi-top">
                <span className="kpi-label">Unique Attacker Sources</span>
                <div className="kpi-icon-wrap">
                  <Globe size={16} />
                </div>
              </div>
              <div className="kpi-value-row">
                <span className="kpi-value">{(analytics.unique_sources || 0).toLocaleString()}</span>
              </div>
              <div className="kpi-footer">
                <span className="kpi-pill kpi-pill-high">
                  Adversary IPs
                </span>
                <span className="kpi-subtext">External attack origin points</span>
              </div>
            </div>

            <div className="kpi-card kpi-theme-mitre">
              <div className="kpi-top">
                <span className="kpi-label">Target Destinations</span>
                <div className="kpi-icon-wrap">
                  <Target size={16} />
                </div>
              </div>
              <div className="kpi-value-row">
                <span className="kpi-value">{(analytics.unique_destinations || 0).toLocaleString()}</span>
              </div>
              <div className="kpi-footer">
                <span className="kpi-pill kpi-pill-purple">
                  Internal Hosts
                </span>
                <span className="kpi-subtext">Target infrastructure assets</span>
              </div>
            </div>
          </div>

          {/* Longitudinal Trend Chart */}
          <div className="soc-card" style={{ marginBottom: 24 }}>
            <div className="card-header">
              <div>
                <h3 className="card-title">
                  <TrendingUp size={17} color="var(--cyan-bright)" />
                  <span>Telemetry Intake Velocity & Volume Timeline</span>
                </h3>
                <p className="card-subtitle">Aggregated temporal progression from ingested CSV timestamps</p>
              </div>
            </div>
            {trendData.length > 0 ? (
              <AreaTrendChart data={trendData} height={220} />
            ) : (
              <div style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
                No temporal telemetry series recorded.
              </div>
            )}
          </div>

          {/* 2-Column Analytics Grids */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(460px, 1fr))', gap: 20 }}>
            {/* Top Attack Event Types */}
            <div className="soc-card">
              <div className="card-header">
                <div>
                  <h3 className="card-title">
                    <Target size={17} color="var(--critical)" />
                    <span>Attack Stage & Event Distribution</span>
                  </h3>
                  <p className="card-subtitle">Breakdown of alert categories detected in user data</p>
                </div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {attackTypes.map((item, idx) => (
                  <div key={idx} style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 14px',
                    borderRadius: 6,
                    background: 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid var(--card-border)'
                  }}>
                    <div>
                      <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{item.name}</span>
                      <span className={`badge-severity ${(item.level || 'medium').toLowerCase()}`} style={{ marginLeft: 8, fontSize: 10 }}>
                        {item.level || 'Medium'}
                      </span>
                    </div>
                    <span className="mono" style={{ fontSize: 13, fontWeight: 700, color: 'var(--cyan-bright)' }}>
                      {item.count} events
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Top Attacker Source IPs */}
            <div className="soc-card">
              <div className="card-header">
                <div>
                  <h3 className="card-title">
                    <Globe size={17} color="var(--cyan-bright)" />
                    <span>Top Threat Actor Origins (Source IPs)</span>
                  </h3>
                  <p className="card-subtitle">Highest volume attack origins extracted from alerts</p>
                </div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {topSources.length === 0 ? (
                  <div style={{ padding: '24px 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
                    No source IPs recorded.
                  </div>
                ) : (
                  topSources.map((item, idx) => (
                    <div key={idx} style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '10px 14px',
                      borderRadius: 6,
                      background: 'var(--bg-tertiary)',
                      border: '1px solid var(--card-border)'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <code style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>{item.ip}</code>
                      </div>
                      <span className="mono" style={{ fontSize: 13, fontWeight: 700, color: '#F97316' }}>
                        {item.count} alerts
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
