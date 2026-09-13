import React, { useState } from 'react';
import { ShieldAlert, Server, Terminal, Database, Globe, ArrowRight } from 'lucide-react';

/**
 * Interactive Attack Chain Topology Graph
 */
export function AttackGraph({ chain }) {
  const [activeNode, setActiveNode] = useState(null);

  const nodes = [
    {
      id: 'src',
      label: chain?.source_ip || '198.51.100.24',
      type: 'Adversary (C2 Origin)',
      icon: Globe,
      color: '#EF4444',
      x: 70,
      y: 190,
      status: 'Threat Actor'
    },
    {
      id: 'entry',
      label: 'Edge Bastion / SSH:22',
      type: 'Ingress Vector',
      icon: Terminal,
      color: '#F97316',
      x: 270,
      y: 100,
      status: 'Exploited'
    },
    {
      id: 'host1',
      label: chain?.dest_ips?.[0] || '10.0.4.12',
      type: 'Compromised Pivot',
      icon: Server,
      color: '#EF4444',
      x: 470,
      y: 190,
      status: 'Root Access (LSASS Dump)'
    },
    {
      id: 'target',
      label: chain?.dest_ips?.[1] || '10.0.2.8',
      type: 'Internal Mission DB',
      icon: Database,
      color: '#EAB308',
      x: 690,
      y: 120,
      status: 'Targeted (SMB Staging)'
    }
  ];

  const edges = [
    { from: nodes[0], to: nodes[1], label: 'T1595 Recon Sweep' },
    { from: nodes[1], to: nodes[2], label: 'T1110 SSH Brute-Force' },
    { from: nodes[2], to: nodes[3], label: 'T1021 Lateral Movement' },
  ];

  return (
    <div className="topology-wrap">
      <div style={{ position: 'absolute', top: 16, left: 20, zIndex: 10 }}>
        <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--cyan-bright)', textTransform: 'uppercase' }}>
          ATTACK TOPOLOGY GRAPH
        </span>
        <h4 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginTop: 2 }}>
          Observed Lateral Kill-Chain Progression
        </h4>
      </div>

      <svg className="topology-svg" viewBox="0 0 820 380">
        <defs>
          <linearGradient id="edgeGrad" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#EF4444" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#06B6D4" stopOpacity="0.8" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Edges */}
        {edges.map((e, idx) => {
          const dx = e.to.x - e.from.x;
          const dy = e.to.y - e.from.y;
          const cx = (e.from.x + e.to.x) / 2;
          const cy = (e.from.y + e.to.y) / 2 - 25;

          return (
            <g key={idx}>
              <path
                d={`M ${e.from.x} ${e.from.y} Q ${cx} ${cy} ${e.to.x} ${e.to.y}`}
                fill="none"
                stroke="url(#edgeGrad)"
                strokeWidth="2.5"
                strokeDasharray="6 4"
              />
              <text
                x={cx}
                y={cy - 8}
                fill="#94A3B8"
                fontSize="10"
                fontWeight="600"
                textAnchor="middle"
                fontFamily="var(--font-mono)"
              >
                {e.label}
              </text>
            </g>
          );
        })}

        {/* Nodes */}
        {nodes.map(node => {
          const Icon = node.icon;
          const isSelected = activeNode?.id === node.id;
          return (
            <g
              key={node.id}
              transform={`translate(${node.x}, ${node.y})`}
              onClick={() => setActiveNode(node)}
              style={{ cursor: 'pointer' }}
            >
              <circle
                r={isSelected ? 32 : 26}
                fill="#131A2A"
                stroke={node.color}
                strokeWidth={isSelected ? 3 : 2}
                filter="url(#glow)"
                style={{ transition: 'all 0.2s' }}
              />
              <foreignObject x={-14} y={-14} width={28} height={28}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: node.color }}>
                  <Icon size={20} />
                </div>
              </foreignObject>
              <text
                y={44}
                fill="#F8FAFC"
                fontSize="11.5"
                fontWeight="700"
                textAnchor="middle"
                fontFamily="var(--font-mono)"
              >
                {node.label}
              </text>
              <text
                y={58}
                fill="#64748B"
                fontSize="9.5"
                fontWeight="600"
                textAnchor="middle"
              >
                {node.type}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Selected Node Inspector Drawer */}
      {activeNode && (
        <div style={{
          position: 'absolute',
          bottom: 16,
          right: 20,
          background: 'rgba(19, 26, 42, 0.95)',
          backdropFilter: 'blur(8px)',
          border: '1px solid var(--card-border-glow)',
          borderRadius: 8,
          padding: '12px 16px',
          width: 260,
          boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
          zIndex: 20
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
            <strong style={{ fontSize: 13, color: activeNode.color }}>{activeNode.type}</strong>
            <button
              onClick={() => setActiveNode(null)}
              style={{ background: 'none', border: 'none', color: '#94A3B8', cursor: 'pointer', fontSize: 12 }}
            >
              ✕
            </button>
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: '#fff', marginBottom: 6 }}>
            {activeNode.label}
          </div>
          <div style={{ fontSize: 11, color: '#94A3B8' }}>
            Telemetry: <strong style={{ color: '#F8FAFC' }}>{activeNode.status}</strong>
          </div>
        </div>
      )}
    </div>
  );
}
