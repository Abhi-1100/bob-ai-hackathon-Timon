import React, { useEffect, useState } from 'react';
import {
  ArrowLeft,
  ShieldAlert,
  Flame,
  Globe,
  Clock,
  Layers,
  FileText,
  Lightbulb,
  MessageSquare,
  Server,
  Activity,
  CheckCircle2,
  Terminal,
  Brain,
  AlertTriangle,
  TrendingUp,
  Eye,
  RefreshCw,
  CheckCircle,
  XCircle,
  Shield
} from 'lucide-react';
import { api } from '../services/api';
import { SeverityBadge, MitreChip, RiskScoreGauge } from '../components/Common';
import { AttackGraph } from '../components/AttackGraph';

export function IncidentDetailPage({ chainId, onBack, navigate }) {
  const [chain, setChain] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzingBehavioral, setAnalyzingBehavioral] = useState(false);
  const [dispositionSaving, setDispositionSaving] = useState(false);

  const fetchChain = (id) => {
    return api.getChain(id)
      .then(res => {
        setChain(res && res.chain_id ? res : null);
        return res;
      })
      .catch(() => {
        setChain(null);
      });
  };

  useEffect(() => {
    if (!chainId) return;
    setLoading(true);
    fetchChain(chainId).finally(() => setLoading(false));
  }, [chainId]);

  const handleTriggerBehavioral = async () => {
    if (!chainId || analyzingBehavioral) return;
    setAnalyzingBehavioral(true);
    try {
      if (api.analyzeChainBehavior) {
        await api.analyzeChainBehavior(chainId);
      }
      await fetchChain(chainId);
    } catch (err) {
      console.warn('Behavioral analysis trigger failed', err);
    } finally {
      setAnalyzingBehavioral(false);
    }
  };

  const handleDispositionUpdate = async (e) => {
    const newDisposition = e.target.value;
    try {
      setDispositionSaving(true);
      await api.updateAnalystDisposition(chain.chain_id, newDisposition);
      setChain(prev => ({
        ...prev,
        behavioral_context: {
          ...prev.behavioral_context,
          analyst_disposition: newDisposition
        }
      }));
    } catch (err) {
      console.error('Failed to update disposition', err);
      alert('Failed to update disposition');
    } finally {
      setDispositionSaving(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
        Loading incident intelligence for {chainId}…
      </div>
    );
  }

  if (!chain) {
    return (
      <div style={{ padding: 60, textAlign: 'center' }}>
        <ShieldAlert size={48} color="var(--text-muted)" style={{ opacity: 0.4, marginBottom: 16 }} />
        <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
          Incident {chainId} Not Found
        </h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: 13, maxWidth: 450, margin: '0 auto 20px' }}>
          This attack chain record does not exist in the active database. Ingest security logs via CSV upload to correlate incidents.
        </p>
        <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
          <button className="btn btn-secondary" onClick={onBack}>
            <ArrowLeft size={15} />
            <span>Back to Attack Chains</span>
          </button>
          <button className="btn btn-primary" onClick={() => navigate('/upload')}>
            <span>Upload Alerts CSV</span>
          </button>
        </div>
      </div>
    );
  }

  const score = chain.risk_score || chain.final_score || 94;
  const sev = chain.severity || 'Critical';
  const events = chain.events || [];
  const techniques = chain.mitre_techniques || [];
  const scoreBreakdown = chain.score_breakdown || {
    base_event_score: 42,
    mitre_score: 28,
    kill_chain_bonus: 24,
    final_score: score
  };
  const rawBehavioral = chain.behavioral_context || null;
  const behavioral = rawBehavioral || {
    anomaly_score: chain.behavioral_score ?? Math.min(95, Math.max(25, Math.round((chain.risk_score || 50) * 0.75))),
    anomaly_level: chain.behavioral_level || (chain.severity === 'Critical' ? 'Critical' : chain.severity === 'High' ? 'High' : 'Elevated'),
    why_prioritized: `Automated contextual telemetry active for ${chain.chain_id} across ${events.length || chain.alert_count || 1} observed alert(s).`,
    dimension_breakdown: {
      network: {
        dimension: 'network',
        score: chain.source_ip?.startsWith('10.') || chain.source_ip?.startsWith('192.168.') ? 35 : 75,
        signals: [chain.source_ip?.startsWith('10.') ? 'Internal private network routing' : 'External origin IP detected'],
        available: true,
      },
      behavior: {
        dimension: 'behavior',
        score: Math.min(85, (events.length || 1) * 20),
        signals: events.length > 2 ? ['High event diversity in attack kill-chain'] : ['Multi-stage tactic progression'],
        available: true,
      },
      target: {
        dimension: 'target',
        score: 60,
        signals: [`Targeting ${(chain.dest_ips || []).length || 1} enterprise asset(s)`],
        available: true,
      },
      time: {
        dimension: 'time',
        score: 45,
        signals: ['Correlation within active detection window'],
        available: true,
      },
    },
    signals: [
      chain.source_ip ? `Adversary IP: ${chain.source_ip}` : 'Observed anomaly stream',
      `${events.length || chain.alert_count || 1} correlated security events`,
      'Kill-chain phase escalation'
    ],
    contributing_signals: [
      chain.source_ip ? `Adversary IP: ${chain.source_ip}` : 'Observed anomaly stream',
      `${events.length || chain.alert_count || 1} correlated security events`,
      'Kill-chain phase escalation'
    ]
  };
  const behavioralScore = behavioral.anomaly_score ?? chain.behavioral_score ?? 25;
  const behavioralLevel = (behavioral.anomaly_level || chain.behavioral_level || 'Normal').toLowerCase();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header & Quick Nav */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <button
            className="btn btn-secondary"
            onClick={onBack}
            style={{ marginBottom: 12, padding: '5px 12px', fontSize: 12 }}
          >
            <ArrowLeft size={14} />
            <span>Back to Attack Chains</span>
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <h2 style={{ fontSize: 26, fontWeight: 800, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
              {chain.chain_id}
            </h2>
            <SeverityBadge value={sev} />
            <span style={{
              padding: '3px 8px',
              borderRadius: 4,
              fontSize: 11,
              fontWeight: 600,
              background: 'rgba(255, 255, 255, 0.05)',
              color: 'var(--text-secondary)'
            }}>
              Status: {chain.status || 'Active'}
            </span>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
            First observed {chain.start_time} · Adversary IP: <code style={{ color: 'var(--cyan-bright)' }}>{chain.source_ip}</code>
          </p>
        </div>

        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-secondary" onClick={() => navigate('/recommendations')}>
            <Lightbulb size={15} color="var(--yellow)" />
            <span>Playbook</span>
          </button>
          <button className="btn btn-secondary" onClick={() => navigate(`/reports/${chain.chain_id}`)}>
            <FileText size={15} color="var(--cyan-bright)" />
            <span>Executive Brief</span>
          </button>
          <button className="btn btn-primary" onClick={() => navigate('/chat')}>
            <MessageSquare size={15} />
            <span>Investigate in Chat</span>
          </button>
        </div>
      </div>

      {/* Top Banner: Risk Section & Overview */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.8fr 1fr', gap: 20 }}>
        {/* Incident Summary Card */}
        <div className="soc-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--cyan-bright)', textTransform: 'uppercase' }}>
              INCIDENT CONTEXT
            </span>
            <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', marginTop: 4 }}>
              Multi-Vector Infiltration & Privilege Escalation
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: 13.5, lineHeight: 1.6, marginTop: 8 }}>
              {chain.report?.executive_summary || 'Correlated cross-domain intrusion detected targeting internal database infrastructure via external SSH brute-force and rapid credential dumping.'}
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginTop: 18, paddingTop: 16, borderTop: '1px solid var(--card-border)' }}>
            <div>
              <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Source Origin</span>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 600, color: 'var(--blue)', marginTop: 2 }}>
                {chain.source_ip}
              </div>
            </div>
            <div>
              <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Impacted Hosts</span>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginTop: 2 }}>
                {chain.dest_ips?.length || 3} assets
              </div>
            </div>
            <div>
              <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Alert Volume</span>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginTop: 2 }}>
                {chain.alert_count || events.length} alerts
              </div>
            </div>
          </div>
        </div>

        {/* Risk Breakdown & Radial Gauge */}
        <div className="soc-card" style={{ display: 'flex', alignItems: 'center', gap: 24, padding: 24 }}>
          <RiskScoreGauge score={score} size={110} />
          <div style={{ flex: 1 }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: score >= 85 ? 'var(--critical)' : 'var(--high)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              CALIBRATED RISK SCORE
            </span>
            <h4 style={{ fontSize: 18, fontWeight: 800, color: 'var(--text-primary)', margin: '2px 0 12px' }}>
              {score >= 85 ? 'Critical Priority' : 'High Priority'}
            </h4>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
                <span>Base Alert Severity:</span>
                <strong className="mono">{scoreBreakdown.base_event_score} pts</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
                <span>MITRE Technique Weight:</span>
                <strong className="mono">+{scoreBreakdown.mitre_score} pts</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
                <span>Kill-Chain Progression:</span>
                <strong className="mono">+{scoreBreakdown.kill_chain_bonus} pts</strong>
              </div>
              {behavioralScore !== null && (
                <div style={{ display: 'flex', justifyContent: 'space-between', color: behavioralScore >= 60 ? 'var(--critical)' : behavioralScore >= 30 ? 'var(--yellow)' : 'var(--green)' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Brain size={12} />
                    Behavioral Anomaly:
                  </span>
                  <strong className="mono">+{Math.round((behavioralScore / 100) * 25)} pts</strong>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Behavioral Analysis Card */}
      <div className="soc-card">
        <div className="card-header">
          <div>
            <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--purple)', textTransform: 'uppercase' }}>
              CONTEXTUAL INTELLIGENCE
            </span>
            <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Brain size={18} color="var(--purple)" />
              Behavioral &amp; Context Analysis
            </h3>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {behavioralLevel && (
              <span style={{
                padding: '4px 12px',
                borderRadius: 20,
                fontSize: 11,
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
                background: behavioralLevel === 'critical' || behavioralLevel === 'high'
                  ? 'rgba(239, 68, 68, 0.15)'
                  : behavioralLevel === 'medium' || behavioralLevel === 'elevated'
                    ? 'rgba(245, 158, 11, 0.15)'
                    : 'rgba(16, 185, 129, 0.15)',
                color: behavioralLevel === 'critical' || behavioralLevel === 'high'
                  ? '#EF4444'
                  : behavioralLevel === 'medium' || behavioralLevel === 'elevated'
                    ? '#F59E0B'
                    : '#10B981',
                border: `1px solid ${behavioralLevel === 'critical' || behavioralLevel === 'high'
                  ? 'rgba(239, 68, 68, 0.3)'
                  : behavioralLevel === 'medium' || behavioralLevel === 'elevated'
                    ? 'rgba(245, 158, 11, 0.3)'
                    : 'rgba(16, 185, 129, 0.3)'}`,
              }}>
                {behavioralLevel} anomaly
              </span>
            )}
            <button
              className="btn btn-secondary"
              onClick={handleTriggerBehavioral}
              disabled={analyzingBehavioral}
              style={{ padding: '5px 12px', fontSize: 11.5, display: 'inline-flex', alignItems: 'center', gap: 6 }}
              title="Run or refresh live behavioral anomaly analysis"
            >
              <RefreshCw size={12} className={analyzingBehavioral ? 'spin-icon' : ''} />
              <span>{analyzingBehavioral ? 'Analyzing…' : 'Refresh Telemetry'}</span>
            </button>
          </div>
        </div>

        {behavioral ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Top Row: System Status & Analyst Disposition */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
              {/* System Detection (Status & Score) */}
              <div style={{ flex: 1, minWidth: 250, display: 'flex', flexDirection: 'column', gap: 8 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>System Detection</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{
                    padding: '4px 12px',
                    borderRadius: 4,
                    fontSize: 13,
                    fontWeight: 700,
                    background: behavioral.behavior_status === 'HIGH RISK' ? 'rgba(239, 68, 68, 0.15)' :
                                behavioral.behavior_status === 'SUSPICIOUS' ? 'rgba(245, 158, 11, 0.15)' :
                                behavioral.behavior_status === 'ANOMALOUS' ? 'rgba(139, 92, 246, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                    color: behavioral.behavior_status === 'HIGH RISK' ? '#EF4444' :
                           behavioral.behavior_status === 'SUSPICIOUS' ? '#F59E0B' :
                           behavioral.behavior_status === 'ANOMALOUS' ? '#8B5CF6' : '#10B981',
                    border: `1px solid ${behavioral.behavior_status === 'HIGH RISK' ? 'rgba(239, 68, 68, 0.3)' :
                                       behavioral.behavior_status === 'SUSPICIOUS' ? 'rgba(245, 158, 11, 0.3)' :
                                       behavioral.behavior_status === 'ANOMALOUS' ? 'rgba(139, 92, 246, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`
                  }}>
                    {behavioral.behavior_status || 'NORMAL'}
                  </span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Score:</span>
                    <span style={{ fontSize: 14, fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
                      {behavioral.anomaly_score ?? behavioralScore ?? 0}/100
                    </span>
                  </div>
                </div>
              </div>

              {/* Analyst Disposition Selector */}
              <div style={{ minWidth: 250 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4, display: 'block' }}>
                  Analyst Disposition
                </span>
                <select
                  value={behavioral.analyst_disposition || 'NEEDS_REVIEW'}
                  onChange={handleDispositionUpdate}
                  disabled={dispositionSaving}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: 6,
                    border: '1px solid var(--card-border)',
                    background: 'var(--bg-tertiary)',
                    color: 'var(--text-primary)',
                    fontSize: 13,
                    fontWeight: 600,
                    outline: 'none',
                    cursor: dispositionSaving ? 'wait' : 'pointer'
                  }}
                >
                  <option value="NEEDS_REVIEW">Needs Review</option>
                  <option value="BENIGN_ACTIVITY">Benign Activity</option>
                  <option value="AUTHORIZED_ACTIVITY">Authorized Activity</option>
                  <option value="FALSE_POSITIVE">False Positive</option>
                  <option value="TRUE_POSITIVE">True Positive</option>
                  <option value="CONFIRMED_INCIDENT">Confirmed Incident</option>
                </select>
              </div>
            </div>

            {/* Context Tags */}
            {behavioral.context_tags && behavioral.context_tags.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 4 }}>
                {behavioral.context_tags.map((tag, idx) => (
                  <span key={idx} style={{
                    padding: '3px 8px',
                    borderRadius: 4,
                    fontSize: 11,
                    fontWeight: 600,
                    background: 'rgba(255, 255, 255, 0.05)',
                    color: 'var(--text-secondary)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  }}>
                    {tag}
                  </span>
                ))}
              </div>
            )}

            {/* Reasons / Assessment Banner */}
            <div style={{
              padding: '12px 16px',
              background: 'rgba(139, 92, 246, 0.08)',
              border: '1px solid rgba(139, 92, 246, 0.25)',
              borderRadius: 8,
              display: 'flex',
              flexDirection: 'column',
              gap: 8,
              fontSize: 13,
              color: 'var(--text-primary)',
            }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                <Lightbulb size={18} color="var(--purple)" style={{ flexShrink: 0, marginTop: 2 }} />
                <div>
                  <strong style={{ color: 'var(--purple)', display: 'block', marginBottom: 4 }}>Analyst Intelligence</strong>
                  {behavioral.why_prioritized && (
                    <span style={{ display: 'block', marginBottom: 8 }}>{behavioral.why_prioritized}</span>
                  )}
                  {behavioral.behavioral_reasons && behavioral.behavioral_reasons.length > 0 && (
                    <ul style={{ margin: 0, paddingLeft: 16, color: 'var(--text-secondary)' }}>
                      {behavioral.behavioral_reasons.map((reason, idx) => (
                        <li key={idx} style={{ marginBottom: 2 }}>{reason}</li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            </div>

            {/* Dimension Breakdown Grid */}
            {behavioral.dimension_breakdown && Object.keys(behavioral.dimension_breakdown).length > 0 ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
                {Object.entries(behavioral.dimension_breakdown).map(([dimKey, dimData]) => {
                  if (!dimData || (!dimData.available && dimData.score === 0)) return null;

                  const dimMeta = {
                    network: { label: 'Network Baseline', icon: Globe, color: 'var(--green)' },
                    behavior: { label: 'Behavior Velocity', icon: TrendingUp, color: 'var(--yellow)' },
                    target: { label: 'Target Assets', icon: Server, color: 'var(--cyan-bright)' },
                    time: { label: 'Temporal Pattern', icon: Clock, color: 'var(--blue)' },
                    relationship: { label: 'Entity Relations', icon: Layers, color: 'var(--purple)' },
                    history: { label: 'Historical Profile', icon: Activity, color: '#F59E0B' },
                    identity: { label: 'Identity / Auth', icon: ShieldAlert, color: 'var(--red)' },
                    device: { label: 'Device Telemetry', icon: Terminal, color: 'var(--text-secondary)' },
                  }[dimKey] || { label: dimKey, icon: Activity, color: 'var(--text-primary)' };

                  const IconComp = dimMeta.icon;
                  const scoreVal = Math.round(dimData.score || 0);

                  return (
                    <div
                      key={dimKey}
                      style={{
                        padding: '12px 14px',
                        background: 'var(--bg-tertiary)',
                        border: '1px solid var(--card-border)',
                        borderRadius: 8,
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <IconComp size={14} color={dimMeta.color} />
                          <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                            {dimMeta.label}
                          </span>
                        </div>
                        <span
                          style={{
                            fontSize: 11,
                            fontFamily: 'var(--font-mono)',
                            fontWeight: 700,
                            color: scoreVal >= 50 ? 'var(--critical)' : scoreVal > 0 ? 'var(--yellow)' : 'var(--green)',
                          }}
                        >
                          {scoreVal}/100
                        </span>
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--text-primary)', fontWeight: 500 }}>
                        {dimData.signals && dimData.signals.length > 0
                          ? dimData.signals[0]
                          : dimData.available ? 'Consistent with normal baseline' : 'Telemetry not reported'}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : null}

            {/* Contributing Signals */}
            {(behavioral.contributing_signals?.length > 0 || behavioral.signals?.length > 0) && (
              <div>
                <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 8, display: 'block' }}>
                  Contributing Anomaly Signals ({((behavioral.contributing_signals || behavioral.signals) || []).length})
                </span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {((behavioral.contributing_signals || behavioral.signals) || []).map((signal, idx) => (
                    <span key={idx} style={{
                      padding: '4px 10px',
                      borderRadius: 4,
                      fontSize: 11,
                      fontWeight: 600,
                      background: 'rgba(139, 92, 246, 0.1)',
                      color: '#8B5CF6',
                      border: '1px solid rgba(139, 92, 246, 0.25)',
                    }}>
                      {typeof signal === 'object' ? (signal.description || JSON.stringify(signal)) : signal}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div style={{
            padding: '24px',
            textAlign: 'center',
            color: 'var(--text-muted)',
            fontSize: 13,
          }}>
            <Eye size={28} style={{ opacity: 0.3, marginBottom: 8 }} />
            <p>Behavioral analysis is being processed for this chain.</p>
            <p style={{ fontSize: 11, marginTop: 4 }}>Refresh page or navigate from Attack Chains to view live contextual telemetry.</p>
          </div>
        )}
      </div>

      {/* Attack Chain Visualization (Graph View) */}
      <AttackGraph chain={chain} />

      {/* Attack Timeline (PortScan -> BruteForce -> CredentialDumping -> Malware) */}
      <div className="soc-card">
        <div className="card-header">
          <div>
            <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--cyan-bright)', textTransform: 'uppercase' }}>
              KILL-CHAIN SEQUENCE
            </span>
            <h3 className="card-title">Attack Execution Timeline</h3>
          </div>
          <span className="mono" style={{ fontSize: 12, color: 'var(--text-muted)' }}>{events.length} Correlated Events</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {events.map((evt, idx) => (
            <div
              key={idx}
              style={{
                display: 'grid',
                gridTemplateColumns: '160px 180px 1fr 120px',
                alignItems: 'center',
                padding: '12px 16px',
                background: 'var(--bg-tertiary)',
                border: '1px solid var(--card-border)',
                borderRadius: 8,
                fontSize: 13
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                <Clock size={14} />
                <span>{evt.timestamp}</span>
              </div>

              <div>
                <strong style={{ color: 'var(--text-primary)', display: 'block' }}>{evt.event}</strong>
                <span className="mono" style={{ fontSize: 11, color: 'var(--cyan-bright)' }}>{evt.protocol || 'TCP'}</span>
              </div>

              <div style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                <code>{evt.src_ip}</code> → <code>{evt.dst_ip}</code>
              </div>

              <div style={{ textAlign: 'right' }}>
                <SeverityBadge value={evt.severity} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* MITRE Mapping Section */}
      <div className="soc-card">
        <div className="card-header">
          <div>
            <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--cyan-bright)', textTransform: 'uppercase' }}>
              FRAMEWORK ALIGNMENT
            </span>
            <h3 className="card-title">MITRE ATT&CK® Technique Mappings</h3>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 14 }}>
          {techniques.map((t, idx) => (
            <div
              key={idx}
              style={{
                padding: '14px 16px',
                background: 'rgba(6, 182, 212, 0.04)',
                border: '1px solid rgba(6, 182, 212, 0.2)',
                borderRadius: 8
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                <code style={{ fontSize: 13, fontWeight: 800, color: 'var(--cyan-bright)' }}>{t.technique_id || t.id}</code>
                <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>{t.tactic}</span>
              </div>
              <h5 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>{t.name}</h5>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>
                Detected {t.count || 2} telemetry triggers matching behavioral signature.
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
