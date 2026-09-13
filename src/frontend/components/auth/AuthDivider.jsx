import React from 'react';

export function AuthDivider({ text = "or continue with credentials" }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        textAlign: 'center',
        margin: '18px 0',
        color: 'var(--text-muted)',
        fontSize: 12,
        fontWeight: 500,
      }}
    >
      <div style={{ flex: 1, borderBottom: '1px solid var(--card-border)' }} />
      <span style={{ padding: '0 12px' }}>{text}</span>
      <div style={{ flex: 1, borderBottom: '1px solid var(--card-border)' }} />
    </div>
  );
}

export default AuthDivider;
