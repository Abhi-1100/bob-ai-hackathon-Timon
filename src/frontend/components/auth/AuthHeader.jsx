import React from 'react';

export function AuthHeader({
  title,
  subtitle,
  badge = 'Level 3 Clearance Gateway',
}) {
  return (
    <div style={{ marginBottom: 24 }}>
      {badge && (
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '4px 10px',
            borderRadius: 9999,
            background: 'rgba(37, 99, 235, 0.08)',
            border: '1px solid rgba(37, 99, 235, 0.22)',
            fontSize: 11,
            fontWeight: 700,
            color: 'var(--blue)',
            letterSpacing: '0.04em',
            marginBottom: 12,
          }}
        >
          <span
            style={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              background: 'var(--blue)',
              boxShadow: '0 0 6px var(--blue)',
            }}
          />
          <span>{badge}</span>
        </div>
      )}

      <h1
        style={{
          fontSize: 24,
          fontWeight: 800,
          letterSpacing: '-0.025em',
          color: 'var(--text-primary)',
          lineHeight: 1.25,
          margin: 0,
        }}
      >
        {title}
      </h1>

      {subtitle && (
        <p
          style={{
            fontSize: 13.5,
            color: 'var(--text-secondary)',
            marginTop: 6,
            lineHeight: 1.5,
            marginBottom: 0,
          }}
        >
          {subtitle}
        </p>
      )}
    </div>
  );
}

export default AuthHeader;
