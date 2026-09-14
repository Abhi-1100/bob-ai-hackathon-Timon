import React from 'react';
import { Shield, GlobeLock, ArrowLeft, Sun, Moon } from 'lucide-react';
import { BrandLogo } from '../BrandLogo';

export function AuthLayout({
  children,
  navigate,
  theme,
  toggleTheme,
}) {
  return (
    <div className="auth-page-container">
      <div className="auth-split-layout">
        {/* ===================================================================
            LEFT PANEL: ENTERPRISE BRAND & TELEMETRY SHOWCASE
            =================================================================== */}
        <div className="auth-brand-panel">
          <div className="auth-ambient-glow-1" />
          <div className="auth-ambient-glow-2" />

          {/* Top Brand Header */}
          <div className="auth-brand-header">
            <div
              className="auth-logo-badge"
              onClick={() => navigate && navigate('/')}
              role="button"
              tabIndex={0}
            >
              <div className="auth-logo-icon">
                <BrandLogo size={26} />
              </div>
              <div>
                <div className="auth-brand-title">
                  THREAT<span>INTEL</span>
                </div>
              </div>
            </div>

            <div className="auth-clearance-pill">
              <Shield size={14} />
              <span>Secure Platform Access</span>
            </div>
          </div>

          {/* Center Showcase Content */}
          <div className="auth-brand-center">
            <h1 className="auth-brand-headline">
              Smart threat intelligence and alert management.
            </h1>
            <p className="auth-brand-subheadline">
              Connect security events, spot genuine threats faster, and get clear steps to keep your systems safe.
            </p>

            {/* Live Telemetry Chips */}
            <div className="auth-telemetry-grid">
              <div className="auth-telemetry-card">
                <div className="auth-telemetry-num">99.2%</div>
                <div className="auth-telemetry-lbl">Fewer False Alarms</div>
              </div>
              <div className="auth-telemetry-card">
                <div className="auth-telemetry-num">&lt; 3.2s</div>
                <div className="auth-telemetry-lbl">Analysis Speed</div>
              </div>
              <div className="auth-telemetry-card">
                <div className="auth-telemetry-num">100%</div>
                <div className="auth-telemetry-lbl">Standards Aligned</div>
              </div>
            </div>

            {/* Testimonial Quote */}
            <div className="auth-quote-card">
              <p className="auth-quote-text">
                "THREATINTEL transformed how our team handles security alerts. It connects related events and highlights what to fix first, saving us hours every day."
              </p>
              <div className="auth-quote-author">
                <div className="auth-quote-avatar">JD</div>
                <div>
                  <div className="auth-quote-name">Jordan Davies</div>
                  <div className="auth-quote-role">Senior Security Architect</div>
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Security Compliance Strip */}
          <div className="auth-brand-footer">
            <div className="auth-compliance-tags">
              <span className="auth-compliance-item">
                <GlobeLock size={13} color="#38BDF8" /> SOC 2 Type II
              </span>
              <span>•</span>
              <span className="auth-compliance-item">ISO 27001 Certified</span>
              <span>•</span>
              <span className="auth-compliance-item">GDPR Compliant</span>
            </div>
            <div style={{ fontSize: 11, color: '#64748B', fontWeight: 600 }}>
              256-BIT SSL ENCRYPTED
            </div>
          </div>
        </div>

        {/* ===================================================================
            RIGHT PANEL: INTERACTIVE FORM CONTAINER
            =================================================================== */}
        <div className="auth-form-panel">
          <div className="auth-top-actions">
            <button
              onClick={() => navigate && navigate('/')}
              className="auth-back-btn"
            >
              <ArrowLeft size={15} />
              <span>Back to Home</span>
            </button>

            {toggleTheme && (
              <button
                onClick={toggleTheme}
                className="nav-theme-toggle"
                title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
                aria-label="Toggle theme"
              >
                {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
              </button>
            )}
          </div>

          <div className="auth-form-container">
            {children}
          </div>

          <div style={{ height: 24 }} />
        </div>
      </div>
    </div>
  );
}

export default AuthLayout;
