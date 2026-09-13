import React, { useState } from 'react';

/**
 * Interactive SVG Area Trend Chart
 */
export function AreaTrendChart({ data = [], height = 180 }) {
  const [hoverIndex, setHoverIndex] = useState(null);
  if (!data.length) return null;

  const width = 600;
  const padding = 30;
  const maxVal = Math.max(...data.map(d => d.alerts || d.value || 100)) * 1.15;
  const minVal = 0;

  const points = data.map((d, i) => {
    const x = padding + (i / (data.length - 1)) * (width - 2 * padding);
    const y = height - padding - ((d.alerts || d.value || 0) - minVal) / (maxVal - minVal) * (height - 2 * padding);
    return { x, y, data: d };
  });

  const pathD = points.reduce((acc, p, i) => {
    return i === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`;
  }, '');

  const areaD = `${pathD} L ${points[points.length - 1].x} ${height - padding} L ${points[0].x} ${height - padding} Z`;

  return (
    <div style={{ width: '100%', position: 'relative' }}>
      <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', overflow: 'visible' }}>
        <defs>
          <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2563EB" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#2563EB" stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* Grid lines */}
        {[0, 0.5, 1].map((ratio, idx) => {
          const y = height - padding - ratio * (height - 2 * padding);
          return (
            <line
              key={idx}
              x1={padding}
              y1={y}
              x2={width - padding}
              y2={y}
              stroke="var(--card-border, #E2E8F0)"
              strokeDasharray="4 4"
            />
          );
        })}

        {/* Area fill & Path */}
        <path d={areaD} fill="url(#areaGrad)" />
        <path d={pathD} fill="none" stroke="#2563EB" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />

        {/* Data points */}
        {points.map((p, i) => (
          <g key={i} onMouseEnter={() => setHoverIndex(i)} onMouseLeave={() => setHoverIndex(null)}>
            <circle
              cx={p.x}
              cy={p.y}
              r={hoverIndex === i ? 6 : 4}
              fill="var(--card, #FFFFFF)"
              stroke="#2563EB"
              strokeWidth="2.5"
              style={{ cursor: 'pointer', transition: 'r 0.15s' }}
            />
            {/* X-axis labels */}
            <text
              x={p.x}
              y={height - 8}
              fill="var(--text-muted, #64748B)"
              fontSize="10"
              fontWeight="600"
              textAnchor="middle"
            >
              {p.data.day || p.data.label}
            </text>
          </g>
        ))}
      </svg>

      {/* Tooltip */}
      {hoverIndex !== null && (
        <div style={{
          position: 'absolute',
          top: 10,
          left: `${(points[hoverIndex].x / width) * 100}%`,
          transform: 'translateX(-50%)',
          background: 'var(--card, #FFFFFF)',
          border: '1px solid var(--card-border, #E2E8F0)',
          borderRadius: 6,
          padding: '6px 12px',
          fontSize: 11.5,
          color: 'var(--text-primary, #0F172A)',
          pointerEvents: 'none',
          boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
          whiteSpace: 'nowrap',
          zIndex: 10
        }}>
          <strong>{points[hoverIndex].data.day || points[hoverIndex].data.label}</strong>: {points[hoverIndex].data.alerts || points[hoverIndex].data.value} alerts
          {points[hoverIndex].data.incidents && ` (${points[hoverIndex].data.incidents} incidents)`}
        </div>
      )}
    </div>
  );
}

/**
 * Interactive Horizontal Bar Chart (for MITRE technique frequencies)
 */
export function FrequencyBarChart({ items = [] }) {
  const maxCount = Math.max(...items.map(x => x.count || 1), 1);
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {items.map((item, idx) => {
        const pct = Math.round((item.count / maxCount) * 100);
        let barColor = '#2563EB';
        if (item.level === 'Critical' || item.severity === 'critical') barColor = '#DC2626';
        else if (item.level === 'High' || item.severity === 'high') barColor = '#EA580C';
        else if (item.level === 'Medium' || item.severity === 'medium') barColor = '#D97706';

        return (
          <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
              <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>{item.technique || item.name}</span>
              <span style={{ color: 'var(--text-primary)', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{item.count}</span>
            </div>
            <div style={{ height: 7, background: 'var(--bg-tertiary, #F1F5F9)', borderRadius: 4, overflow: 'hidden', border: '1px solid var(--card-border, #E2E8F0)' }}>
              <div style={{
                height: '100%',
                width: `${pct}%`,
                background: barColor,
                borderRadius: 4,
                transition: 'width 0.8s ease'
              }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

/**
 * Risk Distribution Donut & Split Bar
 */
export function RiskDistributionChart({ distribution = {} }) {
  const crit = Number(distribution.critical || 0);
  const high = Number(distribution.high || 0);
  const med = Number(distribution.medium || 0);
  const low = Number(distribution.low || 0);
  const total = (crit + high + med + low) || 1;

  const tiers = [
    { label: 'Critical', count: crit, color: '#EF4444' },
    { label: 'High', count: high, color: '#F97316' },
    { label: 'Medium', count: med, color: '#EAB308' },
    { label: 'Low', count: low, color: '#22C55E' }
  ];

  return (
    <div>
      <div style={{ height: 12, display: 'flex', borderRadius: 6, overflow: 'hidden', marginBottom: 16 }}>
        {tiers.map(t => (
          <div
            key={t.label}
            title={`${t.label}: ${t.count}`}
            style={{
              width: `${(t.count / total) * 100}%`,
              background: t.color,
              transition: 'width 0.8s ease'
            }}
          />
        ))}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        {tiers.map(t => (
          <div key={t.label} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: t.color }} />
            <span style={{ color: 'var(--text-muted)' }}>{t.label}</span>
            <strong style={{ marginLeft: 'auto', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{t.count}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * MITRE ATT&CK Matrix Heatmap Component
 */
export function MitreMatrixHeatmap({ matrix = [], onSelectTechnique }) {
  return (
    <div className="matrix-container">
      <div className="matrix-grid">
        {matrix.map((col, cIdx) => (
          <div key={cIdx} className="matrix-column">
            <div className="matrix-col-header">{col.tactic}</div>
            {col.techniques.map(tech => {
              const heatClass = tech.severity ? `heat-${tech.severity}` : 'heat-none';
              return (
                <div
                  key={tech.id}
                  className={`matrix-cell ${heatClass}`}
                  onClick={() => onSelectTechnique && onSelectTechnique(tech)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span className="matrix-cell-id">{tech.id}</span>
                    <span style={{ fontSize: 10, fontWeight: 700, opacity: 0.8 }}>{tech.count}x</span>
                  </div>
                  <span className="matrix-cell-name">{tech.name}</span>
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
