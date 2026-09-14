import React from 'react';
import { BrandLogo } from '../BrandLogo';
import { Code2, Shield, Terminal, BookOpen, Mail, ExternalLink, ArrowUp } from 'lucide-react';

export function LandingFooter({ navigate }) {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <footer className="landing-footer">
      <div className="landing-container">
        <div className="footer-top-grid">
          {/* Brand info */}
          <div className="footer-brand-col">
            <div className="footer-brand" onClick={scrollToTop}>
              <div className="brand-icon">
                <BrandLogo size={22} />
              </div>
              <div>
                <div className="brand-title">
                  THREAT<span>INTEL</span>
                </div>
                <span className="brand-subtitle">CORRELATION & PRIORITISATION</span>
              </div>
            </div>
            <p className="footer-bio">
              Next-generation Threat Intelligence Correlation & Alert Prioritisation Assistant built for modern SOC teams, incident responders, and threat hunters.
            </p>
            <div className="footer-badge-pill">
              <Shield size={13} color="var(--low)" />
              <span>Production Grade Security Architecture</span>
            </div>
          </div>

          {/* Quick Links Column 1: Platform Modules */}
          <div className="footer-nav-col">
            <h5 className="footer-col-title">Platform Modules</h5>
            <ul className="footer-links-list">
              <li><button onClick={() => navigate('/dashboard')} className="footer-link">SOC Command Center</button></li>
              <li><button onClick={() => navigate('/upload')} className="footer-link">Alert Ingestion & Parser</button></li>
              <li><button onClick={() => navigate('/attack-chains')} className="footer-link">Attack Chain Correlation</button></li>
              <li><button onClick={() => navigate('/mitre')} className="footer-link">MITRE ATT&CK Matrix</button></li>
              <li><button onClick={() => navigate('/risk')} className="footer-link">Risk Prioritisation Queue</button></li>
              <li><button onClick={() => navigate('/recommendations')} className="footer-link">Mitigation Playbooks</button></li>
            </ul>
          </div>

          {/* Quick Links Column 2: Advanced Capabilities */}
          <div className="footer-nav-col">
            <h5 className="footer-col-title">Advanced AI</h5>
            <ul className="footer-links-list">
              <li><button onClick={() => navigate('/reports')} className="footer-link">Executive BLUF Reports</button></li>
              <li><button onClick={() => navigate('/chat')} className="footer-link">AI Threat Copilot (RAG)</button></li>
              <li><button onClick={() => navigate('/analytics')} className="footer-link">Cross-Domain Analytics</button></li>
              <li><button onClick={() => navigate('/settings')} className="footer-link">Vector DB & API Config</button></li>
              <li><button onClick={() => navigate('/login')} className="footer-link">Operator Sign In</button></li>
              <li><button onClick={() => navigate('/signup')} className="footer-link">Provision Account (Sign Up)</button></li>
            </ul>
          </div>

          {/* Quick Links Column 3: Documentation & Links */}
          <div className="footer-nav-col">
            <h5 className="footer-col-title">Documentation & Source</h5>
            <ul className="footer-links-list">
              <li>
                <a href="https://github.com" target="_blank" rel="noreferrer" className="footer-link ext">
                  <Code2 size={13} />
                  <span>GitHub Repository</span>
                </a>
              </li>
              <li>
                <a href="#docs" onClick={(e) => { e.preventDefault(); navigate('/settings'); }} className="footer-link ext">
                  <BookOpen size={13} />
                  <span>Architecture Docs</span>
                </a>
              </li>
              <li>
                <a href="#api" onClick={(e) => { e.preventDefault(); alert('FastAPI Swagger available at http://localhost:8000/docs'); }} className="footer-link ext">
                  <Terminal size={13} />
                  <span>FastAPI Swagger Spec</span>
                </a>
              </li>
              <li>
                <a href="#contact" onClick={(e) => { e.preventDefault(); alert('Inquiries: soc-team@d2threatintel.internal'); }} className="footer-link ext">
                  <Mail size={13} />
                  <span>SOC Operations Desk</span>
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Footer Bottom Strip */}
        <div className="footer-bottom-strip">
          <div className="footer-copyright">
            © {new Date().getFullYear()} THREATINTEL Correlation & Alert Prioritisation Assistant. All rights reserved.
          </div>
          <div className="footer-compliance-tags">
            <span>TLP:AMBER Protocol</span>
            <span>·</span>
            <span>MITRE ATT&CK® v14.1</span>
            <span>·</span>
            <span>NIST SP 800-61</span>
          </div>
          <button onClick={scrollToTop} className="back-to-top-btn" title="Back to top">
            <ArrowUp size={15} />
            <span>Top</span>
          </button>
        </div>
      </div>
    </footer>
  );
}
