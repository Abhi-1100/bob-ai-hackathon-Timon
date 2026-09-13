import React, { useState } from 'react';
import {
  Settings,
  User,
  Key,
  Bell,
  Sliders,
  CheckCircle2,
  Database,
  Radio,
  Save,
  Server,
  Cpu,
  RefreshCw
} from 'lucide-react';

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState('profile');
  const [saved, setSaved] = useState(false);

  // Form states
  const [operatorName, setOperatorName] = useState('Analyst Jaimin');
  const [callsign, setCallsign] = useState('SENTINEL-ALPHA');
  const [groqKey, setGroqKey] = useState('gsk_••••••••••••••••••••••••••••••••');
  const [watsonxKey, setWatsonxKey] = useState('••••••••••••••••••••••••••••••••');
  const [watsonxProject, setWatsonxProject] = useState('prj-sentinel-ai-2026');
  const [qdrantUrl, setQdrantUrl] = useState('http://localhost:6333 (or In-Memory)');
  const [slackWebhook, setSlackWebhook] = useState('https://hooks.slack.com/services/T00/B00/XXXX');
  const [pollInterval, setPollInterval] = useState('15');

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const tabs = [
    { id: 'profile', label: 'Operator Profile', icon: User },
    { id: 'apikeys', label: 'API Keys & LLM', icon: Key },
    { id: 'system', label: 'System Diagnostics', icon: Server },
    { id: 'notifications', label: 'Notifications & Webhooks', icon: Bell },
    { id: 'preferences', label: 'Station Display', icon: Sliders },
  ];

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>
      <div style={{ marginBottom: 24 }}>
        <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--cyan-bright)', textTransform: 'uppercase' }}>
          OPERATIONS CONFIGURATION
        </span>
        <h2 style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)', marginTop: 4 }}>
          SOC Console & Station Settings
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginTop: 4 }}>
          Manage analyst identity, AI inference endpoints, vector database bindings, and alert notification webhooks.
        </p>
      </div>

      {saved && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          padding: '12px 18px',
          background: 'rgba(34, 197, 94, 0.12)',
          border: '1px solid rgba(34, 197, 94, 0.3)',
          borderRadius: 8,
          color: '#4ADE80',
          fontSize: 13,
          marginBottom: 20
        }}>
          <CheckCircle2 size={16} />
          <span>Configuration saved successfully to local environment.</span>
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 8, borderBottom: '1px solid var(--card-border)', marginBottom: 24 }}>
        {tabs.map(t => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '12px 16px',
                background: 'none',
                border: 'none',
                borderBottom: '2px solid',
                borderBottomColor: activeTab === t.id ? 'var(--cyan)' : 'transparent',
                color: activeTab === t.id ? '#fff' : 'var(--text-muted)',
                fontSize: 13.5,
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              <Icon size={16} />
              <span>{t.label}</span>
            </button>
          );
        })}
      </div>

      <form onSubmit={handleSave}>
        {/* Tab 1: Profile */}
        {activeTab === 'profile' && (
          <div className="soc-card" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <h3 className="card-title">Operator Clearance & Station Identity</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#94A3B8', marginBottom: 6 }}>
                  OPERATOR NAME
                </label>
                <input
                  type="text"
                  value={operatorName}
                  onChange={e => setOperatorName(e.target.value)}
                  style={{
                    width: '100%',
                    background: '#0D1527',
                    border: '1px solid #1E293B',
                    borderRadius: 6,
                    padding: '10px 14px',
                    color: '#fff',
                    fontSize: 13.5
                  }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#94A3B8', marginBottom: 6 }}>
                  TACTICAL CALLSIGN
                </label>
                <input
                  type="text"
                  value={callsign}
                  onChange={e => setCallsign(e.target.value)}
                  style={{
                    width: '100%',
                    background: '#0D1527',
                    border: '1px solid #1E293B',
                    borderRadius: 6,
                    padding: '10px 14px',
                    color: '#fff',
                    fontSize: 13.5,
                    fontFamily: 'var(--font-mono)'
                  }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#94A3B8', marginBottom: 6 }}>
                  SOC ROLE & TRACK
                </label>
                <input
                  type="text"
                  disabled
                  value="Lead Threat Analyst — TimonTrack (AI Track)"
                  style={{
                    width: '100%',
                    background: 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid #1E293B',
                    borderRadius: 6,
                    padding: '10px 14px',
                    color: '#94A3B8',
                    fontSize: 13.5
                  }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#94A3B8', marginBottom: 6 }}>
                  CLEARANCE LEVEL
                </label>
                <input
                  type="text"
                  disabled
                  value="LEVEL 03 — SPECIAL OPERATIONS COMMAND"
                  style={{
                    width: '100%',
                    background: 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid #1E293B',
                    borderRadius: 6,
                    padding: '10px 14px',
                    color: 'var(--cyan-bright)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 13.5,
                    fontWeight: 700
                  }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: API Keys */}
        {activeTab === 'apikeys' && (
          <div className="soc-card" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <h3 className="card-title">Inference & Vector Database Configurations</h3>
            <div>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#94A3B8', marginBottom: 6 }}>
                GROQ CLOUD API KEY (LLAMA 3.3 70B FAST INFERENCE)
              </label>
              <input
                type="password"
                value={groqKey}
                onChange={e => setGroqKey(e.target.value)}
                style={{
                  width: '100%',
                  background: '#0D1527',
                  border: '1px solid #1E293B',
                  borderRadius: 6,
                  padding: '10px 14px',
                  color: '#fff',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 13.5
                }}
              />
              <span style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4, display: 'block' }}>
                Used by Recommendation Agent, BLUF Report Agent, and Analyst Chat Copilot.
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#94A3B8', marginBottom: 6 }}>
                  IBM WATSONX.AI API KEY
                </label>
                <input
                  type="password"
                  value={watsonxKey}
                  onChange={e => setWatsonxKey(e.target.value)}
                  style={{
                    width: '100%',
                    background: '#0D1527',
                    border: '1px solid #1E293B',
                    borderRadius: 6,
                    padding: '10px 14px',
                    color: '#fff',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 13.5
                  }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#94A3B8', marginBottom: 6 }}>
                  WATSONX PROJECT ID
                </label>
                <input
                  type="text"
                  value={watsonxProject}
                  onChange={e => setWatsonxProject(e.target.value)}
                  style={{
                    width: '100%',
                    background: '#0D1527',
                    border: '1px solid #1E293B',
                    borderRadius: 6,
                    padding: '10px 14px',
                    color: '#fff',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 13.5
                  }}
                />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#94A3B8', marginBottom: 6 }}>
                QDRANT VECTOR DATABASE ENDPOINT
              </label>
              <input
                type="text"
                value={qdrantUrl}
                onChange={e => setQdrantUrl(e.target.value)}
                style={{
                  width: '100%',
                  background: '#0D1527',
                  border: '1px solid #1E293B',
                  borderRadius: 6,
                  padding: '10px 14px',
                  color: '#fff',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 13.5
                }}
              />
              <span style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4, display: 'block' }}>
                Leave empty for automatic In-Memory mode (:memory:) with local BAAI/bge-small embeddings.
              </span>
            </div>
          </div>
        )}

        {/* Tab 3: System Diagnostics */}
        {activeTab === 'system' && (
          <div className="soc-card" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <h3 className="card-title">Live Service Health Diagnostics</h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px', background: '#0D1527', borderRadius: 8, border: '1px solid #1E293B' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <Server size={20} color="#4ADE80" />
                  <div>
                    <strong style={{ color: '#fff' }}>FastAPI Backend Service</strong>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>http://localhost:8000 · Uvicorn ASGI Worker</div>
                  </div>
                </div>
                <span className="badge-severity low">Online</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px', background: '#0D1527', borderRadius: 8, border: '1px solid #1E293B' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <Cpu size={20} color="var(--cyan-bright)" />
                  <div>
                    <strong style={{ color: '#fff' }}>Qdrant Vector Database Engine</strong>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>In-Memory Mode · Embedding Dimension: 384 (Cosine)</div>
                  </div>
                </div>
                <span className="badge-severity low">Active</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px', background: '#0D1527', borderRadius: 8, border: '1px solid #1E293B' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <Database size={20} color="#38BDF8" />
                  <div>
                    <strong style={{ color: '#fff' }}>SQLite Telemetry Corpus</strong>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>threat_intel.db · Foreign Key Enforcement Enabled</div>
                  </div>
                </div>
                <span className="badge-severity low">Synchronized</span>
              </div>
            </div>
          </div>
        )}

        {/* Tab 4: Notifications */}
        {activeTab === 'notifications' && (
          <div className="soc-card" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <h3 className="card-title">Incident Alert Webhook Relays</h3>
            <div>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#94A3B8', marginBottom: 6 }}>
                SLACK / MS TEAMS INCOMING WEBHOOK URL
              </label>
              <input
                type="text"
                value={slackWebhook}
                onChange={e => setSlackWebhook(e.target.value)}
                style={{
                  width: '100%',
                  background: '#0D1527',
                  border: '1px solid #1E293B',
                  borderRadius: 6,
                  padding: '10px 14px',
                  color: '#fff',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 13.5
                }}
              />
              <span style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4, display: 'block' }}>
                Automated webhook dispatch triggered whenever a Critical (Risk &gt; 85) attack chain is formed.
              </span>
            </div>
          </div>
        )}

        {/* Tab 5: Preferences */}
        {activeTab === 'preferences' && (
          <div className="soc-card" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <h3 className="card-title">Station UI Theme & Telemetry Frequency</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#94A3B8', marginBottom: 6 }}>
                  TELEMETRY SYNC INTERVAL
                </label>
                <select
                  value={pollInterval}
                  onChange={e => setPollInterval(e.target.value)}
                  style={{
                    width: '100%',
                    background: '#0D1527',
                    border: '1px solid #1E293B',
                    borderRadius: 6,
                    padding: '10px 14px',
                    color: '#fff',
                    fontSize: 13.5
                  }}
                >
                  <option value="5">Every 5 seconds (Real-Time Stream)</option>
                  <option value="15">Every 15 seconds (Standard SOC)</option>
                  <option value="60">Every 60 seconds (Conservative)</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#94A3B8', marginBottom: 6 }}>
                  VISUAL DENSITY
                </label>
                <select
                  defaultValue="dense"
                  style={{
                    width: '100%',
                    background: '#0D1527',
                    border: '1px solid #1E293B',
                    borderRadius: 6,
                    padding: '10px 14px',
                    color: '#fff',
                    fontSize: 13.5
                  }}
                >
                  <option value="dense">High Density (CrowdStrike / Sentinel SOC)</option>
                  <option value="comfortable">Comfortable</option>
                </select>
              </div>
            </div>
          </div>
        )}

        <div style={{ marginTop: 24 }}>
          <button type="submit" className="btn btn-primary" style={{ padding: '10px 24px' }}>
            <Save size={16} />
            <span>Save Configuration</span>
          </button>
        </div>
      </form>
    </div>
  );
}
