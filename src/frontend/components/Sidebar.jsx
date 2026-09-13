import React from 'react';
import {
  LayoutDashboard,
  UploadCloud,
  Network,
  ShieldAlert,
  Flame,
  Lightbulb,
  FileText,
  MessageSquare,
  BarChart3,
  Settings,
  Radar,
  PanelLeftClose,
  PanelLeftOpen,
  LogOut
} from 'lucide-react';

export function Sidebar({ currentRoute, navigate, collapsed, setCollapsed }) {
  const navItems = [
    { route: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { route: '/upload', label: 'Upload Alerts', icon: UploadCloud },
    { route: '/attack-chains', label: 'Attack Chains', icon: Network },
    { route: '/mitre', label: 'MITRE Analysis', icon: ShieldAlert },
    { route: '/risk', label: 'Risk Prioritization', icon: Flame },
    { route: '/recommendations', label: 'Recommendations', icon: Lightbulb },
    { route: '/reports', label: 'Intelligence Reports', icon: FileText },
    { route: '/chat', label: 'AI Analyst Chat', icon: MessageSquare },
    { route: '/analytics', label: 'Analytics', icon: BarChart3 },
    { route: '/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <div className="brand-wrap">
          <div className="brand-icon">
            <Radar size={22} />
          </div>
          {!collapsed && (
            <div>
              <div className="brand-title">
                THREAT<span>INTEL</span>
              </div>
              <span className="brand-subtitle">CORRELATION & PRIORITIZATION</span>
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
          return (
            <button
              key={item.route}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => navigate(item.route)}
              title={collapsed ? item.label : undefined}
            >
              <Icon size={18} />
              <span className="nav-text">{item.label}</span>
              {item.badge && <span className="nav-badge">{item.badge}</span>}
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="operator-badge">
          <div className="operator-avatar">SO</div>
          {!collapsed && (
            <div className="operator-meta">
              <div className="operator-name">Analyst Jaimin</div>
              <div className="operator-role">Level 03 · TimonTrack</div>
            </div>
          )}
        </div>
        <button
          className="nav-item"
          onClick={() => navigate('/login')}
          style={{ color: '#94A3B8' }}
          title={collapsed ? 'Sign Out' : undefined}
        >
          <LogOut size={16} />
          <span className="nav-text">Sign Out</span>
        </button>
      </div>
    </aside>
  );
}
