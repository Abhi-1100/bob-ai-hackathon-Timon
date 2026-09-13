import React from 'react';
import {
  ChevronRight,
  RefreshCw,
  Bell,
  UploadCloud,
  MessageSquare,
  FileText,
  Radio,
  Sun,
  Moon,
  Sparkles
} from 'lucide-react';

export function Topbar({ title, breadcrumb = 'OPERATIONS', onRefresh, navigate, theme, setTheme }) {
  return (
    <header className="topbar">
      <div className="topbar-left">
        <div className="breadcrumbs">
          <span>THREAT INTEL ASSISTANT</span>
          <ChevronRight size={12} />
          <span>{breadcrumb}</span>
        </div>
        <h1 className="topbar-title">{title}</h1>
      </div>

      <div className="topbar-right">
        <div className="status-beacon">
          <span className="pulse-dot" />
          <span>SYSTEM NOMINAL</span>
        </div>

        <button
          className="btn btn-secondary"
          onClick={() => navigate('/')}
          title="Return to Product Landing Page"
          style={{ padding: '6px 12px', borderColor: 'rgba(37, 99, 235, 0.35)' }}
        >
          <Sparkles size={15} color="var(--blue)" />
          <span>Product Overview</span>
        </button>

        {setTheme && (
          <button
            className="btn btn-secondary"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} theme`}
            style={{ padding: '6px 12px' }}
          >
            {theme === 'dark' ? <Sun size={15} color="#FBBF24" /> : <Moon size={15} color="#2563EB" />}
            <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
          </button>
        )}

        {onRefresh && (
          <button className="btn-icon" onClick={onRefresh} title="Sync Live Telemetry">
            <RefreshCw size={16} />
          </button>
        )}

        <button className="btn btn-secondary" onClick={() => navigate('/upload')} style={{ padding: '6px 12px' }}>
          <UploadCloud size={15} color="var(--cyan-bright)" />
          <span>Upload CSV</span>
        </button>

        <button className="btn btn-secondary" onClick={() => navigate('/chat')} style={{ padding: '6px 12px' }}>
          <MessageSquare size={15} color="var(--blue)" />
          <span>Open Chat</span>
        </button>

        <button className="btn btn-primary" onClick={() => navigate('/reports')} style={{ padding: '6px 14px' }}>
          <FileText size={15} />
          <span>Reports</span>
        </button>
      </div>
    </header>
  );
}
