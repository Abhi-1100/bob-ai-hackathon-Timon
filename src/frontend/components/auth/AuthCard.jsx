import React from 'react';
import { motion } from 'framer-motion';

export function AuthCard({ children, className = "" }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16, scale: 0.99 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
      className={`auth-card ${className}`}
      style={{
        width: '100%',
        maxWidth: 480,
        margin: '0 auto',
        background: 'var(--card)',
        border: '1px solid var(--card-border)',
        borderRadius: '16px',
        padding: '24px 28px',
        boxShadow: '0 20px 45px -12px rgba(0, 0, 0, 0.1), 0 0 0 1px rgba(37, 99, 235, 0.08)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Top Cyber Accents */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 3,
          background: 'linear-gradient(90deg, #1E40AF 0%, #2563EB 50%, #38BDF8 100%)',
        }}
      />
      {children}
    </motion.div>
  );
}

export default AuthCard;
