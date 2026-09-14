import React, { useState, useRef, useEffect } from 'react';
import { BrandLogo } from '../BrandLogo';
import { ChevronDown, ChevronRight, Moon, Sun, Shield, Sparkles, Activity, Layers } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';

export function LandingNavbar({ navigate, theme, toggleTheme, onRequestDemo }) {
  const { isAuthenticated } = useAuthStore();
  const [solutionsOpen, setSolutionsOpen] = useState(false);
  const dropdownRef = useRef(null);

  const scrollTo = (id) => {
    setSolutionsOpen(false);
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setSolutionsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="landing-navbar-wrapper">
      <div className="landing-navbar-pill">
        {/* Left: Brand Logo & Title */}
        <div
          className="nav-brand-simple"
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          role="button"
          tabIndex={0}
        >
          <div className="nav-brand-icon-box">
            <BrandLogo size={22} />
          </div>
          <span className="nav-brand-text">THREATINTEL</span>
        </div>

        {/* Center: Navigation Links */}
        <nav className="nav-center-links">
          {/* Solutions Dropdown */}
          <div className="nav-dropdown-wrapper" ref={dropdownRef}>
            <button
              onClick={() => setSolutionsOpen(!solutionsOpen)}
              className={`nav-simple-link ${solutionsOpen ? 'active' : ''}`}
            >
              <span>Solutions</span>
              <ChevronDown size={14} className={`dropdown-chevron ${solutionsOpen ? 'rotated' : ''}`} />
            </button>

            {solutionsOpen && (
              <div className="nav-dropdown-menu">
                <button onClick={() => scrollTo('features')} className="dropdown-item">
                  <div className="dropdown-item-icon">
                    <Activity size={15} color="#2563EB" />
                  </div>
                  <div>
                    <div className="dropdown-item-title">Alert Correlation</div>
                    <div className="dropdown-item-desc">Transform thousands of alerts into attack chains</div>
                  </div>
                </button>

                <button onClick={() => scrollTo('features')} className="dropdown-item">
                  <div className="dropdown-item-icon">
                    <Shield size={15} color="#059669" />
                  </div>
                  <div>
                    <div className="dropdown-item-title">MITRE ATT&CK Mapping</div>
                    <div className="dropdown-item-desc">Automated adversary technique classification</div>
                  </div>
                </button>

                <button onClick={() => scrollTo('features')} className="dropdown-item">
                  <div className="dropdown-item-icon">
                    <Layers size={15} color="#EA580C" />
                  </div>
                  <div>
                    <div className="dropdown-item-title">Risk Scoring Engine</div>
                    <div className="dropdown-item-desc">Deterministic 0-100 severity prioritization</div>
                  </div>
                </button>

                <button onClick={() => scrollTo('chat-copilot')} className="dropdown-item">
                  <div className="dropdown-item-icon">
                    <Sparkles size={15} color="#7C3AED" />
                  </div>
                  <div>
                    <div className="dropdown-item-title">AI Analyst Copilot</div>
                    <div className="dropdown-item-desc">Vector-grounded intelligence Q&A</div>
                  </div>
                </button>
              </div>
            )}
          </div>

          <button onClick={() => scrollTo('benefits')} className="nav-simple-link">
            Enterprise
          </button>

          <button onClick={() => scrollTo('how-it-works')} className="nav-simple-link">
            <span>Intelligence</span>
            <span className="nav-pro-badge">PRO</span>
          </button>

          <button
            onClick={() => {
              if (isAuthenticated) {
                navigate('/dashboard');
              } else {
                navigate('/login');
              }
            }}
            className="nav-simple-link nav-live-app"
          >
            <span>Live App</span>
            <span className="live-dot" />
          </button>

          <button onClick={() => scrollTo('platform')} className="nav-simple-link">
            Pricing
          </button>
        </nav>

        {/* Right: Actions */}
        <div className="nav-right-actions">
          <button
            onClick={toggleTheme}
            className="nav-theme-toggle"
            title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
          </button>

          <button onClick={() => navigate('/login')} className="nav-signin-btn">
            Sign in
          </button>

          <button onClick={() => navigate('/signup')} className="nav-get-started-btn">
            <span>Get started</span>
            <ChevronRight size={14} />
          </button>
        </div>
      </div>
    </header>
  );
}

