import React from 'react';
import {
  ChevronRight,
  RefreshCw,
  Bell,
  UploadCloud,
  MessageSquare,
  FileText,
  Radio
} from 'lucide-react';

export function Topbar({ title, breadcrumb = 'OPERATIONS', onRefresh, navigate }) {
  return (
    <header className="topbar">
      <div className="topbar-left">
        <div className="breadcrumbs">
          <span>SENTINEL FORGE</span>
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
          <MessageSquare size={15} color="#38BDF8" />
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
