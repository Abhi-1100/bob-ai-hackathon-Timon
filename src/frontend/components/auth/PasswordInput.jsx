import React, { forwardRef, useState } from 'react';
import { Lock, Eye, EyeOff } from 'lucide-react';

export const PasswordInput = forwardRef(function PasswordInput(
  {
    label = 'Password',
    error,
    showStrengthMeter = false,
    value,
    id,
    className = '',
    ...props
  },
  ref
) {
  const [show, setShow] = useState(false);
  const inputId = id || props.name || 'password-input';

  // Calculate strength if value is passed
  const getStrength = (val) => {
    if (!val) return { score: 0, label: 'Password required' };
    let score = 0;
    if (val.length >= 8) score++;
    if (/[A-Z]/.test(val)) score++;
    if (/[0-9]/.test(val)) score++;
    if (/[^A-Za-z0-9]/.test(val)) score++;
    if (score <= 1) return { score: 1, label: 'Weak (needs 8+ chars & numbers)' };
    if (score <= 3) return { score: 2, label: 'Medium (add symbols for enterprise grade)' };
    return { score: 3, label: 'Strong enterprise-grade passphrase' };
  };

  const strength = showStrengthMeter ? getStrength(value || '') : null;

  return (
    <div className={`auth-input-group ${className}`} style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {label && (
        <label
          htmlFor={inputId}
          style={{
            fontSize: 12,
            fontWeight: 700,
            color: 'var(--text-secondary)',
            letterSpacing: '0.04em',
            textTransform: 'uppercase',
          }}
        >
          {label}
        </label>
      )}

      <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
        <div
          style={{
            position: 'absolute',
            left: 14,
            color: error ? '#EF4444' : 'var(--text-muted)',
            pointerEvents: 'none',
            display: 'flex',
            alignItems: 'center',
          }}
        >
          <Lock size={16} />
        </div>

        <input
          ref={ref}
          id={inputId}
          type={show ? 'text' : 'password'}
          value={value}
          style={{
            width: '100%',
            background: 'var(--input-bg)',
            border: error ? '1px solid #EF4444' : '1px solid var(--input-border)',
            borderRadius: 9,
            padding: '10px 42px 10px 42px',
            color: 'var(--input-text)',
            fontSize: 13.5,
            outline: 'none',
            fontFamily: 'inherit',
            transition: 'border-color 0.15s, box-shadow 0.15s',
            boxSizing: 'border-box',
          }}
          {...props}
        />

        <button
          type="button"
          onClick={() => setShow(!show)}
          style={{
            position: 'absolute',
            right: 12,
            background: 'none',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            padding: 4,
            display: 'flex',
            alignItems: 'center',
          }}
          aria-label={show ? 'Hide password' : 'Show password'}
        >
          {show ? <EyeOff size={16} /> : <Eye size={16} />}
        </button>
      </div>

      {showStrengthMeter && value && (
        <div style={{ marginTop: 4 }}>
          <div style={{ display: 'flex', gap: 4 }}>
            <div
              style={{
                height: 4,
                flex: 1,
                borderRadius: 2,
                background: strength.score >= 1 ? '#EF4444' : 'var(--card-border)',
                transition: 'background 0.2s',
              }}
            />
            <div
              style={{
                height: 4,
                flex: 1,
                borderRadius: 2,
                background: strength.score >= 2 ? '#F59E0B' : 'var(--card-border)',
                transition: 'background 0.2s',
              }}
            />
            <div
              style={{
                height: 4,
                flex: 1,
                borderRadius: 2,
                background: strength.score >= 3 ? '#10B981' : 'var(--card-border)',
                transition: 'background 0.2s',
              }}
            />
          </div>
          <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', marginTop: 4, display: 'block' }}>
            {strength.label}
          </span>
        </div>
      )}

      {error && (
        <span style={{ fontSize: 11.5, color: '#EF4444', fontWeight: 500, marginTop: 2 }}>
          {error}
        </span>
      )}
    </div>
  );
});

export default PasswordInput;
