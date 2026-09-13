import React, { useEffect, useMemo, useState } from 'react';
import {
  Network,
  Filter,
  Search,
  Globe,
  ArrowUpRight,
  Shield,
  Layers,
  ChevronRight,
  RefreshCw
} from 'lucide-react';
import { api, listFrom, severity } from '../services/api';
import { SeverityBadge, MitreChip } from '../components/Common';

export function AttackChainsPage({ onOpenChain, navigate }) {
  const [chains, setChains] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const loadChains = () => {
    setLoading(true);
    api.getChains()
      .then(res => {
        const list = listFrom(res, ['chains', 'results', 'data']);
        setChains(list);
      })
      .catch(() => setChains([]))
      .finally(() => setLoading(false));
  };

  useEffect(loadChains, []);

  const filteredChains = useMemo(() => {
    return chains.filter(c => {
      const matchFilter = filter === 'all' || severity(c.severity || c.risk_level) === filter;
      const q = searchQuery.toLowerCase();
      const matchSearch = !q ||
        (c.chain_id && c.chain_id.toLowerCase().includes(q)) ||
        (c.source_ip && c.source_ip.toLowerCase().includes(q)) ||
        (c.mitre_techniques && JSON.stringify(c.mitre_techniques).toLowerCase().includes(q));
      return matchFilter && matchSearch;
    });
  }, [chains, filter, searchQuery]);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
        <div>
          <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--cyan-bright)', textTransform: 'uppercase' }}>
            CORRELATION ENGINE OUTPUT
          </span>
          <h2 style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)', marginTop: 4 }}>
            Correlated Attack Chains
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginTop: 4 }}>
            Multi-stage attack campaigns reconstructed by clustering temporally adjacent alerts and shared network infrastructure.
          </p>
        </div>

        <button className="btn btn-secondary" onClick={loadChains} title="Re-correlate">
          <RefreshCw size={15} />
          <span>Sync Chains</span>
        </button>
      </div>

      {/* Toolbar: Search and Filter Tabs */}
      <div className="soc-card" style={{ padding: '14px 20px', marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
          {/* Search */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, background: '#0D1527', border: '1px solid #1E293B', borderRadius: 8, padding: '8px 14px', flex: '1 1 300px' }}>
            <Search size={16} color="#64748B" />
            <input
              type="text"
              placeholder="Search by Chain ID (e.g. AC001), Source IP, or MITRE ID (e.g. T1110)…"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#F8FAFC',
                fontSize: 13,
                outline: 'none',
                width: '100%'
              }}
            />
          </div>

          {/* Filter Pills */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-muted)', marginRight: 4 }}>
              <Filter size={14} />
              <span>Risk Filter:</span>
            </div>
            {['all', 'critical', 'high', 'medium', 'low'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                style={{
                  padding: '5px 12px',
                  borderRadius: 6,
                  border: '1px solid',
                  borderColor: filter === f ? 'var(--cyan)' : 'var(--card-border)',
                  background: filter === f ? 'rgba(6, 182, 212, 0.15)' : 'rgba(255, 255, 255, 0.02)',
                  color: filter === f ? '#fff' : 'var(--text-secondary)',
                  fontSize: 12,
                  fontWeight: 600,
                  textTransform: 'capitalize',
                  cursor: 'pointer',
                  transition: 'all 0.15s'
                }}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Table of Attack Chains */}
      <div className="soc-card">
        <div className="soc-table-wrap">
          <table className="soc-table">
            <thead>
              <tr>
                <th>Chain ID</th>
                <th>Source IP</th>
                <th>Destinations</th>
                <th>Events</th>
                <th>Risk Score</th>
                <th>Risk Level</th>
                <th>MITRE Techniques</th>
                <th>Status</th>
                <th>Created At</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredChains.length === 0 ? (
                <tr>
                  <td colSpan={10} style={{ textAlign: 'center', padding: '36px 0', color: 'var(--text-muted)' }}>
                    No attack chains match the filter or search criteria.
                  </td>
                </tr>
              ) : (
                filteredChains.map(c => {
                  const id = c.chain_id || 'AC001';
                  const score = c.risk_score || c.final_score || 85;
                  const sev = c.severity || 'Critical';
                  const techniques = c.mitre_techniques || [];

                  return (
                    <tr key={id} onClick={() => onOpenChain(id)}>
                      <td>
                        <code style={{ fontWeight: 800, color: 'var(--cyan-bright)', fontSize: 13.5 }}>{id}</code>
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <Globe size={13} color="#64748B" />
                          <code style={{ color: 'var(--text-primary)' }}>{c.source_ip || '198.51.100.24'}</code>
                        </div>
                      </td>
                      <td>
                        <span className="mono" style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                          {c.dest_ips?.slice(0, 2).join(', ') || '10.0.4.12'}
                          {c.dest_ips?.length > 2 ? ` (+${c.dest_ips.length - 2})` : ''}
                        </span>
                      </td>
                      <td>
                        <span className="mono" style={{ fontWeight: 600 }}>{c.alert_count || 8} events</span>
                      </td>
                      <td>
                        <span className="mono" style={{
                          fontWeight: 800,
                          fontSize: 13.5,
                          color: score >= 85 ? 'var(--critical)' : score >= 70 ? 'var(--high)' : 'var(--medium)'
                        }}>
                          {score}
                        </span>
                      </td>
                      <td>
                        <SeverityBadge value={sev} />
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                          {techniques.map((t, idx) => (
                            <MitreChip key={idx} id={t.technique_id || t.id} />
                          ))}
                        </div>
                      </td>
                      <td>
                        <span style={{
                          padding: '3px 8px',
                          borderRadius: 4,
                          fontSize: 11,
                          fontWeight: 600,
                          background: c.status === 'Active' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(255, 255, 255, 0.05)',
                          color: c.status === 'Active' ? '#FCA5A5' : '#94A3B8'
                        }}>
                          {c.status || 'Active'}
                        </span>
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
                          style={{ padding: '5px 12px', fontSize: 12 }}
                        >
                          <span>Details</span>
                          <ArrowUpRight size={13} />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
