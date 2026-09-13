/**
 * Sentinel Forge — 0 Static Data / Dynamic State Defaults
 * All operational data comes dynamically from user uploaded CSVs and backend correlation.
 * These structures serve strictly as typed empty-state initializers.
 */

export const DEFAULT_KPIS = {
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

export const MOCK_KPIS = DEFAULT_KPIS;
export const MOCK_ATTACK_CHAINS = [];
export const MOCK_TREND_DATA = [];
export const MOCK_MITRE_FREQUENCY = [];
export const MOCK_RISK_DISTRIBUTION = [
  { name: 'Critical', value: 0, color: '#EF4444' },
  { name: 'High', value: 0, color: '#F97316' },
  { name: 'Medium', value: 0, color: '#FBBF24' },
  { name: 'Low', value: 0, color: '#10B981' },
];
export const MOCK_HOURLY_VOLUME = [];
export const MOCK_MITRE_MATRIX = [];
export const MOCK_CHAT_SESSIONS = [];
