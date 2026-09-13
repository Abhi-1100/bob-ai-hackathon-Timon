import React, { useEffect, useState } from 'react';
import { ShieldAlert, Layers, ExternalLink, Flame, Info, CheckCircle2, Upload } from 'lucide-react';
import { MitreMatrixHeatmap } from '../components/Charts';
import { MitreChip } from '../components/Common';
import { api } from '../services/api';

export function MitrePage({ onOpenChain, navigate }) {
  const [selectedTechnique, setSelectedTechnique] = useState(null);
  const [mitreData, setMitreData] = useState({ total_detected: 0, techniques: [], matrix: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getMitreOverview()
      .then(res => {
        if (res && typeof res === 'object') {
          setMitreData(res);
        }
      })
      .catch(() => {
        setMitreData({ total_detected: 0, techniques: [], matrix: [] });
      })
      .finally(() => setLoading(false));
  }, []);

  const flatTechniques = mitreData.techniques || [];
  const matrix = mitreData.matrix || [];

  return (
    <div>
      <div style={{ marginBottom: 20, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--cyan-bright)', textTransform: 'uppercase' }}>
            ENTERPRISE DEFENSE MATRIX
          </span>
          <h2 style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)', marginTop: 4 }}>
            MITRE ATT&CK® Matrix & Dynamic Analytics
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginTop: 4 }}>
            Adversary tactics and techniques correlated dynamically from user uploaded security alert logs.
          </p>
        </div>

        {flatTechniques.length === 0 && !loading && (
          <button className="btn btn-primary" onClick={() => navigate('/upload')}>
            <Upload size={14} />
            <span>Upload Alert CSV</span>
          </button>
        )}
      </div>

      {/* 0-State banner if no techniques mapped */}
      {flatTechniques.length === 0 && !loading && (
        <div style={{
          background: 'rgba(6, 182, 212, 0.05)',
          border: '1px solid rgba(6, 182, 212, 0.2)',
          borderRadius: 8,
          padding: '24px',
          marginBottom: 24,
          textAlign: 'center'
        }}>
          <Layers size={36} color="var(--cyan-bright)" style={{ opacity: 0.6, marginBottom: 10 }} />
          <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 6 }}>
            0 MITRE ATT&CK Techniques Currently Detected
          </h3>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', maxWidth: 500, margin: '0 auto 16px' }}>
            Upload raw security logs via the Upload page. The MITRE mapping service will parse events (e.g. BruteForce, PortScan, LateralMovement) and plot them onto the enterprise matrix.
          </p>
          <button className="btn btn-primary" onClick={() => navigate('/upload')}>
            <span>Ingest Alerts CSV</span>
          </button>
        </div>
      )}

      {/* ATT&CK Matrix Heatmap Card */}
      <div className="soc-card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <div>
            <h3 className="card-title">
              <Layers size={17} color="var(--cyan-bright)" />
              <span>ATT&CK Enterprise Matrix Heatmap ({mitreData.total_detected || 0} Techniques Identified)</span>
            </h3>
            <p className="card-subtitle">Click on any detected technique cell to inspect observed campaigns and telemetry triggers</p>
          </div>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', fontSize: 11 }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 8, height: 8, borderRadius: 2, background: 'var(--critical)' }} /> Critical
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 8, height: 8, borderRadius: 2, background: 'var(--high)' }} /> High
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 8, height: 8, borderRadius: 2, background: 'var(--medium)' }} /> Medium
            </span>
          </div>
        </div>

        {matrix.length > 0 && matrix.some(m => m.techniques.length > 0) ? (
          <MitreMatrixHeatmap
            matrix={matrix}
            onSelectTechnique={tech => setSelectedTechnique(tech)}
          />
        ) : (
          <div style={{ padding: '40px 20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
            No techniques mapped. Ingest CSV alerts to populate the matrix heatmap.
          </div>
        )}
      </div>

      {/* Detail drawer / modal if technique selected */}
      {selectedTechnique && (
        <div className="soc-card" style={{
          marginBottom: 24,
          border: '1px solid var(--blue)',
          background: 'var(--card)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <code style={{ fontSize: 16, fontWeight: 800, color: 'var(--blue)' }}>{selectedTechnique.id}</code>
                <h3 style={{ fontSize: 18, fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>{selectedTechnique.name}</h3>
                <span className="badge-severity high">{selectedTechnique.tactic}</span>
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginTop: 8 }}>
                Observed in <strong>{selectedTechnique.count}</strong> alert events across correlated campaigns.
              </p>
            </div>
            <button className="btn btn-secondary" onClick={() => setSelectedTechnique(null)} style={{ padding: '4px 10px', fontSize: 12 }}>
              Close
            </button>
          </div>

          {selectedTechnique.chains?.length > 0 && (
            <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--card-border)' }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Correlated Attack Chains Featuring this Technique:
              </span>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 8 }}>
                {selectedTechnique.chains.map(cId => (
                  <button
                    key={cId}
                    className="btn btn-secondary"
                    onClick={() => onOpenChain && onOpenChain(cId)}
                    style={{ padding: '5px 12px', fontSize: 12, borderColor: 'rgba(6, 182, 212, 0.3)' }}
                  >
                    <span>{cId}</span>
                    <ExternalLink size={12} />
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Technique Frequency & Campaign Linkage Table */}
      <div className="soc-card">
        <div className="card-header">
          <div>
            <h3 className="card-title">
              <Flame size={17} color="var(--high)" />
              <span>Observed Technique Prevalence Table</span>
            </h3>
            <p className="card-subtitle">Techniques identified from ingested alert events</p>
          </div>
        </div>

        <div className="soc-table-wrap">
          <table className="soc-table">
            <thead>
              <tr>
                <th>Technique ID</th>
                <th>Technique Name</th>
                <th>Primary Tactic</th>
                <th>Observed Detections</th>
                <th>Severity Tier</th>
                <th>Linked Chains</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {flatTechniques.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '36px 0', color: 'var(--text-muted)' }}>
                    0 MITRE techniques observed. Ingest alert CSV to populate detections.
                  </td>
                </tr>
              ) : (
                flatTechniques.map(tech => (
                  <tr key={tech.id} onClick={() => setSelectedTechnique(tech)}>
                    <td>
                      <MitreChip id={tech.id} />
                    </td>
                    <td>
                      <strong style={{ color: 'var(--text-primary)' }}>{tech.name}</strong>
                    </td>
                    <td>
                      <span className="mono" style={{ fontSize: 12, color: 'var(--cyan-bright)' }}>{tech.tactic}</span>
                    </td>
                    <td>
                      <span className="mono" style={{ fontWeight: 700 }}>{tech.count} events</span>
                    </td>
                    <td>
                      <span className={`badge-severity ${tech.severity || 'medium'}`}>
                        {tech.severity || 'Medium'}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        {(tech.chains || []).slice(0, 4).map(cId => (
                          <button
                            key={cId}
                            onClick={(e) => {
                              e.stopPropagation();
                              if (onOpenChain) onOpenChain(cId);
                            }}
                            style={{
                              background: 'rgba(255, 255, 255, 0.05)',
                              border: '1px solid var(--card-border)',
                              borderRadius: 4,
                              color: 'var(--cyan-bright)',
                              padding: '2px 6px',
                              fontSize: 11,
                              fontFamily: 'var(--font-mono)',
                              cursor: 'pointer'
                            }}
                          >
                            {cId}
                          </button>
                        ))}
                      </div>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <button
                        className="btn btn-secondary"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedTechnique(tech);
                        }}
                        style={{ padding: '4px 10px', fontSize: 12 }}
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
