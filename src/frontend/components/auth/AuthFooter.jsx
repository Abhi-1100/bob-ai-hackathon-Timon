import React from 'react';

export function AuthFooter({
  mode = 'login', // 'login' | 'register' | 'forgot-password' | 'reset-password'
  navigate,
}) {
  return (
    <div style={{ marginTop: 24, textAlign: 'center', fontSize: 13 }}>
      {mode === 'login' && (
        <div style={{ color: 'var(--text-secondary)' }}>
          <span>Don't have an operator account? </span>
          <button
            type="button"
            onClick={() => navigate && navigate('/register')}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--blue)',
              fontWeight: 700,
              cursor: 'pointer',
              padding: 0,
            }}
          >
            Provision Account
          </button>
        </div>
      )}

      {mode === 'register' && (
        <div style={{ color: 'var(--text-secondary)' }}>
          <span>Already provisioned? </span>
          <button
            type="button"
            onClick={() => navigate && navigate('/login')}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--blue)',
              fontWeight: 700,
              cursor: 'pointer',
              padding: 0,
            }}
          >
            Sign In to Station
          </button>
        </div>
      )}

      {(mode === 'forgot-password' || mode === 'reset-password') && (
        <div style={{ color: 'var(--text-secondary)' }}>
          <span>Remember your credentials? </span>
          <button
            type="button"
            onClick={() => navigate && navigate('/login')}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--blue)',
              fontWeight: 700,
              cursor: 'pointer',
              padding: 0,
            }}
          >
            Return to Login
          </button>
        </div>
      )}

      <div
        style={{
          marginTop: 20,
          paddingTop: 16,
          borderTop: '1px solid var(--card-border)',
          fontSize: 11.5,
          color: 'var(--text-muted)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 12,
        }}
      >
        <span>TLP:AMBER Security Protocols</span>
        <span>•</span>
        <span>FIPS 140-3 Cryptographic Core</span>
      </div>
    </div>
  );
}

export default AuthFooter;
