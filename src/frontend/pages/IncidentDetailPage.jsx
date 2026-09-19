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
  Eye
} from 'lucide-react';
import { api } from '../services/api';
import { SeverityBadge, MitreChip, RiskScoreGauge } from '../components/Common';
import { AttackGraph } from '../components/AttackGraph';

export function IncidentDetailPage({ chainId, onBack, navigate }) {
  const [chain, setChain] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!chainId) return;
    setLoading(true);
    api.getChain(chainId)
      .then(res => {
        setChain(res && res.chain_id ? res : null);
      })
      .catch(() => {
        setChain(null);
      })
      .finally(() => setLoading(false));
  }, [chainId]);

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
  const behavioral = chain.behavioral_context || null;
  const behavioralScore = chain.behavioral_score ?? null;
  const behavioralLevel = chain.behavioral_level || null;

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
        </div>

        {behavioral ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Anomaly Score Bar */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <span style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 600 }}>Anomaly Score</span>
                  <span style={{ fontSize: 14, fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
                    {behavioral.anomaly_score ?? behavioralScore ?? 0}/100
                  </span>
                </div>
                <div style={{
                  height: 8,
                  borderRadius: 4,
                  background: 'var(--bg-tertiary)',
                  overflow: 'hidden',
                }}>
                  <div style={{
                    height: '100%',
                    width: `${behavioral.anomaly_score ?? behavioralScore ?? 0}%`,
                    borderRadius: 4,
                    background: (behavioral.anomaly_score ?? behavioralScore ?? 0) >= 60
                      ? 'linear-gradient(90deg, #EF4444, #DC2626)'
                      : (behavioral.anomaly_score ?? behavioralScore ?? 0) >= 30
                        ? 'linear-gradient(90deg, #F59E0B, #D97706)'
                        : 'linear-gradient(90deg, #10B981, #059669)',
                    transition: 'width 0.6s ease',
                  }} />
                </div>
              </div>
            </div>

            {/* Analyst Assessment Banner */}
            {behavioral.why_prioritized && (
              <div style={{
                padding: '12px 16px',
                background: 'rgba(139, 92, 246, 0.08)',
                border: '1px solid rgba(139, 92, 246, 0.25)',
                borderRadius: 8,
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                fontSize: 13,
                color: 'var(--text-primary)',
              }}>
                <Lightbulb size={18} color="var(--purple)" style={{ flexShrink: 0 }} />
                <div>
                  <strong style={{ color: 'var(--purple)' }}>Analyst Intelligence: </strong>
                  <span>{behavioral.why_prioritized}</span>
                </div>
              </div>
            )}

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
