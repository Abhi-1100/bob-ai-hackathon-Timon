import React from 'react';
import {
  BarChart3,
  TrendingUp,
  Clock,
  ShieldAlert,
  Layers,
  Activity,
  Zap,
  Target
} from 'lucide-react';
import { AreaTrendChart, FrequencyBarChart, RiskDistributionChart } from '../components/Charts';
import {
  MOCK_TREND_DATA,
  MOCK_MITRE_FREQUENCY,
  MOCK_RISK_DISTRIBUTION
} from '../services/mockData';

export function AnalyticsPage() {
  const attackTypes = [
    { name: 'Brute Force & Credential Spray', count: 48, level: 'Critical' },
    { name: 'Network Port & Service Sweeps', count: 42, level: 'Medium' },
    { name: 'Web Application RCE & Injection', count: 35, level: 'Critical' },
    { name: 'In-Memory Script Execution', count: 29, level: 'High' },
    { name: 'Lateral SMB / SSH Pivots', count: 19, level: 'High' },
    { name: 'Volumetric DDoS Flooding', count: 14, level: 'High' }
  ];

  const sourceBreakdown = [
    { name: 'Enterprise SIEM (Splunk / QRadar)', count: 680, level: 'High' },
    { name: 'Endpoint Telemetry (EDR)', count: 420, level: 'Critical' },
    { name: 'Satellite Downlink Telemetry', count: 180, level: 'Medium' },
    { name: 'OSINT & Threat Feeds', count: 148, level: 'Low' }
  ];

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--cyan-bright)', textTransform: 'uppercase' }}>
          STRATEGIC SOC INTELLIGENCE
        </span>
        <h2 style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)', marginTop: 4 }}>
          Security Operations Analytics & Telemetry
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginTop: 4 }}>
          Longitudinal trend analysis, adversary technique prevalence, and detection-to-remediation efficiency metrics.
        </p>
      </div>

      {/* Analytics KPI Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16, marginBottom: 24 }}>
        <div className="soc-card">
          <span className="kpi-label">Mean Time to Detect (MTTD)</span>
          <div className="kpi-value" style={{ color: '#4ADE80' }}>4.2 min</div>
          <p style={{ fontSize: 11.5, color: 'var(--text-muted)', marginTop: 4 }}>-38% vs industry average</p>
        </div>
        <div className="soc-card">
          <span className="kpi-label">Mean Time to Remediate (MTTR)</span>
          <div className="kpi-value" style={{ color: 'var(--cyan-bright)' }}>14.8 min</div>
          <p style={{ fontSize: 11.5, color: 'var(--text-muted)', marginTop: 4 }}>Accelerated by automated playbooks</p>
        </div>
        <div className="soc-card">
          <span className="kpi-label">Noise Reduction Ratio</span>
          <div className="kpi-value" style={{ color: 'var(--blue)' }}>98.7%</div>
          <p style={{ fontSize: 11.5, color: 'var(--text-muted)', marginTop: 4 }}>1,428 alerts grouped to 18 chains</p>
        </div>
        <div className="soc-card">
          <span className="kpi-label">Correlation Accuracy</span>
          <div className="kpi-value" style={{ color: '#FACC15' }}>96.4%</div>
          <p style={{ fontSize: 11.5, color: 'var(--text-muted)', marginTop: 4 }}>MITRE technique alignment score</p>
        </div>
      </div>

      {/* Grid of 4 Deep Dive Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(460px, 1fr))', gap: 20 }}>
        {/* Risk Trend Last 7 Days */}
        <div className="soc-card">
          <div className="card-header">
            <div>
              <h3 className="card-title">
                <TrendingUp size={17} color="var(--cyan-bright)" />
                <span>Risk Trend (Last 7 Days)</span>
              </h3>
              <p className="card-subtitle">Daily average risk severity trajectory</p>
            </div>
            <span className="mono" style={{ fontSize: 11, color: 'var(--cyan-bright)' }}>Moving Avg</span>
          </div>
          <AreaTrendChart data={MOCK_TREND_DATA} height={190} />
        </div>

        {/* Volume by Telemetry Feed */}
        <div className="soc-card">
          <div className="card-header">
            <div>
              <h3 className="card-title">
                <Activity size={17} color="var(--blue)" />
                <span>Alert Intake by Security Feed Source</span>
              </h3>
              <p className="card-subtitle">Ingestion load distribution across heterogeneous sensors</p>
            </div>
          </div>
          <FrequencyBarChart items={sourceBreakdown} />
        </div>

        {/* Top Attacker Tactics */}
        <div className="soc-card">
          <div className="card-header">
            <div>
              <h3 className="card-title">
                <Target size={17} color="var(--critical)" />
                <span>Prevalent Attack Vectors & Methods</span>
              </h3>
              <p className="card-subtitle">Aggregated threat behaviors observed across all chains</p>
            </div>
          </div>
          <FrequencyBarChart items={attackTypes} />
        </div>

        {/* Threat Exposure Distribution */}
        <div className="soc-card">
          <div className="card-header">
            <div>
              <h3 className="card-title">
                <ShieldAlert size={17} color="var(--high)" />
                <span>Global Threat Exposure Breakdown</span>
              </h3>
              <p className="card-subtitle">Current organizational risk footprint by severity tier</p>
            </div>
          </div>
          <RiskDistributionChart distribution={MOCK_RISK_DISTRIBUTION} />
        </div>
      </div>
    </div>
  );
}
