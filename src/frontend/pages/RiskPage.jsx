import React, { useEffect, useMemo, useState } from 'react';
import { Flame, ShieldAlert, ArrowUpRight, Filter, ChevronRight, Clock, AlertTriangle, Upload } from 'lucide-react';
import { SeverityBadge, RiskScoreGauge } from '../components/Common';
import { api, listFrom } from '../services/api';

export function RiskPage({ onOpenChain, navigate }) {
  const [chains, setChains] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTier, setSelectedTier] = useState('all');

  useEffect(() => {
    setLoading(true);
    api.getChains()
      .then(res => {
        const list = listFrom(res, ['chains', 'results', 'data']);
        setChains(list);
      })
      .catch(() => setChains([]))
      .finally(() => setLoading(false));
  }, []);

  const sortedChains = useMemo(() => {
    const list = [...chains];
    list.sort((a, b) => (b.risk_score || b.final_score || 0) - (a.risk_score || a.final_score || 0));
    return list;
  }, [chains]);

  const filteredChains = useMemo(() => {
    if (selectedTier === 'all') return sortedChains;
    return sortedChains.filter(c => (c.severity || c.risk_level || '').toLowerCase() === selectedTier);
  }, [sortedChains, selectedTier]);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
        <div>
          <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--high)', textTransform: 'uppercase' }}>
            COMMAND PRIORITISATION
          </span>
          <h2 style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)', marginTop: 4 }}>
            Risk Prioritization Queue ({sortedChains.length} Incidents)
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
                borderColor: selectedTier === tier ? 'var(--blue)' : 'var(--card-border)',
                background: selectedTier === tier ? 'var(--blue)' : 'var(--card)',
                color: selectedTier === tier ? '#FFFFFF' : 'var(--text-secondary)',
                fontSize: 12,
                fontWeight: 600,
                textTransform: 'capitalize',
                cursor: 'pointer',
                transition: 'all 0.15s'
              }}
            >
              {tier}
            </button>
          ))}
        </div>
      </div>

      {/* Prioritization Queue Cards Grid */}
      {sortedChains.length === 0 && !loading ? (
        <div className="soc-card" style={{ padding: '60px 24px', textAlign: 'center' }}>
          <ShieldAlert size={48} color="var(--text-muted)" style={{ opacity: 0.4, marginBottom: 16 }} />
          <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
            0 Attack Chains Evaluated
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: 13, maxWidth: 460, margin: '0 auto 20px' }}>
            The risk scoring engine ranks correlated attack chains dynamically from ingested alert logs. Upload a CSV file to evaluate risk.
          </p>
          <button className="btn btn-primary" onClick={() => navigate('/upload')}>
            <Upload size={14} />
            <span>Upload Alerts CSV</span>
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {filteredChains.map((c, rank) => {
            const id = c.chain_id;
            const score = c.risk_score || c.final_score || 0;
            const sev = c.severity || 'Medium';

            return (
              <div
                key={id}
                className="soc-card hover-glow"
                onClick={() => onOpenChain(id)}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '80px 1.4fr 1.2fr 180px 100px',
                  alignItems: 'center',
                  gap: 20,
                  cursor: 'pointer',
                  borderLeft: `4px solid ${
                    sev.toLowerCase() === 'critical' ? 'var(--critical)' :
                    sev.toLowerCase() === 'high' ? 'var(--high)' : 'var(--medium)'
                  }`
                }}
              >
                {/* Rank & Gauge */}
                <div style={{ textAlign: 'center' }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)' }}>RANK #{rank + 1}</span>
                  <div style={{ marginTop: 4 }}>
                    <RiskScoreGauge score={score} size={48} />
                  </div>
                </div>

                {/* Campaign Identifiers */}
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <code style={{ fontSize: 14, fontWeight: 800, color: 'var(--cyan-bright)' }}>{id}</code>
                    <SeverityBadge value={sev} />
                  </div>
                  <div style={{ fontSize: 13, color: 'var(--text-primary)', marginTop: 4, fontWeight: 600 }}>
                    Attacker IP: <code>{c.source_ip}</code>
                  </div>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2, margin: 0 }}>
                    Targeting {c.dest_ips?.join(', ') || 'Internal subnet'} ({c.alert_count || 1} events)
                  </p>
                </div>

                {/* Event sequence breakdown */}
                <div>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                    Observed Event Progression
                  </span>
                  <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginTop: 4 }}>
                    {(c.events || []).slice(0, 3).map((ev, i) => (
                      <span key={i} style={{
                        padding: '3px 8px',
                        background: 'var(--bg-tertiary)',
                        border: '1px solid var(--card-border)',
                        borderRadius: 4,
                        fontSize: 11,
                        color: 'var(--text-secondary)',
                        fontWeight: 500
                      }}>
                        {typeof ev === 'object' ? ev.event : ev}
                      </span>
                    ))}
                    {(c.events?.length || 0) > 3 && (
                      <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                        +{c.events.length - 3} more
                      </span>
                    )}
                  </div>
                </div>

                {/* Observed time */}
                <div>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Clock size={12} /> Observed
                  </span>
                  <span className="mono" style={{ fontSize: 12, color: 'var(--text-secondary)', display: 'block', marginTop: 2 }}>
                    {c.created_at || 'Just now'}
                  </span>
                </div>

                {/* Action button */}
                <div style={{ textAlign: 'right' }}>
                  <button
                    className="btn btn-secondary"
                    onClick={(e) => {
                      e.stopPropagation();
                      onOpenChain(id);
                    }}
                    style={{ padding: '6px 12px', fontSize: 12 }}
                  >
                    <span>Investigate</span>
                    <ArrowUpRight size={13} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
