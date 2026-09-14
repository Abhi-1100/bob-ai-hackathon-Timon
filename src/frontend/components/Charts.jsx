import React, { useState } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
  BarChart,
  LabelList,
} from 'recharts';

/* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
   Shared helpers
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */

// Strip "MM-DD " prefix and keep only "HH:MM" for dense time labels
const shortLabel = (raw) => {
  if (!raw) return '';
  const s = String(raw).trim();
  const parts = s.split(' ');
  return parts.length >= 2 ? parts[parts.length - 1] : s;
};

// Shared tooltip container
const TooltipBox = ({ children }) => (
  <div style={{
    background: 'var(--card, #fff)',
    border: '1px solid var(--card-border, #E2E8F0)',
    borderRadius: 10,
    padding: '10px 14px',
    fontSize: 12,
    color: 'var(--text-primary, #0F172A)',
    boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
    lineHeight: 1.7,
  }}>
    {children}
  </div>
);

/* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
   1. Telemetry Timeline â€” Bar + Line Combo Chart
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
const TimelineTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <TooltipBox>
      <div style={{ fontWeight: 700, marginBottom: 4, color: 'var(--text-secondary)' }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 10, height: 10, borderRadius: 2, background: p.color, display: 'inline-block' }} />
          <span style={{ color: 'var(--text-secondary)' }}>{p.name}:</span>
          <strong>{p.value}</strong>
        </div>
      ))}
    </TooltipBox>
  );
};

export function AreaTrendChart({ data = [], height = 220 }) {
  if (!data.length) return (
    <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
      No telemetry data available.
    </div>
  );

  const chartData = data.map(d => ({
    label: shortLabel(d.day || d.label || ''),
    fullLabel: d.day || d.label || '',
    Alerts: d.alerts || d.value || 0,
    Incidents: d.incidents || 0,
  }));

  // Thin ticks for dense datasets â€” at most 10
  const maxTicks = 10;
  const step = Math.max(1, Math.ceil(chartData.length / maxTicks));
  const ticks = chartData.filter((_, i) => i % step === 0).map(d => d.label);
  const hasIncidents = data.some(d => (d.incidents || 0) > 0);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={chartData} margin={{ top: 8, right: hasIncidents ? 40 : 16, left: -8, bottom: 4 }}>
        <defs>
          <linearGradient id="barGradAlerts" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#3B82F6" stopOpacity={0.9} />
            <stop offset="100%" stopColor="#1D4ED8" stopOpacity={0.7} />
          </linearGradient>
        </defs>

        <CartesianGrid strokeDasharray="3 3" stroke="var(--card-border, #E2E8F0)" vertical={false} />

        <XAxis
          dataKey="label"
          ticks={ticks}
          tick={{ fontSize: 10, fill: 'var(--text-muted, #64748B)', fontWeight: 600 }}
          axisLine={{ stroke: 'var(--card-border, #E2E8F0)' }}
          tickLine={false}
          interval={0}
        />

        <YAxis
          yAxisId="left"
          tick={{ fontSize: 10, fill: 'var(--text-muted, #64748B)' }}
          axisLine={false}
          tickLine={false}
          width={32}
        />

        {hasIncidents && (
          <YAxis
            yAxisId="right"
            orientation="right"
            tick={{ fontSize: 10, fill: 'var(--text-muted, #64748B)' }}
            axisLine={false}
            tickLine={false}
            width={28}
          />
        )}

        <Tooltip content={<TimelineTooltip />} cursor={{ fill: 'var(--card-border, #E2E8F0)', opacity: 0.4 }} />
        <Legend
          iconType="circle"
          iconSize={8}
          wrapperStyle={{ fontSize: 11, color: 'var(--text-muted)', paddingTop: 8 }}
        />

        <Bar
          yAxisId="left"
          dataKey="Alerts"
          fill="url(#barGradAlerts)"
          radius={[4, 4, 0, 0]}
          maxBarSize={32}
        />

        {hasIncidents && (
          <Line
            yAxisId="right"
            dataKey="Incidents"
            type="monotone"
            stroke="#F97316"
            strokeWidth={2.5}
            dot={{ r: 3, fill: '#F97316', strokeWidth: 0 }}
            activeDot={{ r: 5 }}
          />
        )}
      </ComposedChart>
    </ResponsiveContainer>
  );
}

/* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
   2. MITRE Frequency â€” Horizontal Bar Chart
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
const MitreTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0];
  return (
    <TooltipBox>
      <div style={{ fontWeight: 700, marginBottom: 2 }}>{d.payload.name}</div>
      <div>Count: <strong>{d.value}</strong></div>
    </TooltipBox>
  );
};

const SEVERITY_COLORS = {
  critical: '#EF4444',
  high: '#F97316',
  medium: '#EAB308',
  low: '#22C55E',
};

export function FrequencyBarChart({ items = [] }) {
  if (!items.length) return null;

  const chartData = items.map(item => ({
    name: item.technique || item.name || 'Unknown',
    count: item.count || 0,
    color: SEVERITY_COLORS[(item.severity || item.level || '').toLowerCase()] || '#3B82F6',
  }));

  return (
    <ResponsiveContainer width="100%" height={Math.max(160, chartData.length * 44)}>
      <BarChart
        data={chartData}
        layout="vertical"
        margin={{ top: 4, right: 48, left: 8, bottom: 4 }}
        barCategoryGap="30%"
      >
        <CartesianGrid strokeDasharray="3 3" stroke="var(--card-border, #E2E8F0)" horizontal={false} />
        <XAxis
          type="number"
          tick={{ fontSize: 10, fill: 'var(--text-muted, #64748B)' }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          type="category"
          dataKey="name"
          width={115}
          tick={{ fontSize: 11, fill: 'var(--text-secondary, #334155)', fontWeight: 600 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<MitreTooltip />} cursor={{ fill: 'var(--card-border, #E2E8F0)', opacity: 0.4 }} />
        <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={18}>
          {chartData.map((entry, i) => (
            <Cell key={i} fill={entry.color} />
          ))}
          <LabelList
            dataKey="count"
            position="right"
            style={{ fontSize: 11, fontWeight: 700, fill: 'var(--text-primary, #0F172A)' }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
   3. Risk Distribution â€” Donut Pie + Legend
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
const RISK_COLORS = {
  Critical: '#EF4444',
  High: '#F97316',
  Medium: '#EAB308',
  Low: '#22C55E',
};

const RiskTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0];
  return (
    <TooltipBox>
      <span style={{ fontWeight: 700 }}>{d.name}:</span> {d.value} chain{d.value !== 1 ? 's' : ''}
    </TooltipBox>
  );
};

const renderPctLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
  if (percent < 0.06) return null;
  const RADIAN = Math.PI / 180;
  const r = innerRadius + (outerRadius - innerRadius) * 0.58;
  const x = cx + r * Math.cos(-midAngle * RADIAN);
  const y = cy + r * Math.sin(-midAngle * RADIAN);
  return (
    <text x={x} y={y} fill="#fff" textAnchor="middle" dominantBaseline="central" fontSize={11} fontWeight={700}>
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

export function RiskDistributionChart({ distribution = {} }) {
  const [activeIndex, setActiveIndex] = useState(null);

  const tiers = [
    { name: 'Critical', value: Number(distribution.critical || 0) },
    { name: 'High',     value: Number(distribution.high || 0) },
    { name: 'Medium',   value: Number(distribution.medium || 0) },
    { name: 'Low',      value: Number(distribution.low || 0) },
  ].filter(t => t.value > 0);

  const total = tiers.reduce((s, t) => s + t.value, 0);

  if (total === 0) return (
    <div style={{ height: 160, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
      No attack chains scored yet.
    </div>
  );

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
      <ResponsiveContainer width={160} height={160}>
        <PieChart>
          <Pie
            data={tiers}
            cx="50%"
            cy="50%"
            innerRadius={44}
            outerRadius={72}
            paddingAngle={3}
            dataKey="value"
            labelLine={false}
            label={renderPctLabel}
            onMouseEnter={(_, i) => setActiveIndex(i)}
            onMouseLeave={() => setActiveIndex(null)}
            stroke="none"
          >
            {tiers.map((entry, i) => (
              <Cell
                key={i}
                fill={RISK_COLORS[entry.name]}
                opacity={activeIndex === null || activeIndex === i ? 1 : 0.55}
                style={{ cursor: 'pointer', transition: 'opacity 0.2s' }}
              />
            ))}
          </Pie>
          <Tooltip content={<RiskTooltip />} />
        </PieChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 10 }}>
        {tiers.map((t, i) => {
          const pct = ((t.value / total) * 100).toFixed(1);
          return (
            <div
              key={i}
              style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'default' }}
              onMouseEnter={() => setActiveIndex(i)}
              onMouseLeave={() => setActiveIndex(null)}
            >
              <span style={{
                width: 10, height: 10, borderRadius: 3,
                background: RISK_COLORS[t.name],
                flexShrink: 0,
                opacity: activeIndex === null || activeIndex === i ? 1 : 0.4,
                transition: 'opacity 0.2s',
              }} />
              <span style={{ fontSize: 12, color: 'var(--text-secondary)', flex: 1 }}>{t.name}</span>
              <span style={{ fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
                {t.value}
              </span>
              <span style={{ fontSize: 11, color: 'var(--text-muted)', minWidth: 36, textAlign: 'right' }}>
                {pct}%
              </span>
            </div>
          );
        })}
        <div style={{ borderTop: '1px solid var(--card-border)', paddingTop: 8, fontSize: 12, color: 'var(--text-muted)' }}>
          Total: <strong style={{ color: 'var(--text-primary)' }}>{total}</strong> chains
        </div>
      </div>
    </div>
  );
}

/* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
   4. MITRE ATT&CK Matrix Heatmap (unchanged â€” CSS grid)
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
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
