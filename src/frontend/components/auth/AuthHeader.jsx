import React from 'react';

export function AuthHeader({
  title,
  subtitle,
  badge = 'Level 3 Clearance Gateway',
}) {
  return (
    <div style={{ marginBottom: 14 }}>
      {badge && (
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 5,
            padding: '3px 8px',
            borderRadius: 9999,
            background: 'rgba(37, 99, 235, 0.08)',
            border: '1px solid rgba(37, 99, 235, 0.22)',
            fontSize: 10.5,
            fontWeight: 700,
            color: 'var(--blue)',
            letterSpacing: '0.04em',
            marginBottom: 8,
          }}
        >
          <span
            style={{
              width: 5,
              height: 5,
              borderRadius: '50%',
              background: 'var(--blue)',
              boxShadow: '0 0 5px var(--blue)',
            }}
          />
          <span>{badge}</span>
        </div>
      )}

      <h1
        style={{
          fontSize: 20,
          fontWeight: 800,
          letterSpacing: '-0.025em',
          color: 'var(--text-primary)',
          lineHeight: 1.2,
          margin: 0,
        }}
      >
        {title}
      </h1>

      {subtitle && (
        <p
          style={{
            fontSize: 12.5,
            color: 'var(--text-secondary)',
            marginTop: 4,
            lineHeight: 1.4,
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
