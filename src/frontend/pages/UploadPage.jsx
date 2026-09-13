import React, { useRef, useState } from 'react';
import {
  UploadCloud,
  FileText,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Database,
  RefreshCw,
  Zap,
  Trash2,
  Info,
  Check,
  Layers,
  Network,
  ShieldAlert
} from 'lucide-react';
import { api } from '../services/api';
import { ErrorBanner } from '../components/Common';

export function UploadPage({ navigate, onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [currentStep, setCurrentStep] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [resetMessage, setResetMessage] = useState('');
  const [confirmReset, setConfirmReset] = useState(false);
  const fileInputRef = useRef(null);
  const [hasUploadedState, setHasUploadedState] = useState(() => {
    return typeof window !== 'undefined' && localStorage.getItem('d2_has_uploaded') === 'true';
  });

  const handleFile = (f) => {
    setError('');
    setResult(null);
    setResetMessage('');
    if (!f) return;
    if (!f.name.toLowerCase().endsWith('.csv')) {
      setError('Invalid file format: Only RFC 4180 compliant .csv security alert logs are accepted.');
      return;
    }
    setFile(f);
  };

  const executeIngest = async (selectedFile = file) => {
    if (!selectedFile) return;
    setBusy(true);
    setError('');
    setResetMessage('');
    setCurrentStep('Ingesting alerts from CSV & validating schemas...');

    try {
      setCurrentStep('Correlating multi-stage attack chains & mapping MITRE techniques...');
      const response = await api.uploadAndIngest(selectedFile);
      setResult(response);
      try {
        localStorage.setItem('d2_has_uploaded', 'true');
        setHasUploadedState(true);
      } catch {}
      if (onUploadSuccess) onUploadSuccess();
    } catch (err) {
      setError(err.message || 'Alert ingest failed. Please check CSV format and API connection.');
    } finally {
      setBusy(false);
      setCurrentStep('');
    }
  };

  const handleResetData = async () => {
    setBusy(true);
    setError('');
    try {
      const res = await api.resetDatabase();
      setResetMessage(res.message || 'All database records wiped to 0. System is in 0-state.');
      setResult(null);
      setFile(null);
      setConfirmReset(false);
      try {
        localStorage.setItem('d2_has_uploaded', 'false');
        setHasUploadedState(false);
      } catch {}
    } catch (err) {
      setError(err.message || 'Failed to reset database.');
    } finally {
      setBusy(false);
    }
  };

  const loadEnterpriseSampleData = async () => {
    setBusy(true);
    setError('');
    setResetMessage('');
    setCurrentStep('Preparing enterprise threat alerts (1,000 alerts)...');

    try {
      // Fetch the actual sample CSV from the repository if available, or generate full 100-alert synthetic log
      let csvContent = "";
      try {
        const fetchRes = await fetch('/sample_data/enterprise_threat_alerts_1000.csv');
        if (fetchRes.ok) {
          csvContent = await fetchRes.text();
        }
      } catch {
        csvContent = "";
      }

      if (!csvContent || !csvContent.includes('timestamp')) {
        // High fidelity multi-stage attack logs
        const eventsList = [
          'PortScan', 'SSH_BruteForce', 'CredentialDumping', 'LateralMovement_SSH', 'DataStaging',
          'Web_Exploit_Attempt', 'WebShell_Dropped', 'CommandExecution', 'PrivilegeEscalation', 'DataExfiltration'
        ];
        const severities = ['Low', 'Medium', 'High', 'Critical', 'Critical'];
        const srcIps = ['198.51.100.24', '203.0.113.88', '185.220.101.5', '194.26.29.112', '45.154.255.89'];
        const dstIps = ['10.0.4.12', '10.0.1.50', '10.0.2.100', '10.0.5.20', '10.0.3.15'];

        let rows = ["timestamp,src_ip,dst_ip,event,severity"];
        const baseTime = new Date('2026-09-13T12:00:00Z').getTime();

        for (let i = 0; i < 150; i++) {
          const t = new Date(baseTime + i * 45000).toISOString();
          const src = srcIps[i % srcIps.length];
          const dst = dstIps[Math.floor(i / 10) % dstIps.length];
          const ev = eventsList[i % eventsList.length];
          const sev = severities[i % severities.length];
          rows.push(`${t},${src},${dst},${ev},${sev}`);
        }
        csvContent = rows.join("\n");
      }

      const sampleBlob = new Blob([csvContent], { type: 'text/csv' });
      const sampleFile = new File([sampleBlob], 'enterprise_threat_alerts.csv', { type: 'text/csv' });
      setFile(sampleFile);
      await executeIngest(sampleFile);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
      setCurrentStep('');
    }
  };

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>
      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--cyan-bright)', textTransform: 'uppercase' }}>
            MULTI-SOURCE DATA INTAKE
          </span>
          <h2 style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)', marginTop: 4 }}>
            Security Alert Ingestion & Dynamic Pipeline
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginTop: 4 }}>
            Upload raw security logs. The backend pipeline ingests, validates, clusters into attack chains, maps to MITRE ATT&CK, and calculates risk scores dynamically.
          </p>
        </div>

        {/* Reset Database to 0-state Button */}
        <div>
          {confirmReset ? (
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <span style={{ fontSize: 12, color: 'var(--critical)', fontWeight: 600 }}>Wipe all DB data to 0?</span>
              <button
                className="btn btn-primary"
                style={{ background: 'var(--critical)', borderColor: 'var(--critical)', padding: '6px 12px', fontSize: 12 }}
                disabled={busy}
                onClick={handleResetData}
              >
                Confirm Wipe
              </button>
              <button
                className="btn btn-secondary"
                style={{ padding: '6px 10px', fontSize: 12 }}
                onClick={() => setConfirmReset(false)}
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              className="btn btn-secondary"
              style={{ color: 'var(--critical)', borderColor: 'rgba(239, 68, 68, 0.3)', padding: '7px 14px', fontSize: 12 }}
              onClick={() => setConfirmReset(true)}
              title="Wipe database back to 0 state"
            >
              <Trash2 size={14} />
              <span>Reset to 0-State</span>
            </button>
          )}
        </div>
      </div>

      <ErrorBanner message={error} onDismiss={() => setError('')} />

      {/* Onboarding Callout: Ingest CSV to Unlock Platform */}
      {!hasUploadedState && !result && (
        <div style={{
          padding: '20px 24px',
          background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.12), rgba(6, 182, 212, 0.08))',
          border: '1px solid rgba(6, 182, 212, 0.4)',
          borderRadius: 12,
          marginBottom: 24,
          display: 'flex',
          alignItems: 'flex-start',
          gap: 16,
          boxShadow: '0 4px 20px -2px rgba(6, 182, 212, 0.15)'
        }}>
          <div style={{
            width: 44,
            height: 44,
            borderRadius: 10,
            background: 'rgba(6, 182, 212, 0.2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--cyan-bright)',
            flexShrink: 0
          }}>
            <ShieldAlert size={24} />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
              <span style={{
                background: 'var(--blue)',
                color: '#fff',
                fontSize: 10.5,
                fontWeight: 700,
                padding: '2px 8px',
                borderRadius: 4,
                letterSpacing: '0.05em',
                textTransform: 'uppercase'
              }}>
                Action Required
              </span>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                Initial Setup: Upload Security Telemetry to Launch Platform
              </h3>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: 13, lineHeight: 1.5, margin: 0 }}>
              To access your Threat Intelligence Dashboard, Attack Chains, and AI Copilot, please upload your security alert CSV below, or click <strong>Load Test Alert CSV</strong> to initialize with enterprise telemetry.
            </p>
          </div>
        </div>
      )}

      {resetMessage && (
        <div style={{
          padding: '12px 18px',
          background: 'rgba(6, 182, 212, 0.1)',
          border: '1px solid rgba(6, 182, 212, 0.3)',
          borderRadius: 8,
          marginBottom: 20,
          color: 'var(--cyan-bright)',
          fontSize: 13,
          display: 'flex',
          alignItems: 'center',
          gap: 10
        }}>
          <CheckCircle2 size={16} />
          <span>{resetMessage}</span>
        </div>
      )}

      {/* Upload result success card */}
      {result ? (
        <div className="soc-card" style={{
          background: 'linear-gradient(145deg, rgba(34, 197, 94, 0.08), rgba(19, 26, 42, 0.9))',
          borderColor: 'rgba(34, 197, 94, 0.3)',
          padding: 32
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20 }}>
            <div style={{
              width: 50,
              height: 50,
              borderRadius: '50%',
              background: 'rgba(34, 197, 94, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#4ADE80'
            }}>
              <CheckCircle2 size={30} />
            </div>
            <div>
              <span style={{ fontSize: 11, fontWeight: 700, color: '#4ADE80', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                INGESTION & CORRELATION PIPELINE COMPLETE
              </span>
              <h3 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)' }}>
                {result.alerts_ingested ?? result.count ?? 0} Alerts Successfully Ingested
              </h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginTop: 2 }}>
                {result.message || 'Correlated cross-domain security events into active attack chains.'}
              </p>
            </div>
          </div>

          {/* Dynamic Pipeline Summary Metrics */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: 12,
            marginBottom: 24,
            padding: 16,
            background: 'var(--bg-tertiary)',
            borderRadius: 8,
            border: '1px solid var(--card-border)'
          }}>
            <div>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Alerts Ingested</span>
              <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--cyan-bright)' }}>
                {result.alerts_ingested ?? 0}
              </div>
            </div>
            <div>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Attack Chains Correlated</span>
              <div style={{ fontSize: 18, fontWeight: 800, color: '#60A5FA' }}>
                {result.chains_correlated ?? 'Generated'}
              </div>
            </div>
            <div>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>MITRE Techniques Mapped</span>
              <div style={{ fontSize: 18, fontWeight: 800, color: '#FBBF24' }}>
                {result.mitre_mapped ?? 'Active'}
              </div>
            </div>
            <div>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Chains Risk-Scored</span>
              <div style={{ fontSize: 18, fontWeight: 800, color: '#EF4444' }}>
                {result.risk_scored ?? 'Prioritized'}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <button className="btn btn-primary" onClick={() => navigate('/dashboard')}>
              <span>View Dynamic Dashboard</span>
              <ArrowRight size={16} />
            </button>
            <button className="btn btn-secondary" onClick={() => navigate('/attack-chains')}>
              <Network size={15} />
              <span>Explore Attack Chains</span>
            </button>
            <button className="btn btn-secondary" onClick={() => { setFile(null); setResult(null); }}>
              <span>Upload Another CSV</span>
            </button>
          </div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 24 }}>
          {/* Drag and drop zone */}
          <div
            className="soc-card"
            style={{
              border: file ? '2px solid var(--cyan)' : '2px dashed var(--card-border)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '48px 24px',
              textAlign: 'center',
              cursor: 'pointer',
              background: file ? 'rgba(37, 99, 235, 0.05)' : 'var(--bg-tertiary)'
            }}
            onDragOver={e => e.preventDefault()}
            onDrop={e => {
              e.preventDefault();
              handleFile(e.dataTransfer.files[0]);
            }}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              type="file"
              ref={fileInputRef}
              accept=".csv,text/csv"
              hidden
              onChange={e => handleFile(e.target.files[0])}
            />

            <div style={{
              width: 56,
              height: 56,
              borderRadius: '50%',
              background: 'rgba(6, 182, 212, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--cyan-bright)',
              marginBottom: 16
            }}>
              <UploadCloud size={28} />
            </div>

            {file ? (
              <>
                <h4 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>{file.name}</h4>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
                  {(file.size / 1024).toFixed(1)} KB · Ready to ingest into dynamic pipeline
                </p>
                <button
                  className="btn btn-secondary"
                  style={{ marginTop: 16, padding: '6px 14px', fontSize: 12 }}
                  onClick={e => {
                    e.stopPropagation();
                    setFile(null);
                  }}
                >
                  Choose Different File
                </button>
              </>
            ) : (
              <>
                <h4 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
                  Drag and drop alert CSV here
                </h4>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
                  or click to browse from local file system
                </p>
                <span style={{
                  fontSize: 11,
                  color: 'var(--text-muted)',
                  marginTop: 16,
                  padding: '4px 10px',
                  background: 'rgba(255, 255, 255, 0.03)',
                  borderRadius: 4
                }}>
                  Standard CSV Format (timestamp, src_ip, dst_ip, event, severity)
                </span>
              </>
            )}
          </div>

          {/* Validation Checklist & Actions */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div className="soc-card">
              <div className="card-header">
                <h4 className="card-title">
                  <ShieldCheck size={16} color="var(--cyan-bright)" />
                  <span>Validation Schema</span>
                </h4>
              </div>
              <p style={{ fontSize: 12.5, color: 'var(--text-muted)', marginBottom: 14 }}>
                The ingestion parser validates every row against required canonical fields:
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {['timestamp', 'src_ip', 'dst_ip', 'event', 'severity'].map(col => (
                  <div key={col} style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 12px',
                    background: 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid var(--card-border)',
                    borderRadius: 6
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <CheckCircle2 size={14} color="#22C55E" />
                      <code style={{ fontSize: 12, color: 'var(--cyan-bright)' }}>{col}</code>
                    </div>
                    <span style={{ fontSize: 10.5, color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                      Required
                    </span>
                  </div>
                ))}
              </div>

              {busy && (
                <div style={{ marginTop: 16, padding: '10px 14px', background: 'rgba(6, 182, 212, 0.08)', borderRadius: 6, border: '1px solid rgba(6, 182, 212, 0.2)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--cyan-bright)' }}>
                    <RefreshCw size={14} className="spin" />
                    <span>{currentStep || 'Processing pipeline…'}</span>
                  </div>
                </div>
              )}

              <button
                className="btn btn-primary"
                style={{ width: '100%', marginTop: 20 }}
                disabled={!file || busy}
                onClick={() => executeIngest(file)}
              >
                {busy ? (
                  <>
                    <RefreshCw className="spin" size={16} />
                    <span>Executing Pipeline…</span>
                  </>
                ) : (
                  <>
                    <Zap size={16} />
                    <span>Run Ingestion & Correlation</span>
                  </>
                )}
              </button>
            </div>

            {/* One-Click Enterprise Dataset Quick Test */}
            <div className="soc-card">
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                <Database size={20} color="var(--cyan-bright)" style={{ flexShrink: 0, marginTop: 2 }} />
                <div>
                  <h4 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
                    Enterprise Test Dataset
                  </h4>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                    Quickly evaluate with canonical multi-source alerts to populate all 12 modules dynamically.
                  </p>
                  <button
                    className="btn btn-secondary"
                    style={{ marginTop: 12, fontSize: 12, borderColor: 'rgba(6, 182, 212, 0.3)' }}
                    disabled={busy}
                    onClick={loadEnterpriseSampleData}
                  >
                    <Zap size={14} color="var(--cyan-bright)" />
                    <span>Load Test Alert CSV</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
