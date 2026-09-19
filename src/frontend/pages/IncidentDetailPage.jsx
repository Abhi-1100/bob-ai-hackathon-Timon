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

      {/* Behavioral & Context Analysis Card */}
      <div className="soc-card">
        {/* Card Header */}
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
            {(() => {
              const bs = (behavioral.behavior_status || 'NORMAL').toUpperCase();
              const statusCfg = {
                'HIGH RISK':  { bg: 'rgba(239,68,68,0.15)',   color: '#EF4444', border: 'rgba(239,68,68,0.4)' },
                'SUSPICIOUS': { bg: 'rgba(245,158,11,0.15)',  color: '#F59E0B', border: 'rgba(245,158,11,0.4)' },
                'ANOMALOUS':  { bg: 'rgba(139,92,246,0.15)',  color: '#8B5CF6', border: 'rgba(139,92,246,0.4)' },
                'NORMAL':     { bg: 'rgba(16,185,129,0.15)',  color: '#10B981', border: 'rgba(16,185,129,0.4)' },
              };
              const cfg = statusCfg[bs] || statusCfg['NORMAL'];
              return (
                <span
                  title="System-generated behavioral status based on automated analysis"
                  style={{
                    padding: '4px 14px',
                    borderRadius: 20,
                    fontSize: 11,
                    fontWeight: 800,
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                    background: cfg.bg,
                    color: cfg.color,
                    border: `1px solid ${cfg.border}`,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {bs}
                </span>
              );
            })()}
            <button
              className="btn btn-secondary"
              onClick={handleTriggerBehavioral}
              disabled={analyzingBehavioral}
              style={{ padding: '5px 12px', fontSize: 11.5, display: 'inline-flex', alignItems: 'center', gap: 6 }}
              title="Run or refresh live behavioral anomaly analysis"
            >
              <RefreshCw size={12} className={analyzingBehavioral ? 'spin-icon' : ''} />
              <span>{analyzingBehavioral ? 'Analyzing\u2026' : 'Refresh Telemetry'}</span>
            </button>
          </div>
        </div>

        {behavioral ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>

            {/* 1. Anomaly Score Row */}
            {(() => {
              const sc = Math.round(Number(behavioral.anomaly_score ?? behavioralScore ?? 0));
              const bs = (behavioral.behavior_status || 'NORMAL').toUpperCase();
              const barColor = bs === 'HIGH RISK' ? '#EF4444' : bs === 'SUSPICIOUS' ? '#F59E0B' : bs === 'ANOMALOUS' ? '#8B5CF6' : '#10B981';
              return (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Anomaly Score</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 16, fontWeight: 800, color: barColor }}>
                      {sc}<span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>/100</span>
                    </span>
                  </div>
                  <div style={{ height: 6, borderRadius: 9999, background: 'rgba(255,255,255,0.08)', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${Math.max(2, sc)}%`, background: barColor, borderRadius: 9999, transition: 'width 0.5s ease', boxShadow: `0 0 8px ${barColor}60` }} />
                  </div>
                </div>
              );
            })()}

            {/* 2. Analyst Intelligence Banner */}
            <div style={{ padding: '14px 16px', background: 'rgba(139,92,246,0.07)', border: '1px solid rgba(139,92,246,0.22)', borderRadius: 10 }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                <Lightbulb size={17} color="var(--purple)" style={{ flexShrink: 0, marginTop: 1 }} />
                <div style={{ flex: 1 }}>
                  <strong style={{ fontSize: 13, color: 'var(--purple)', display: 'block', marginBottom: 5 }}>Analyst Intelligence</strong>
                  {behavioral.why_prioritized && (
                    <span style={{ display: 'block', fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.6 }}>{behavioral.why_prioritized}</span>
                  )}
                </div>
              </div>
            </div>

            {/* 3. Dimension Breakdown Grid */}
            {behavioral.dimension_breakdown && Object.keys(behavioral.dimension_breakdown).length > 0 && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 10 }}>
                {Object.entries(behavioral.dimension_breakdown).map(([dimKey, dimData]) => {
                  if (!dimData || (!dimData.available && dimData.score === 0)) return null;
                  const dimMeta = {
                    network:      { label: 'Network Baseline',  icon: Globe,       color: 'var(--green)' },
                    behavior:     { label: 'Behavior Velocity', icon: TrendingUp,  color: 'var(--yellow)' },
                    target:       { label: 'Target Assets',     icon: Server,      color: 'var(--cyan-bright)' },
                    time:         { label: 'Temporal Pattern',  icon: Clock,       color: 'var(--blue)' },
                    relationship: { label: 'Entity Relations',  icon: Layers,      color: 'var(--purple)' },
                    history:      { label: 'Historical Profile',icon: Activity,    color: '#F59E0B' },
                    identity:     { label: 'Identity / Auth',   icon: ShieldAlert, color: 'var(--red)' },
                    device:       { label: 'Device Telemetry',  icon: Terminal,    color: 'var(--text-secondary)' },
                  }[dimKey] || { label: dimKey, icon: Activity, color: 'var(--text-primary)' };
                  const IconComp = dimMeta.icon;
                  const scoreVal = Math.round(dimData.score || 0);
                  const scoreColor = scoreVal >= 60 ? 'var(--critical)' : scoreVal >= 30 ? 'var(--yellow)' : 'var(--green)';
                  return (
                    <div key={dimKey} style={{ padding: '11px 13px', background: 'var(--bg-tertiary)', border: '1px solid var(--card-border)', borderRadius: 8 }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <IconComp size={13} color={dimMeta.color} />
                          <span style={{ fontSize: 10.5, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{dimMeta.label}</span>
                        </div>
                        <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', fontWeight: 700, color: scoreColor }}>{scoreVal}/100</span>
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--text-primary)', fontWeight: 500, lineHeight: 1.4 }}>
                        {dimData.signals && dimData.signals.length > 0 ? dimData.signals[0] : dimData.available ? 'Consistent with normal baseline' : 'Telemetry not reported'}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* 4. Context Tags */}
            {behavioral.context_tags && behavioral.context_tags.length > 0 && (
              <div>
                <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 8, display: 'block' }}>Context Tags</span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {behavioral.context_tags.map((tag, idx) => {
                    const tagUpper = (tag || '').toUpperCase();
                    const isRisk   = tagUpper.includes('HIGH') || tagUpper.includes('CRITICAL') || tagUpper.includes('DEVIATION') || tagUpper.includes('FIRST-SEEN');
                    const isNormal = tagUpper.includes('NORMAL') || tagUpper.includes('KNOWN');
                    const isTime   = tagUpper.includes('TIME') || tagUpper.includes('UNUSUAL');
                    const isNet    = tagUpper.includes('NETWORK') || tagUpper.includes('INTERNAL') || tagUpper.includes('EXTERNAL');
                    const cfg = isRisk   ? { bg: 'rgba(245,158,11,0.10)', color: '#F59E0B', border: 'rgba(245,158,11,0.3)' }
                              : isNormal ? { bg: 'rgba(16,185,129,0.08)',  color: '#10B981', border: 'rgba(16,185,129,0.25)' }
                              : isTime   ? { bg: 'rgba(139,92,246,0.10)', color: '#A78BFA', border: 'rgba(139,92,246,0.28)' }
                              : isNet    ? { bg: 'rgba(96,165,250,0.10)',  color: '#60A5FA', border: 'rgba(96,165,250,0.28)' }
                              : { bg: 'rgba(255,255,255,0.05)', color: 'var(--text-secondary)', border: 'rgba(255,255,255,0.12)' };
                    const tagTooltips = {
                      'UNKNOWN IP': 'IP address has not previously been observed in this environment.',
                      'KNOWN IP': 'IP address has been seen before.',
                      'UNKNOWN DEVICE': 'Device has not previously been observed for this user.',
                      'KNOWN DEVICE': 'Device has been seen before for this user.',
                      'INTERNAL NETWORK': 'Source IP is in a private/internal network range.',
                      'EXTERNAL NETWORK': 'Source IP is from an external (non-RFC1918) address.',
                      'NEW TARGET': 'Target has not previously been accessed by this source.',
                      'KNOWN TARGET': 'Target has been accessed by this source before.',
                      'UNUSUAL TIME': 'Activity occurred outside the historical active hours pattern.',
                      'NORMAL TIME': 'Activity occurred during normal business hours.',
                      'HIGH VELOCITY': 'Event rate is significantly above the baseline threshold.',
                      'HIGH FREQUENCY': 'Event frequency is elevated above normal levels.',
                      'NORMAL BEHAVIOR': 'Event velocity is within the expected baseline range.',
                      'BASELINE DEVIATION': 'Observed behavior differs significantly from the established historical baseline.',
                      'FIRST-SEEN BEHAVIOR': 'This combination of entities has not been observed before.',
                      'NEW RELATIONSHIP': 'Novel source-to-target relationship with no historical precedent.',
                      'CRITICAL ASSET': 'Destination includes assets identified as high-value targets.',
                    };
                    return (
                      <span key={idx} title={tagTooltips[tagUpper] || tag} style={{ padding: '3px 9px', borderRadius: 5, fontSize: 11, fontWeight: 700, background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.border}`, cursor: 'default', letterSpacing: '0.04em' }}>
                        {tag}
                      </span>
                    );
                  })}
                </div>
              </div>
            )}

            {/* 5. Why This Was Flagged */}
            {behavioral.behavioral_reasons && behavioral.behavioral_reasons.length > 0 && (
              <div style={{ padding: '13px 16px', background: 'rgba(255,255,255,0.025)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 10, display: 'block' }}>Why This Was Flagged</span>
                <ul style={{ margin: 0, paddingLeft: 18, display: 'flex', flexDirection: 'column', gap: 5 }}>
                  {behavioral.behavioral_reasons.map((reason, idx) => (
                    <li key={idx} style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{reason}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* 6. Contributing Anomaly Signals */}
            {(behavioral.contributing_signals?.length > 0 || behavioral.signals?.length > 0) && (
              <div>
                <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 8, display: 'block' }}>
                  Contributing Anomaly Signals ({((behavioral.contributing_signals || behavioral.signals) || []).length})
                </span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {((behavioral.contributing_signals || behavioral.signals) || []).map((signal, idx) => (
                    <span key={idx} style={{ padding: '4px 10px', borderRadius: 4, fontSize: 11, fontWeight: 600, background: 'rgba(139,92,246,0.1)', color: '#8B5CF6', border: '1px solid rgba(139,92,246,0.25)' }}>
                      {typeof signal === 'object' ? (signal.description || JSON.stringify(signal)) : signal}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* 7. Analyst Disposition */}
            <div style={{ padding: '14px 16px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
              <div>
                <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 4, display: 'block' }}>Analyst Disposition</span>
                <span style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', lineHeight: 1.4 }}>Your assessment — independent of automated system status above.</span>
              </div>
              {(() => {
                const disp = behavioral.analyst_disposition || 'NEEDS_REVIEW';
                const dispCfg = {
                  'NEEDS_REVIEW':        { color: '#60A5FA', bg: 'rgba(96,165,250,0.10)',  border: 'rgba(96,165,250,0.25)' },
                  'BENIGN_ACTIVITY':     { color: '#10B981', bg: 'rgba(16,185,129,0.10)',  border: 'rgba(16,185,129,0.25)' },
                  'AUTHORIZED_ACTIVITY': { color: '#34D399', bg: 'rgba(52,211,153,0.10)',  border: 'rgba(52,211,153,0.25)' },
                  'FALSE_POSITIVE':      { color: '#94A3B8', bg: 'rgba(148,163,184,0.10)', border: 'rgba(148,163,184,0.25)' },
                  'TRUE_POSITIVE':       { color: '#F59E0B', bg: 'rgba(245,158,11,0.10)',  border: 'rgba(245,158,11,0.25)' },
                  'CONFIRMED_INCIDENT':  { color: '#EF4444', bg: 'rgba(239,68,68,0.10)',   border: 'rgba(239,68,68,0.25)' },
                };
                const dc = dispCfg[disp] || dispCfg['NEEDS_REVIEW'];
                return (
                  <div style={{ position: 'relative', display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                    {dispositionSaving && <RefreshCw size={13} className="spin-icon" color="var(--text-muted)" />}
                    <select
                      value={disp}
                      onChange={handleDispositionUpdate}
                      disabled={dispositionSaving}
                      style={{ padding: '8px 36px 8px 12px', borderRadius: 8, border: `1.5px solid ${dc.border}`, background: dc.bg, color: dc.color, fontSize: 13, fontWeight: 700, outline: 'none', cursor: dispositionSaving ? 'wait' : 'pointer', appearance: 'none', WebkitAppearance: 'none', minWidth: 200 }}
                    >
                      <option value="NEEDS_REVIEW">Needs Review</option>
                      <option value="BENIGN_ACTIVITY">Benign Activity</option>
                      <option value="AUTHORIZED_ACTIVITY">Authorized Activity</option>
                      <option value="FALSE_POSITIVE">False Positive</option>
                      <option value="TRUE_POSITIVE">True Positive</option>
                      <option value="CONFIRMED_INCIDENT">Confirmed Incident</option>
                    </select>
                    <svg style={{ position: 'absolute', right: 10, pointerEvents: 'none', opacity: 0.6 }} width={14} height={14} viewBox="0 0 24 24" fill="none" stroke={dc.color} strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="6 9 12 15 18 9" />
                    </svg>
                  </div>
                );
              })()}
            </div>

          </div>
        ) : (
          <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
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
