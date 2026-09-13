import React, { useState } from 'react';
import {
  Settings,
  Shield,
  Key,
  Database,
  Bell,
  Sliders,
  CheckCircle2,
  Save,
  Server,
  Cpu
} from 'lucide-react';

export function SettingsPage() {
  const [operatorName, setOperatorName] = useState('Analyst Jaimin');
  const [callsign, setCallsign] = useState('VANGUARD-01');
  const [groqKey, setGroqKey] = useState('gsk_••••••••••••••••••••••••••••••••••••••••••••');
  const [watsonxKey, setWatsonxKey] = useState('••••••••••••••••••••••••••••••••');
  const [watsonxProject, setWatsonxProject] = useState('proj-sentinel-ai-prod');
  const [qdrantUrl, setQdrantUrl] = useState(':memory: (In-Memory Vector DB)');
  const [slackWebhook, setSlackWebhook] = useState('https://hooks.slack.com/services/T00/B00/XXXX');
  const [pollInterval, setPollInterval] = useState('15');
  const [activeTab, setActiveTab] = useState('profile');
  const [saved, setSaved] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const tabs = [
    { id: 'profile', label: 'Operator Station', icon: Shield },
    { id: 'apikeys', label: 'AI & Inference Engines', icon: Key },
    { id: 'system', label: 'System Diagnostics', icon: Database },
    { id: 'notifications', label: 'Alert Webhooks', icon: Bell },
    { id: 'preferences', label: 'SOC Station Preferences', icon: Sliders },
  ];

  const inputStyle = {
    width: '100%',
    background: 'var(--input-bg)',
    border: '1px solid var(--input-border)',
    borderRadius: 6,
    padding: '10px 14px',
    color: 'var(--input-text)',
    fontSize: 13.5
  };

  const disabledInputStyle = {
    width: '100%',
    background: 'var(--bg-tertiary)',
    border: '1px solid var(--card-border)',
    borderRadius: 6,
    padding: '10px 14px',
    color: 'var(--text-muted)',
    fontSize: 13.5
  };

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--blue)', textTransform: 'uppercase' }}>
            OPERATIONAL ENVIRONMENT
          </span>
          <h2 style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)', marginTop: 4 }}>
            System & Station Configuration
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginTop: 4 }}>
            Manage SOC operator credentials, vector storage parameters, and LLM inference engine endpoints.
          </p>
        </div>

        {saved && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '8px 16px',
            background: 'var(--low-bg)',
            border: '1px solid var(--low-border)',
            borderRadius: 8,
            color: 'var(--low-text)',
            fontSize: 13,
            fontWeight: 600
          }}>
            <CheckCircle2 size={16} />
            <span>Station configurations persisted</span>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid var(--card-border)', marginBottom: 24 }}>
        {tabs.map(t => {
          const Icon = t.icon;
          const isActive = activeTab === t.id;
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
                borderBottomColor: isActive ? 'var(--blue)' : 'transparent',
                color: isActive ? 'var(--blue)' : 'var(--text-secondary)',
                fontSize: 13.5,
                fontWeight: isActive ? 700 : 500,
                cursor: 'pointer',
                transition: 'all 0.15s'
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
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                  OPERATOR NAME
                </label>
                <input
                  type="text"
                  value={operatorName}
                  onChange={e => setOperatorName(e.target.value)}
                  style={inputStyle}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                  TACTICAL CALLSIGN
                </label>
                <input
                  type="text"
                  value={callsign}
                  onChange={e => setCallsign(e.target.value)}
                  style={{ ...inputStyle, fontFamily: 'var(--font-mono)' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                  SOC ROLE & TRACK
                </label>
                <input
                  type="text"
                  disabled
                  value="Lead Threat Analyst — TimonTrack (AI Track)"
                  style={disabledInputStyle}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                  CLEARANCE LEVEL
                </label>
                <input
                  type="text"
                  disabled
                  value="LEVEL 03 — SPECIAL OPERATIONS COMMAND"
                  style={{
                    ...disabledInputStyle,
                    color: 'var(--blue)',
                    fontFamily: 'var(--font-mono)',
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
              <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                GROQ CLOUD API KEY (LLAMA 3.3 70B FAST INFERENCE)
              </label>
              <input
                type="password"
                value={groqKey}
                onChange={e => setGroqKey(e.target.value)}
                style={{ ...inputStyle, fontFamily: 'var(--font-mono)' }}
              />
              <span style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4, display: 'block' }}>
                Used by Recommendation Agent, BLUF Report Agent, and Analyst Chat Copilot.
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                  IBM WATSONX.AI API KEY
                </label>
                <input
                  type="password"
                  value={watsonxKey}
                  onChange={e => setWatsonxKey(e.target.value)}
                  style={{ ...inputStyle, fontFamily: 'var(--font-mono)' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                  WATSONX PROJECT ID
                </label>
                <input
                  type="text"
                  value={watsonxProject}
                  onChange={e => setWatsonxProject(e.target.value)}
                  style={{ ...inputStyle, fontFamily: 'var(--font-mono)' }}
                />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                QDRANT VECTOR DATABASE ENDPOINT
              </label>
              <input
                type="text"
                value={qdrantUrl}
                onChange={e => setQdrantUrl(e.target.value)}
                style={{ ...inputStyle, fontFamily: 'var(--font-mono)' }}
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
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px', background: 'var(--bg-tertiary)', borderRadius: 8, border: '1px solid var(--card-border)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <Server size={20} color="var(--low)" />
                  <div>
                    <strong style={{ color: 'var(--text-primary)' }}>FastAPI Backend Service</strong>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>http://localhost:8000 · Uvicorn ASGI Worker</div>
                  </div>
                </div>
                <span className="badge-severity low">Online</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px', background: 'var(--bg-tertiary)', borderRadius: 8, border: '1px solid var(--card-border)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <Cpu size={20} color="var(--blue)" />
                  <div>
                    <strong style={{ color: 'var(--text-primary)' }}>Qdrant Vector Database Engine</strong>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>In-Memory Mode · Embedding Dimension: 384 (Cosine)</div>
                  </div>
                </div>
                <span className="badge-severity low">Active</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px', background: 'var(--bg-tertiary)', borderRadius: 8, border: '1px solid var(--card-border)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <Database size={20} color="var(--blue)" />
                  <div>
                    <strong style={{ color: 'var(--text-primary)' }}>SQLite Telemetry Corpus</strong>
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
              <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                SLACK / MS TEAMS INCOMING WEBHOOK URL
              </label>
              <input
                type="text"
                value={slackWebhook}
                onChange={e => setSlackWebhook(e.target.value)}
                style={{ ...inputStyle, fontFamily: 'var(--font-mono)' }}
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
            <h3 className="card-title">Station UI & Telemetry Frequency</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                  TELEMETRY SYNC INTERVAL
                </label>
                <select
                  value={pollInterval}
                  onChange={e => setPollInterval(e.target.value)}
                  style={inputStyle}
                >
                  <option value="5">Every 5 seconds (Real-Time Stream)</option>
                  <option value="15">Every 15 seconds (Standard SOC)</option>
                  <option value="60">Every 60 seconds (Conservative)</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                  VISUAL DENSITY
                </label>
                <select
                  defaultValue="dense"
                  style={inputStyle}
                >
                  <option value="dense">High Density (Enterprise SOC)</option>
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
