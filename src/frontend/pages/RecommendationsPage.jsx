import React, { useState } from 'react';
import {
  Lightbulb,
  Shield,
  Zap,
  Search,
  Lock,
  CheckSquare,
  Square,
  Sparkles,
  CheckCircle2,
  Clock
} from 'lucide-react';
import { MOCK_ATTACK_CHAINS } from '../services/mockData';

export function RecommendationsPage({ onOpenChain }) {
  const [selectedChainId, setSelectedChainId] = useState('AC001');
  const [activeTab, setActiveTab] = useState('immediate');
  const [completedTasks, setCompletedTasks] = useState({});

  const chain = MOCK_ATTACK_CHAINS.find(c => c.chain_id === selectedChainId) || MOCK_ATTACK_CHAINS[0];
  const recs = chain.recommendations || {
    immediate_actions: ['Immediately isolate compromised host 10.0.4.12.', 'Block attacker IP on perimeter firewalls.', 'Rotate root & service account passwords.'],
    containment_actions: ['Segment internal subnet 10.0.4.0/24 from financial databases.', 'Terminate unauthorized SSH sessions.'],
    investigation_actions: ['Extract live volatile memory dump from 10.0.4.12.', 'Query SIEM logs for anomalous outbound egress.'],
    prevention_actions: ['Enforce FIDO2 hardware MFA on all external jump hosts.', 'Deploy endpoint LSASS behavioral blocking.']
  };

  const tabs = [
    { id: 'immediate', label: 'Immediate Actions', count: recs.immediate_actions.length, color: 'var(--critical)' },
    { id: 'containment', label: 'Containment Actions', count: recs.containment_actions.length, color: 'var(--high)' },
    { id: 'investigation', label: 'Investigation Actions', count: recs.investigation_actions.length, color: 'var(--cyan)' },
    { id: 'prevention', label: 'Prevention Actions', count: recs.prevention_actions.length, color: 'var(--low)' }
  ];

  const getListForTab = () => {
    if (activeTab === 'immediate') return recs.immediate_actions;
    if (activeTab === 'containment') return recs.containment_actions;
    if (activeTab === 'investigation') return recs.investigation_actions;
    return recs.prevention_actions;
  };

  const toggleTask = (taskKey) => {
    setCompletedTasks(prev => ({
      ...prev,
      [taskKey]: !prev[taskKey]
    }));
  };

  const currentList = getListForTab();

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
        <div>
          <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--cyan-bright)', textTransform: 'uppercase' }}>
            AI-GENERATED RESPONSE PLAYBOOKS
          </span>
          <h2 style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)', marginTop: 4 }}>
            Tactical Action Recommendations
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginTop: 4 }}>
            Remediation steps synthesized by Llama 3.3 70B based on observed kill-chain stages, MITRE techniques, and asset criticality.
          </p>
        </div>

        {/* Chain Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Target Chain:</span>
          <select
            value={selectedChainId}
            onChange={e => setSelectedChainId(e.target.value)}
            style={{
              background: '#131A2A',
              border: '1px solid var(--card-border)',
              borderRadius: 6,
              padding: '6px 12px',
              color: 'var(--cyan-bright)',
              fontFamily: 'var(--font-mono)',
              fontSize: 13,
              fontWeight: 700,
              outline: 'none'
            }}
          >
            {MOCK_ATTACK_CHAINS.map(c => (
              <option key={c.chain_id} value={c.chain_id}>
                {c.chain_id} — {c.severity} ({c.risk_score}/100)
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Playbook Header Card */}
      <div className="soc-card" style={{
        background: 'linear-gradient(145deg, rgba(6, 182, 212, 0.05), rgba(19, 26, 42, 0.95))',
        marginBottom: 20
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="badge-severity critical">Active Incident</span>
              <span className="mono" style={{ fontSize: 13, color: 'var(--text-muted)' }}>Adversary: {chain.source_ip}</span>
            </div>
            <h3 style={{ fontSize: 18, fontWeight: 700, color: '#fff', marginTop: 6 }}>
              Incident Response Plan for {chain.chain_id}
            </h3>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
              Execute containment immediately to prevent lateral credential movement to database servers.
            </p>
          </div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            padding: '6px 12px',
            background: 'rgba(255, 255, 255, 0.03)',
            borderRadius: 6,
            border: '1px solid var(--card-border)'
          }}>
            <Sparkles size={15} color="var(--cyan-bright)" />
            <span style={{ fontSize: 11.5, color: '#94A3B8' }}>Inference: <strong>Llama 3.3 70B</strong></span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 10, borderBottom: '1px solid var(--card-border)', marginBottom: 20 }}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '12px 18px',
              border: 'none',
              background: 'none',
              borderBottom: '2px solid',
              borderBottomColor: activeTab === tab.id ? 'var(--cyan)' : 'transparent',
              color: activeTab === tab.id ? '#fff' : 'var(--text-muted)',
              fontSize: 13.5,
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.15s'
            }}
          >
            <span>{tab.label}</span>
            <span style={{
              fontSize: 10.5,
              fontWeight: 700,
              padding: '2px 7px',
              borderRadius: 9999,
              background: 'rgba(255, 255, 255, 0.05)',
              color: tab.color
            }}>
              {tab.count}
            </span>
          </button>
        ))}
      </div>

      {/* Task Checklist Panel */}
      <div className="soc-card">
        <div className="card-header">
          <h4 className="card-title">
            <CheckCircle2 size={16} color="var(--cyan-bright)" />
            <span>Remediation Action Checklist</span>
          </h4>
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            Click item to mark completed
          </span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {currentList.map((item, idx) => {
            const taskKey = `${selectedChainId}-${activeTab}-${idx}`;
            const isDone = Boolean(completedTasks[taskKey]);

            return (
              <div
                key={idx}
                onClick={() => toggleTask(taskKey)}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 14,
                  padding: '14px 18px',
                  borderRadius: 8,
                  background: isDone ? 'rgba(34, 197, 94, 0.05)' : 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid',
                  borderColor: isDone ? 'rgba(34, 197, 94, 0.3)' : 'var(--card-border)',
                  cursor: 'pointer',
                  transition: 'all 0.15s'
                }}
              >
                <div style={{ color: isDone ? '#4ADE80' : '#64748B', marginTop: 2 }}>
                  {isDone ? <CheckSquare size={18} /> : <Square size={18} />}
                </div>

                <div style={{ flex: 1 }}>
                  <span style={{
                    fontSize: 13.5,
                    color: isDone ? '#94A3B8' : '#F8FAFC',
                    textDecoration: isDone ? 'line-through' : 'none',
                    lineHeight: 1.5,
                    display: 'block'
                  }}>
                    {item}
                  </span>
                  <div style={{ display: 'flex', gap: 12, marginTop: 4, fontSize: 11, color: 'var(--text-muted)' }}>
                    <span>Target: <strong>{chain.dest_ips?.[0] || '10.0.4.12'}</strong></span>
                    <span>Status: <strong style={{ color: isDone ? '#4ADE80' : '#FBBF24' }}>{isDone ? 'Completed' : 'Pending Action'}</strong></span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
