import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { X, CheckCircle2, Sparkles, ArrowRight, ShieldCheck, Mail, Building, User } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';

export function DemoModal({ isOpen, onClose, navigate }) {
  const { isAuthenticated } = useAuthStore();
  const [name, setName] = useState('Analyst Jaimin');
  const [email, setEmail] = useState('secops@enterprise.corp');
  const [company, setCompany] = useState('Global Cyber Defense Inc.');
  const [submitted, setSubmitted] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <div className="demo-modal-backdrop" onClick={onClose}>
      <motion.div
        className="demo-modal-card"
        onClick={e => e.stopPropagation()}
        initial={{ opacity: 0, scale: 0.95, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 15 }}
        transition={{ duration: 0.2 }}
      >
        <button className="demo-modal-close" onClick={onClose}>
          <X size={18} />
        </button>

        {!submitted ? (
          <>
            <div className="demo-modal-header">
              <div className="modal-icon-wrap">
                <Sparkles size={22} color="var(--blue)" />
              </div>
              <h3 className="modal-title">Request Enterprise Demo</h3>
              <p className="modal-sub">
                See how THREATINTEL correlates 10,000+ alerts into high-priority attack chains in real-time.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="demo-modal-form">
              <div>
                <label className="demo-label">FULL NAME</label>
                <div className="demo-input-row">
                  <User size={15} color="var(--text-muted)" />
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={e => setName(e.target.value)}
                    className="demo-input"
                  />
                </div>
              </div>

              <div>
                <label className="demo-label">WORK EMAIL</label>
                <div className="demo-input-row">
                  <Mail size={15} color="var(--text-muted)" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    className="demo-input"
                  />
                </div>
              </div>

              <div>
                <label className="demo-label">ORGANIZATION / ENTERPRISE</label>
                <div className="demo-input-row">
                  <Building size={15} color="var(--text-muted)" />
                  <input
                    type="text"
                    required
                    value={company}
                    onChange={e => setCompany(e.target.value)}
                    className="demo-input"
                  />
                </div>
              </div>

              <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '12px', marginTop: 8, fontSize: 14 }}>
                <span>Schedule SOC Briefing</span>
                <ArrowRight size={16} />
              </button>
            </form>

            <div className="modal-quick-sandbox">
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Prefer immediate hands-on access?</span>
              <button
                onClick={() => { onClose(); navigate(isAuthenticated ? '/dashboard' : '/signup'); }}
                className="sandbox-quick-link"
              >
                <span>{isAuthenticated ? 'Launch Live SOC Sandbox Now' : 'Create Free Account to Access Platform'}</span>
                <ArrowRight size={13} />
              </button>
            </div>
          </>
        ) : (
          <div className="demo-submitted-content">
            <div className="submitted-icon-wrap">
              <CheckCircle2 size={36} color="var(--low)" />
            </div>
            <h3 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)', marginTop: 12 }}>
              Briefing Request Confirmed
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: 13.5, lineHeight: 1.6, maxWidth: 380, margin: '8px auto 20px' }}>
              Thank you, <strong>{name}</strong>. Our enterprise cybersecurity engineering team will contact <code>{email}</code> shortly to coordinate an environment walkthrough.
            </p>

            <button
              onClick={() => { onClose(); navigate(isAuthenticated ? '/dashboard' : '/signup'); }}
              className="btn btn-primary"
              style={{ width: '100%', padding: '12px' }}
            >
              <span>{isAuthenticated ? 'Explore Live Platform in the Meantime' : 'Register Account to Explore Platform'}</span>
              <ArrowRight size={16} />
            </button>
          </div>
        )}
      </motion.div>
    </div>
  );
}
