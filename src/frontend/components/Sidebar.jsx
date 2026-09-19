import React from 'react';
import {
  LayoutDashboard,
  Network,
  ShieldAlert,
  Flame,
  Lightbulb,
  FileText,
  MessageSquare,
  BarChart3,
  Settings,
  PanelLeftClose,
  PanelLeftOpen,
  Lock
} from 'lucide-react';
import { BrandLogo } from './BrandLogo';
import { useAuthStore } from '../store/authStore';
import { useToast } from './auth/Toast';

export function Sidebar({ currentRoute, navigate, collapsed, setCollapsed, hasUploaded = true }) {
  const { user } = useAuthStore();
  const { showToast } = useToast();
  const displayName = user?.name || 'Security Analyst';
  const initials = (displayName || 'SA')
    .split(' ')
    .filter(Boolean)
    .map((n) => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase() || 'SA';
  const navItems = [
    { route: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, requiresUpload: true },
    { route: '/attack-chains', label: 'Attack Chains', icon: Network, requiresUpload: true },
    { route: '/mitre', label: 'MITRE Analysis', icon: ShieldAlert, requiresUpload: true },
    { route: '/risk', label: 'Risk Prioritization', icon: Flame, requiresUpload: true },
    { route: '/recommendations', label: 'Recommendations', icon: Lightbulb, requiresUpload: true },
    { route: '/reports', label: 'Intelligence Reports', icon: FileText, requiresUpload: true },
    { route: '/chat', label: 'AI Analyst Chat', icon: MessageSquare, requiresUpload: true },
    { route: '/analytics', label: 'Analytics', icon: BarChart3, requiresUpload: true },
    { route: '/settings', label: 'Settings', icon: Settings, requiresUpload: false },
  ];

  const handleNavClick = (item) => {
    if (item.requiresUpload && !hasUploaded) {
      showToast('Please upload an alert CSV or load test data to unlock the platform.', 'warning');
      navigate('/upload');
      return;
    }
    navigate(item.route);
  };

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <div className="brand-wrap">
          <div className="brand-icon">
            <BrandLogo size={24} />
          </div>
          {!collapsed && (
            <div>
              <div className="brand-title">
                THREAT <span>INTEL</span>
              </div>
              <span className="brand-subtitle">THREAT INTELLIGENCE PLATFORM</span>
            </div>
          )}
        </div>
        <button
          className="collapse-btn"
          onClick={() => setCollapsed(!collapsed)}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
        </button>
      </div>

      <div className="sidebar-section-title">OPERATIONS CONSOLE</div>

      <nav className="nav-list">
        {navItems.map(item => {
          const Icon = item.icon;
          const isActive = currentRoute === item.route || (item.route === '/attack-chains' && currentRoute.startsWith('/incident'));
          const isLocked = item.requiresUpload && !hasUploaded;

          return (
            <button
              key={item.route}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => handleNavClick(item)}
              title={collapsed ? (isLocked ? `${item.label} (Upload Required)` : item.label) : undefined}
              style={{
                opacity: isLocked ? 0.65 : 1,
              }}
            >
              <Icon size={18} />
              <span className="nav-text">{item.label}</span>
              {isLocked && !collapsed && (
                <Lock size={12} style={{ marginLeft: 'auto', color: '#F59E0B' }} />
              )}
              {item.route === '/upload' && !hasUploaded && !collapsed && (
                <span
                  className="nav-badge"
                  style={{
                    marginLeft: 'auto',
                    background: 'rgba(6, 182, 212, 0.15)',
                    color: 'var(--cyan-bright)',
                    border: '1px solid rgba(6, 182, 212, 0.3)',
                    fontSize: 10,
                    fontWeight: 700,
                    padding: '1px 6px',
                    borderRadius: 4,
                  }}
                >
                  Step 1
                </span>
              )}
              {item.badge && <span className="nav-badge">{item.badge}</span>}
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="operator-badge">
          <div className="operator-avatar">{initials}</div>
          {!collapsed && (
            <div className="operator-meta">
              <div className="operator-name">{displayName}</div>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
