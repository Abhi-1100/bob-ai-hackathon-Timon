import React from 'react';
import { AlertTriangle, Database, X, ShieldAlert } from 'lucide-react';
import { severity } from '../services/api';

export function SeverityBadge({ value = 'unknown' }) {
  const sev = severity(value) || 'low';
  return (
    <span className={`badge-severity ${sev}`}>
      <span className="badge-dot" />
      {value || 'Unknown'}
    </span>
  );
}

export function MitreChip({ id, name }) {
  return (
    <span className="mitre-chip" title={name || id}>
      <span>{id}</span>
      {name && <strong>{name}</strong>}
    </span>
  );
}

export function RiskScoreGauge({ score = 0, size = 80 }) {
  const safe = Math.max(0, Math.min(100, Number(score) || 0));
  const strokeWidth = 8;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (safe / 100) * circumference;

  let color = '#22C55E';
  if (safe >= 85) color = '#EF4444';
  else if (safe >= 70) color = '#F97316';
  else if (safe >= 50) color = '#EAB308';

  return (
    <div className="radial-gauge" style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#1E293B"
          strokeWidth={strokeWidth}
          fill="transparent"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          fill="transparent"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: 'stroke-dashoffset 0.8s ease' }}
        />
      </svg>
      <div className="radial-gauge-text">
        <span className="radial-gauge-value">{safe}</span>
        <span className="radial-gauge-label">/ 100</span>
      </div>
    </div>
  );
}

export function EmptyState({ icon: Icon = Database, title, text, action }) {
  return (
    <div style={{
      textAlign: 'center',
      padding: '48px 24px',
      background: 'rgba(19, 26, 42, 0.4)',
      borderRadius: 'var(--radius-lg)',
      border: '1px dashed var(--card-border)'
    }}>
      <div style={{
        width: 48,
        height: 48,
        borderRadius: '50%',
        background: 'rgba(255, 255, 255, 0.03)',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--cyan-bright)',
        marginBottom: 12
      }}>
        <Icon size={24} />
      </div>
      <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 6 }}>{title}</h3>
      <p style={{ fontSize: 13, color: 'var(--text-muted)', maxWidth: 420, margin: '0 auto 16px' }}>{text}</p>
      {action}
    </div>
  );
}

export function ErrorBanner({ message, onDismiss }) {
  if (!message) return null;
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      padding: '12px 16px',
      background: 'var(--critical-bg)',
      border: '1px solid rgba(239, 68, 68, 0.3)',
      borderRadius: 'var(--radius-md)',
      color: '#FCA5A5',
      fontSize: 13,
      marginBottom: 20
    }}>
      <AlertTriangle size={18} color="var(--critical)" />
      <span style={{ flex: 1 }}>{message}</span>
      {onDismiss && (
        <button onClick={onDismiss} style={{ background: 'none', border: 'none', color: '#FCA5A5', cursor: 'pointer' }}>
          <X size={16} />
        </button>
      )}
    </div>
  );
}
