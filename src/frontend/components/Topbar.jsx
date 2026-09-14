import React, { useState, useRef, useEffect } from 'react';
import {
  ChevronRight,
  RefreshCw,
  Sun,
  Moon,
  User,
  Settings,
  LogOut,
  Shield,
  ChevronDown
} from 'lucide-react';
import { useAuthStore } from '../store/authStore';

export function Topbar({ title, breadcrumb = 'OPERATIONS', onRefresh, navigate, theme, setTheme }) {
  const { user, logout, isAuthenticated } = useAuthStore();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    setMenuOpen(false);
    logout();
    if (navigate) navigate('/login');
  };

  const displayName = user?.name || 'User';
  const displayEmail = user?.email || '';
  const displayRole = user?.role || null;

  const initials = (displayName || 'U')
    .split(' ')
    .filter(Boolean)
    .map((n) => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase() || 'U';

  return (
    <header className="topbar">
      <div className="topbar-left">
        <div className="breadcrumbs">
          <span>Threat Intelligence</span>
          <ChevronRight size={11} />
          <span>{breadcrumb}</span>
        </div>
        <h1 className="topbar-title">{title}</h1>
      </div>

      <div className="topbar-right">
        {/* Subtle Live Status */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            padding: '4px 10px',
            borderRadius: 9999,
            background: 'var(--low-bg)',
            border: '1px solid var(--low-border)',
            fontSize: 11.5,
            fontWeight: 700,
            color: 'var(--low-text)',
            letterSpacing: '0.03em',
          }}
        >
          <span className="pulse-dot" />
          <span>LIVE TELEMETRY</span>
        </div>

        <div style={{ width: 1, height: 18, background: 'var(--card-border)' }} />

        {/* Sync Refresh Icon */}
        {onRefresh && (
          <button
            onClick={onRefresh}
            title="Refresh Telemetry"
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              border: '1px solid var(--card-border)',
              background: 'var(--card)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              transition: 'all 0.15s',
            }}
          >
            <RefreshCw size={14} />
          </button>
        )}

        {/* Theme Toggle Icon */}
        {setTheme && (
          <button
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              border: '1px solid var(--card-border)',
              background: 'var(--card)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              transition: 'all 0.15s',
            }}
          >
            {theme === 'dark' ? <Sun size={15} color="#FBBF24" /> : <Moon size={15} color="#2563EB" />}
          </button>
        )}

        <div style={{ width: 1, height: 18, background: 'var(--card-border)' }} />

        {/* User Profile Menu */}
        <div style={{ position: 'relative' }} ref={menuRef}>
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              background: 'var(--card)',
              border: '1px solid var(--card-border)',
              borderRadius: 24,
              padding: '4px 10px 4px 4px',
              cursor: 'pointer',
              color: 'var(--text-primary)',
              transition: 'border-color 0.15s, background 0.15s',
            }}
            title="User Profile"
          >
            <div
              style={{
                width: 28,
                height: 28,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #1E40AF, #2563EB)',
                color: '#FFFFFF',
                fontSize: 11,
                fontWeight: 800,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 2px 6px rgba(37, 99, 235, 0.3)',
              }}
            >
              {initials}
            </div>
            <span style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--text-primary)' }}>{displayName}</span>
            <ChevronDown size={13} color="var(--text-muted)" />
          </button>

          {/* User Dropdown */}
          {menuOpen && (
            <div
              style={{
                position: 'absolute',
                top: 'calc(100% + 8px)',
                right: 0,
                width: 220,
                background: 'var(--card)',
                border: '1px solid var(--card-border)',
                borderRadius: 12,
                padding: '8px',
                boxShadow: '0 12px 32px -4px rgba(15, 23, 42, 0.15), 0 4px 12px -2px rgba(15, 23, 42, 0.08)',
                zIndex: 1000,
                animation: 'dropdownFadeIn 0.15s ease',
              }}
            >
              <div
                style={{
                  padding: '8px 10px 10px',
                  borderBottom: '1px solid var(--card-border)',
                  marginBottom: 6,
                }}
              >
                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
                  {displayName}
                </div>
                {displayEmail && (
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2, wordBreak: 'break-all' }}>
                    {displayEmail}
                  </div>
                )}
                {displayRole && (
                  <div
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 4,
                      marginTop: 6,
                      padding: '2px 8px',
                      borderRadius: 9999,
                      background: 'rgba(37, 99, 235, 0.08)',
                      fontSize: 10.5,
                      fontWeight: 600,
                      color: 'var(--blue)',
                    }}
                  >
                    <Shield size={11} />
                    <span>{displayRole}</span>
                  </div>
                )}
              </div>

              <button
                onClick={() => {
                  setMenuOpen(false);
                  navigate('/settings');
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  width: '100%',
                  padding: '8px 10px',
                  border: 'none',
                  background: 'none',
                  color: 'var(--text-secondary)',
                  fontSize: 12.5,
                  fontWeight: 500,
                  borderRadius: 6,
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'background 0.15s',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-tertiary)')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'none')}
              >
                <User size={14} />
                <span>Profile</span>
              </button>

              <button
                onClick={() => {
                  setMenuOpen(false);
                  navigate('/settings');
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  width: '100%',
                  padding: '8px 10px',
                  border: 'none',
                  background: 'none',
                  color: 'var(--text-secondary)',
                  fontSize: 12.5,
                  fontWeight: 500,
                  borderRadius: 6,
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'background 0.15s',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-tertiary)')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'none')}
              >
                <Settings size={14} />
                <span>Settings</span>
              </button>

              <div style={{ height: 1, background: 'var(--card-border)', margin: '4px 0' }} />

              <button
                onClick={handleLogout}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  width: '100%',
                  padding: '8px 10px',
                  border: 'none',
                  background: 'none',
                  color: '#EF4444',
                  fontSize: 12.5,
                  fontWeight: 600,
                  borderRadius: 6,
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'background 0.15s',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(239, 68, 68, 0.08)')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'none')}
              >
                <LogOut size={14} />
                <span>Sign Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
