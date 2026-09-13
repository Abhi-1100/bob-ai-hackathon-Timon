import React, { useState } from 'react';
import { Radar, Shield, Lock, Mail, ArrowRight, CheckCircle2, Eye, EyeOff } from 'lucide-react';

export function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('analyst@sentinelforge.mil');
  const [password, setPassword] = useState('••••••••••••');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      onLogin();
    }, 400);
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'radial-gradient(circle at center, rgba(6, 182, 212, 0.08) 0%, rgba(10, 15, 31, 1) 70%)',
      padding: 20
    }}>
      <div style={{
        width: '100%',
        maxWidth: 440,
        background: '#131A2A',
        border: '1px solid #1E293B',
        borderRadius: 16,
        padding: '36px 32px',
        boxShadow: '0 20px 50px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(56, 189, 248, 0.15)',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Top Glowing Strip */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 3,
          background: 'linear-gradient(90deg, #0284C7, #06B6D4, #3B82F6)'
        }} />

        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{
            width: 48,
            height: 48,
            borderRadius: 12,
            background: 'linear-gradient(135deg, #0284C7, #06B6D4)',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            boxShadow: '0 0 20px rgba(6, 182, 212, 0.4)',
            marginBottom: 14
          }}>
            <Radar size={28} />
          </div>
          <h2 style={{ fontSize: 20, fontWeight: 800, color: '#F8FAFC', letterSpacing: '0.04em' }}>
            SENTINEL<span style={{ color: '#38BDF8' }}>FORGE</span>
          </h2>
          <p style={{ fontSize: 12, color: '#64748B', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', marginTop: 4 }}>
            Threat Intelligence Operations Console
          </p>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            marginTop: 10,
            padding: '3px 10px',
            background: 'rgba(6, 182, 212, 0.08)',
            border: '1px solid rgba(6, 182, 212, 0.25)',
            borderRadius: 9999,
            fontSize: 11,
            color: '#38BDF8'
          }}>
            <Shield size={12} />
            <span>Restricted Access — Level 3 Clearance</span>
          </div>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <div>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#94A3B8', marginBottom: 6 }}>
              OPERATOR ID / EMAIL
            </label>
            <div style={{ position: 'relative' }}>
              <Mail size={16} color="#64748B" style={{ position: 'absolute', left: 14, top: 12 }} />
              <input
                type="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                style={{
                  width: '100%',
                  background: '#0D1527',
                  border: '1px solid #1E293B',
                  borderRadius: 8,
                  padding: '10px 14px 10px 40px',
                  color: '#F8FAFC',
                  fontSize: 13.5,
                  outline: 'none',
                  fontFamily: 'var(--font-mono)'
                }}
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#94A3B8', marginBottom: 6 }}>
              AUTHENTICATION TOKEN / PASSWORD
            </label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} color="#64748B" style={{ position: 'absolute', left: 14, top: 12 }} />
              <input
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={e => setPassword(e.target.value)}
                style={{
                  width: '100%',
                  background: '#0D1527',
                  border: '1px solid #1E293B',
                  borderRadius: 8,
                  padding: '10px 40px 10px 40px',
                  color: '#F8FAFC',
                  fontSize: 13.5,
                  outline: 'none',
                  fontFamily: 'var(--font-mono)'
                }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{ position: 'absolute', right: 14, top: 12, background: 'none', border: 'none', color: '#64748B', cursor: 'pointer' }}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 12 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#94A3B8', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={e => setRememberMe(e.target.checked)}
                style={{ accentColor: '#06B6D4' }}
              />
              <span>Remember station</span>
            </label>
            <a href="#forgot" onClick={(e) => { e.preventDefault(); alert('Station credentials managed by SOC Security Officer.'); }} style={{ color: '#38BDF8' }}>
              Reset credentials?
            </a>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
            style={{ width: '100%', padding: '12px', marginTop: 6, fontSize: 14 }}
          >
            {loading ? 'Authenticating Station…' : (
              <>
                <span>Enter Operations Console</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>

        <div style={{ marginTop: 20, paddingTop: 18, borderTop: '1px solid #1E293B', textAlign: 'center' }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onLogin}
            style={{ width: '100%', fontSize: 12.5 }}
          >
            <CheckCircle2 size={15} color="#22C55E" />
            <span>Instant Demo Access (Judge / Evaluator)</span>
          </button>
        </div>
      </div>
    </div>
  );
}
