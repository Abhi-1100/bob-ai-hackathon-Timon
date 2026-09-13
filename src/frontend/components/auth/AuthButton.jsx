import React from 'react';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';

export function AuthButton({
  children,
  loading = false,
  disabled = false,
  variant = 'primary',
  type = 'submit',
  icon: Icon,
  className = '',
  onClick,
  ...props
}) {
  const getStyles = () => {
    switch (variant) {
      case 'secondary':
        return {
          background: 'var(--card)',
          border: '1px solid var(--card-border)',
          color: 'var(--text-primary)',
        };
      case 'evaluator':
        return {
          background: 'rgba(37, 99, 235, 0.08)',
          border: '1px solid rgba(37, 99, 235, 0.35)',
          color: 'var(--blue)',
        };
      case 'primary':
      default:
        return {
          background: '#0F172A',
          border: 'none',
          color: '#FFFFFF',
          boxShadow: '0 2px 10px rgba(15, 23, 42, 0.15)',
        };
    }
  };

  return (
    <motion.button
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      whileHover={{ y: disabled || loading ? 0 : -1 }}
      whileTap={{ scale: disabled || loading ? 1 : 0.98 }}
      style={{
        width: '100%',
        padding: '11px 16px',
        borderRadius: 9,
        fontSize: 14,
        fontWeight: 600,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
        cursor: disabled || loading ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.6 : 1,
        fontFamily: 'inherit',
        transition: 'all 0.15s ease',
        ...getStyles(),
      }}
      className={`auth-btn ${className}`}
      {...props}
    >
      {loading ? (
        <>
          <Loader2 size={16} className="auth-spinner" style={{ animation: 'spin 1s linear infinite' }} />
          <span>Processing…</span>
        </>
      ) : (
        <>
          {Icon && <Icon size={16} />}
          <span>{children}</span>
        </>
      )}
    </motion.button>
  );
}

export default AuthButton;
