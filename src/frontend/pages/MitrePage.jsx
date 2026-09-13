import React, { useState } from 'react';
import { ShieldAlert, Layers, ExternalLink, Flame, Info, CheckCircle2 } from 'lucide-react';
import { MitreMatrixHeatmap } from '../components/Charts';
import { MitreChip } from '../components/Common';
import { MOCK_MITRE_MATRIX, MOCK_MITRE_FREQUENCY } from '../services/mockData';

export function MitrePage({ onOpenChain }) {
  const [selectedTechnique, setSelectedTechnique] = useState(null);

  const flatTechniques = [
    { id: 'T1110', name: 'Brute Force', tactic: 'Credential Access', count: 48, chains: ['AC001', 'AC007', 'AC012'], severity: 'critical' },
    { id: 'T1595', name: 'Active Scanning', tactic: 'Reconnaissance', count: 42, chains: ['AC001', 'AC004', 'AC009'], severity: 'medium' },
    { id: 'T1190', name: 'Exploit Public-Facing Application', tactic: 'Initial Access', count: 35, chains: ['AC002', 'AC008'], severity: 'critical' },
    { id: 'T1059', name: 'Command and Scripting Interpreter', tactic: 'Execution', count: 29, chains: ['AC002', 'AC003', 'AC011'], severity: 'high' },
    { id: 'T1003', name: 'OS Credential Dumping', tactic: 'Credential Access', count: 24, chains: ['AC001', 'AC015'], severity: 'critical' },
    { id: 'T1021', name: 'Remote Services (SSH/RDP)', tactic: 'Lateral Movement', count: 19, chains: ['AC001', 'AC014'], severity: 'high' },
    { id: 'T1071', name: 'Application Layer Protocol', tactic: 'Command and Control', count: 16, chains: ['AC003', 'AC010'], severity: 'high' },
    { id: 'T1486', name: 'Data Encrypted for Impact', tactic: 'Impact', count: 8, chains: ['AC003', 'AC016'], severity: 'critical' },
  ];

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--cyan-bright)', textTransform: 'uppercase' }}>
          ENTERPRISE DEFENSE MATRIX
        </span>
        <h2 style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)', marginTop: 4 }}>
          MITRE ATT&CK® Matrix & Technique Analytics
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginTop: 4 }}>
          Tactics and techniques correlated across multi-source security feeds, highlighted by detection frequency and attack severity.
        </p>
      </div>

      {/* ATT&CK Matrix Heatmap Card */}
      <div className="soc-card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <div>
            <h3 className="card-title">
              <Layers size={17} color="var(--cyan-bright)" />
              <span>ATT&CK Enterprise Matrix Heatmap</span>
            </h3>
            <p className="card-subtitle">Click on any technique cell to inspect observed campaigns and telemetry triggers</p>
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

        <MitreMatrixHeatmap
          matrix={MOCK_MITRE_MATRIX}
          onSelectTechnique={tech => setSelectedTechnique(tech)}
        />
      </div>

      {/* Selected Technique Detail Modal / Drawer */}
      {selectedTechnique && (
        <div className="soc-card" style={{
          background: 'linear-gradient(145deg, rgba(6, 182, 212, 0.08), rgba(19, 26, 42, 0.95))',
          borderColor: 'var(--cyan)',
          marginBottom: 24
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <code style={{ fontSize: 16, fontWeight: 800, color: 'var(--cyan-bright)' }}>{selectedTechnique.id}</code>
                <h4 style={{ fontSize: 16, fontWeight: 700, color: '#fff' }}>{selectedTechnique.name}</h4>
              </div>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
                Observed in <strong>{selectedTechnique.count}</strong> correlated event triggers across active campaigns.
              </p>
            </div>
            <button
              className="btn btn-secondary"
              onClick={() => setSelectedTechnique(null)}
              style={{ padding: '4px 10px', fontSize: 12 }}
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* MITRE Table */}
      <div className="soc-card">
        <div className="card-header">
          <h3 className="card-title">Technique Inventory & Associated Chains</h3>
          <span className="mono" style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            {flatTechniques.length} Detected Techniques
          </span>
        </div>

        <div className="soc-table-wrap">
          <table className="soc-table">
            <thead>
              <tr>
                <th>Technique ID</th>
                <th>Technique Name</th>
                <th>ATT&CK Tactic</th>
                <th>Detections</th>
                <th>Associated Attack Chains</th>
                <th style={{ textAlign: 'right' }}>MITRE Reference</th>
              </tr>
            </thead>
            <tbody>
              {flatTechniques.map(tech => (
                <tr key={tech.id}>
                  <td>
                    <code style={{ fontSize: 13, fontWeight: 800, color: 'var(--cyan-bright)' }}>{tech.id}</code>
                  </td>
                  <td>
                    <strong style={{ color: 'var(--text-primary)' }}>{tech.name}</strong>
                  </td>
                  <td>
                    <span style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                      {tech.tactic}
                    </span>
                  </td>
                  <td>
                    <span className="mono" style={{ fontWeight: 700, color: '#F8FAFC' }}>
                      {tech.count} triggers
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                      {tech.chains.map(cid => (
                        <button
                          key={cid}
                          onClick={() => onOpenChain && onOpenChain(cid)}
                          style={{
                            background: 'rgba(255, 255, 255, 0.05)',
                            border: '1px solid var(--card-border)',
                            borderRadius: 4,
                            padding: '2px 8px',
                            color: 'var(--cyan-bright)',
                            fontSize: 11,
                            fontFamily: 'var(--font-mono)',
                            cursor: 'pointer'
                          }}
                        >
                          {cid}
                        </button>
                      ))}
                    </div>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <a
                      href={`https://attack.mitre.org/techniques/${tech.id.replace('.', '/')}/`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-secondary"
                      style={{ padding: '4px 10px', fontSize: 11 }}
                    >
                      <span>MITRE Docs</span>
                      <ExternalLink size={12} />
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
