import React, { useMemo, useState } from 'react';
import { Flame, ShieldAlert, ArrowUpRight, Filter, ChevronRight, Clock, AlertTriangle } from 'lucide-react';
import { SeverityBadge, RiskScoreGauge } from '../components/Common';
import { MOCK_ATTACK_CHAINS } from '../services/mockData';

export function RiskPage({ onOpenChain }) {
  const [selectedTier, setSelectedTier] = useState('all');

  const sortedChains = useMemo(() => {
    const list = [...MOCK_ATTACK_CHAINS];
    list.sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0));
    return list;
  }, []);

  const filteredChains = useMemo(() => {
    if (selectedTier === 'all') return sortedChains;
    return sortedChains.filter(c => c.severity.toLowerCase() === selectedTier);
  }, [sortedChains, selectedTier]);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
        <div>
          <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--high)', textTransform: 'uppercase' }}>
            COMMAND PRIORITISATION
          </span>
          <h2 style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)', marginTop: 4 }}>
            Risk Prioritization Queue
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginTop: 4 }}>
            Strictly ranked by dynamic multi-factor risk score to focus limited defense resources on active zero-days and critical campaigns.
          </p>
        </div>

        {/* Filter Tabs */}
        <div style={{ display: 'flex', gap: 8 }}>
          {['all', 'critical', 'high', 'medium', 'low'].map(tier => (
            <button
              key={tier}
              onClick={() => setSelectedTier(tier)}
              style={{
                padding: '6px 14px',
                borderRadius: 6,
                border: '1px solid',
                borderColor: selectedTier === tier ? 'var(--cyan)' : 'var(--card-border)',
                background: selectedTier === tier ? 'rgba(6, 182, 212, 0.15)' : 'var(--card)',
                color: selectedTier === tier ? '#fff' : 'var(--text-secondary)',
                fontSize: 12,
                fontWeight: 600,
                textTransform: 'capitalize',
                cursor: 'pointer'
              }}
            >
              {tier}
            </button>
          ))}
        </div>
      </div>

      {/* Prioritization Queue Cards Grid */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {filteredChains.map((c, idx) => {
          const score = c.risk_score || 85;
          const isCritical = score >= 85;
          const isHigh = score >= 70 && score < 85;

          return (
            <div
              key={c.chain_id}
              className="soc-card"
              onClick={() => onOpenChain(c.chain_id)}
              style={{
                cursor: 'pointer',
                display: 'grid',
                gridTemplateColumns: '80px 180px 1fr 140px 100px 140px',
                alignItems: 'center',
                gap: 20,
                padding: '16px 24px',
                borderLeftWidth: 4,
                borderLeftColor: isCritical ? 'var(--critical)' : isHigh ? 'var(--high)' : 'var(--medium)'
              }}
            >
              {/* Priority Rank */}
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>RANK</span>
                <span className="mono" style={{ fontSize: 22, fontWeight: 800, color: isCritical ? 'var(--critical)' : '#fff' }}>
                  #{String(idx + 1).padStart(2, '0')}
                </span>
              </div>

              {/* Chain ID & Source */}
              <div>
                <span className="mono" style={{ fontSize: 15, fontWeight: 800, color: 'var(--cyan-bright)' }}>{c.chain_id}</span>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                  From: <code style={{ color: 'var(--text-secondary)' }}>{c.source_ip}</code>
                </div>
              </div>

              {/* Threat Context & MITRE */}
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: '#F8FAFC' }}>
                  {c.report?.executive_summary || 'Correlated intrusion with active lateral progression'}
                </div>
                <div style={{ display: 'flex', gap: 6, marginTop: 6, flexWrap: 'wrap' }}>
                  {(c.mitre_techniques || []).slice(0, 3).map((t, tIdx) => (
                    <span
                      key={tIdx}
                      style={{
                        padding: '1px 6px',
                        background: 'rgba(255, 255, 255, 0.04)',
                        border: '1px solid var(--card-border)',
                        borderRadius: 4,
                        fontSize: 10.5,
                        fontFamily: 'var(--font-mono)',
                        color: 'var(--text-secondary)'
                      }}
                    >
                      {t.technique_id || t.id}
                    </span>
                  ))}
                </div>
              </div>

              {/* SLA & Time Window */}
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>RESPONSE SLA</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 2, fontSize: 12, fontWeight: 600, color: isCritical ? '#F87171' : '#FDBA74' }}>
                  <Clock size={13} />
                  <span>{isCritical ? '< 15 mins' : '< 1 hour'}</span>
                </div>
              </div>

              {/* Risk Score */}
              <div style={{ textAlign: 'center' }}>
                <span style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>SCORE</span>
                <div className="mono" style={{ fontSize: 18, fontWeight: 800, color: isCritical ? 'var(--critical)' : isHigh ? 'var(--high)' : 'var(--medium)' }}>
                  {score}
                </div>
              </div>

              {/* Action Button */}
              <div style={{ textAlign: 'right' }}>
                <button
                  className="btn btn-secondary"
                  onClick={(e) => {
                    e.stopPropagation();
                    onOpenChain(c.chain_id);
                  }}
                  style={{ padding: '6px 14px', fontSize: 12 }}
                >
                  <span>Triage Now</span>
                  <ArrowUpRight size={13} />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
