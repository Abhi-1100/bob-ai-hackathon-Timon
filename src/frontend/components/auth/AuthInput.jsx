import React, { forwardRef } from 'react';

export const AuthInput = forwardRef(function AuthInput(
  {
    label,
    icon: Icon,
    error,
    helperText,
    id,
    type = 'text',
    className = '',
    ...props
  },
  ref
) {
  const inputId = id || props.name || Math.random().toString(36).substring(7);

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
        {Icon && (
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
            <Icon size={16} />
          </div>
        )}

        <input
          ref={ref}
          id={inputId}
          type={type}
          style={{
            width: '100%',
            background: 'var(--input-bg)',
            border: error ? '1px solid #EF4444' : '1px solid var(--input-border)',
            borderRadius: 9,
            padding: Icon ? '10px 14px 10px 42px' : '10px 14px',
            color: 'var(--input-text)',
            fontSize: 13.5,
            outline: 'none',
            fontFamily: 'inherit',
            transition: 'border-color 0.15s, box-shadow 0.15s',
            boxSizing: 'border-box',
          }}
          {...props}
        />
      </div>

      {error && (
        <span style={{ fontSize: 11.5, color: '#EF4444', fontWeight: 500, marginTop: 2 }}>
          {error}
        </span>
      )}

      {helperText && !error && (
        <span style={{ fontSize: 11.5, color: 'var(--text-muted)', marginTop: 2 }}>
          {helperText}
        </span>
      )}
    </div>
  );
});

export default AuthInput;
