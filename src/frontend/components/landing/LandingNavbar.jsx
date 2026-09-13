import React from 'react';
import { BrandLogo } from '../BrandLogo';
import { ArrowRight, Shield, Moon, Sun, Sparkles } from 'lucide-react';

export function LandingNavbar({ navigate, theme, toggleTheme, onRequestDemo }) {
  const scrollTo = (id) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <header className="landing-navbar">
      <div className="landing-nav-container">
        {/* Brand */}
        <div className="landing-brand" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
          <div className="brand-icon">
            <BrandLogo size={24} />
          </div>
          <div>
            <div className="brand-title">
              D2 <span>THREAT INTEL</span>
            </div>
            <span className="brand-subtitle">CORRELATION & PRIORITISATION</span>
          </div>
        </div>

        {/* Nav Links */}
        <nav className="landing-nav-links">
          <button onClick={() => scrollTo('features')} className="nav-link-btn">Features</button>
          <button onClick={() => scrollTo('how-it-works')} className="nav-link-btn">How It Works</button>
          <button onClick={() => scrollTo('platform')} className="nav-link-btn">Platform Preview</button>
          <button onClick={() => scrollTo('chat-copilot')} className="nav-link-btn">AI Copilot</button>
          <button onClick={() => scrollTo('architecture')} className="nav-link-btn">Architecture</button>
          <button onClick={() => scrollTo('benefits')} className="nav-link-btn">Why D2</button>
        </nav>

        {/* Action CTAs */}
        <div className="landing-nav-actions">
          <button
            onClick={toggleTheme}
            className="theme-toggle-btn"
            title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
          >
            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          </button>

          <button
            onClick={() => navigate('/login')}
            className="btn btn-secondary"
            style={{ padding: '7px 14px', fontSize: 13 }}
          >
            Sign In
          </button>

          <button
            onClick={onRequestDemo}
            className="btn btn-secondary"
            style={{ padding: '7px 14px', fontSize: 13, borderColor: 'rgba(37, 99, 235, 0.4)' }}
          >
            <Sparkles size={14} color="var(--blue)" />
            <span>Request Demo</span>
          </button>

          <button
            onClick={() => navigate('/dashboard')}
            className="btn btn-primary"
            style={{ padding: '7px 16px', fontSize: 13 }}
          >
            <span>Launch Console</span>
            <ArrowRight size={14} />
          </button>
        </div>
      </div>
    </header>
  );
}
