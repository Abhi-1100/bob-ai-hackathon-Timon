import React, { useEffect, useState } from 'react';
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
  Clock,
  Upload,
  ChevronDown
} from 'lucide-react';
import { api, listFrom } from '../services/api';

export function RecommendationsPage({ onOpenChain, navigate }) {
  const [recommendations, setRecommendations] = useState([]);
  const [selectedChainId, setSelectedChainId] = useState('');
  const [activeTab, setActiveTab] = useState('immediate');
  const [completedTasks, setCompletedTasks] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getRecommendations()
      .then(res => {
        const list = listFrom(res, ['recommendations', 'results', 'data']);
        setRecommendations(list);
        if (list.length > 0 && !selectedChainId) {
          setSelectedChainId(list[0].chain_id);
        }
      })
      .catch(() => setRecommendations([]))
      .finally(() => setLoading(false));
  }, []);

  const chain = recommendations.find(c => c.chain_id === selectedChainId) || recommendations[0];

  const recs = chain ? {
    immediate_actions: chain.immediate_actions || [],
    containment_actions: chain.containment_actions || [],
    investigation_actions: chain.investigation_actions || [],
    prevention_actions: chain.prevention_actions || [],
    executive_summary: chain.executive_summary || ''
  } : {
    immediate_actions: [],
    containment_actions: [],
    investigation_actions: [],
    prevention_actions: [],
    executive_summary: ''
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
            Remediation steps synthesized across 4 containment tiers for active attack campaigns.
          </p>
        </div>

        {/* Campaign Selector Dropdown */}
        {recommendations.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 600 }}>Select Campaign:</span>
            <select
              value={selectedChainId}
              onChange={e => setSelectedChainId(e.target.value)}
              style={{
                background: 'var(--card)',
                color: 'var(--text-primary)',
                border: '1px solid var(--cyan)',
                padding: '8px 12px',
                borderRadius: 6,
                fontSize: 13,
                fontFamily: 'var(--font-mono)',
                fontWeight: 700,
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              {recommendations.map(r => (
                <option key={r.chain_id} value={r.chain_id}>
                  {r.chain_id} — {r.source_ip} (Risk {r.risk_score})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {recommendations.length === 0 && !loading ? (
        <div className="soc-card" style={{ padding: '60px 24px', textAlign: 'center' }}>
          <Lightbulb size={48} color="var(--text-muted)" style={{ opacity: 0.4, marginBottom: 16 }} />
          <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
            0 Recommendations Available
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: 13, maxWidth: 460, margin: '0 auto 20px' }}>
            Recommendations are generated dynamically for correlated attack chains. Ingest alert CSV logs to evaluate campaigns and produce actionable playbooks.
          </p>
          <button className="btn btn-primary" onClick={() => navigate('/upload')}>
            <Upload size={14} />
            <span>Upload Alerts CSV</span>
          </button>
        </div>
      ) : (
        <>
          {/* Executive Overview Banner */}
          {chain && (
            <div className="soc-card" style={{
              marginBottom: 24,
              borderLeft: `4px solid ${
                (chain.severity || '').toLowerCase() === 'critical' ? 'var(--critical)' :
                (chain.severity || '').toLowerCase() === 'high' ? 'var(--high)' : 'var(--medium)'
              }`,
              background: 'linear-gradient(145deg, rgba(6, 182, 212, 0.05), rgba(19, 26, 42, 0.9))'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <code style={{ fontSize: 15, fontWeight: 800, color: 'var(--cyan-bright)' }}>{chain.chain_id}</code>
                    <span className={`badge-severity ${(chain.severity || 'medium').toLowerCase()}`}>
                      {chain.severity || 'Medium'} Priority
                    </span>
                    <span className="mono" style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                      Origin: {chain.source_ip}
                    </span>
                  </div>
                  <p style={{ color: 'var(--text-secondary)', fontSize: 13.5, marginTop: 8, lineHeight: 1.5 }}>
                    {recs.executive_summary || `Automated playbook generated for incident ${chain.chain_id}.`}
                  </p>
                </div>
                {onOpenChain && (
                  <button
                    className="btn btn-secondary"
                    onClick={() => onOpenChain(chain.chain_id)}
                    style={{ fontSize: 12 }}
                  >
                    View Attack Graph
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Action Tabs */}
          <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '10px 18px',
                  borderRadius: 8,
                  border: '1px solid',
                  borderColor: activeTab === tab.id ? 'var(--cyan)' : 'var(--card-border)',
                  background: activeTab === tab.id ? 'rgba(6, 182, 212, 0.12)' : 'var(--card)',
                  color: activeTab === tab.id ? '#fff' : 'var(--text-secondary)',
                  fontWeight: 700,
                  fontSize: 13,
                  cursor: 'pointer',
                  transition: 'all 0.15s'
                }}
              >
                <span>{tab.label}</span>
                <span style={{
                  padding: '2px 7px',
                  borderRadius: 10,
                  background: tab.color,
                  color: '#fff',
                  fontSize: 11,
                  fontWeight: 800
                }}>
                  {tab.count}
                </span>
              </button>
            ))}
          </div>

          {/* Tasks checklist card */}
          <div className="soc-card">
            <div className="card-header">
              <h3 className="card-title">
                <CheckCircle2 size={18} color="var(--cyan-bright)" />
                <span>Action Checklist ({currentList.length} Tasks)</span>
              </h3>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                Click to mark actions completed during incident containment
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 12 }}>
              {currentList.length === 0 ? (
                <div style={{ padding: '24px 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
                  No actions defined for this tier.
                </div>
              ) : (
                currentList.map((action, idx) => {
                  const taskKey = `${chain.chain_id}-${activeTab}-${idx}`;
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
                      <div style={{ marginTop: 2, color: isDone ? '#4ADE80' : 'var(--text-muted)' }}>
                        {isDone ? <CheckSquare size={18} /> : <Square size={18} />}
                      </div>
                      <div style={{ flex: 1 }}>
                        <span style={{
                          fontSize: 13.5,
                          color: isDone ? 'var(--text-muted)' : 'var(--text-primary)',
                          textDecoration: isDone ? 'line-through' : 'none',
                          lineHeight: 1.5
                        }}>
                          {action}
                        </span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
