import React from 'react';

/**
 * Enterprise Brand Emblem for Threat Intelligence Correlation & Alert Prioritisation.
 * 
 * Visual Symbolism:
 * - Outer Shield: Enterprise cyber protection & defense posture.
 * - Ingestion Nodes: Multi-source security telemetry & alert logs.
 * - Convergence Vectors: Deterministic attack chain correlation.
 * - Central Core: Calibrated alert prioritization & risk scoring.
 */
export function BrandLogo({ size = 26, className = "" }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={{ display: 'block' }}
    >
      <defs>
        <linearGradient id="brandShieldBorder" x1="4" y1="2" x2="28" y2="30" gradientUnits="userSpaceOnUse">
          <stop stopColor="#38BDF8" />
          <stop offset="1" stopColor="#2563EB" />
        </linearGradient>
        <linearGradient id="brandShieldFill" x1="16" y1="4" x2="16" y2="28" gradientUnits="userSpaceOnUse">
          <stop stopColor="#1E40AF" stopOpacity="0.35" />
          <stop offset="1" stopColor="#0F172A" stopOpacity="0.6" />
        </linearGradient>
        <filter id="coreGlow" x="11" y="11" width="10" height="10" filterUnits="userSpaceOnUse">
          <feGaussianBlur stdDeviation="1" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
      </defs>

      {/* Outer Tactical Shield */}
      <path
        d="M16 3.5L6.5 7.5V15C6.5 21.3 10.6 26.8 16 28.5C21.4 26.8 25.5 21.3 25.5 15V7.5L16 3.5Z"
        fill="url(#brandShieldFill)"
        stroke="url(#brandShieldBorder)"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Correlation Vectors (3 telemetry streams converging into central incident core) */}
      <path
        d="M10.5 11.5L16 16.2M21.5 11.5L16 16.2M16 8.8V16.2"
        stroke="#93C5FD"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Ingested Telemetry Nodes */}
      <circle cx="10.5" cy="11.5" r="1.75" fill="#38BDF8" />
      <circle cx="21.5" cy="11.5" r="1.75" fill="#38BDF8" />
      <circle cx="16" cy="8.8" r="1.75" fill="#60A5FA" />

      {/* Prioritization Target Core */}
      <circle cx="16" cy="16.2" r="3" fill="#FFFFFF" filter="url(#coreGlow)" />
      <circle cx="16" cy="16.2" r="1.4" fill="#1D4ED8" />

      {/* Baseline Containment Anchor Arc */}
      <path
        d="M12.5 22C13.5 23 14.7 23.8 16 24.2C17.3 23.8 18.5 23 19.5 22"
        stroke="#38BDF8"
        strokeWidth="1.4"
        strokeLinecap="round"
        opacity="0.85"
      />
    </svg>
  );
}
