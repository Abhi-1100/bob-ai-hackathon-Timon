import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';
import './landing.css';
import './auth.css';

// Toast System
import { ToastProvider } from './components/auth/Toast';

// Auth State Store
import { useAuthStore } from './store/authStore';

// Components
import { Sidebar } from './components/Sidebar';
import { Topbar } from './components/Topbar';

// Public & Marketing Pages
import { LandingPage } from './pages/LandingPage';

// Authentication Pages
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { ForgotPasswordPage } from './pages/ForgotPasswordPage';
import { ResetPasswordPage } from './pages/ResetPasswordPage';

// Operational SOC Pages
import { DashboardPage } from './pages/DashboardPage';
import { UploadPage } from './pages/UploadPage';
import { AttackChainsPage } from './pages/AttackChainsPage';
import { IncidentDetailPage } from './pages/IncidentDetailPage';
import { MitrePage } from './pages/MitrePage';
import { RiskPage } from './pages/RiskPage';
import { RecommendationsPage } from './pages/RecommendationsPage';
import { ReportsPage } from './pages/ReportsPage';
import { ChatPage } from './pages/ChatPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { SettingsPage } from './pages/SettingsPage';

function App() {
  const [currentRoute, setCurrentRoute] = useState(() => {
    return window.location.pathname || '/';
  });
  const [collapsed, setCollapsed] = useState(false);
  const [selectedChainId, setSelectedChainId] = useState('AC001');
  const [selectedReportId, setSelectedReportId] = useState(null);

  const { isAuthenticated } = useAuthStore();

  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('sentinel_theme') || 'light';
  });

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    document.body.setAttribute('data-theme', theme);
    localStorage.setItem('sentinel_theme', theme);
  }, [theme]);

  // Sync route on popstate (browser back/forward buttons)
  useEffect(() => {
    const handlePop = () => {
      setCurrentRoute(window.location.pathname || '/');
    };
    window.addEventListener('popstate', handlePop);
    return () => window.removeEventListener('popstate', handlePop);
  }, []);

  const navigate = (route) => {
    window.history.pushState({}, '', route);
    setCurrentRoute(route);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const openIncident = (chainId) => {
    setSelectedChainId(chainId);
    navigate(`/incident/${chainId}`);
  };

  const openReport = (reportId) => {
    setSelectedReportId(reportId);
    navigate(`/reports/${reportId}`);
  };

  // 1. Landing Page has its own full-screen layout
  if (currentRoute === '/' || currentRoute === '/landing') {
    return (
      <LandingPage
        navigate={navigate}
        theme={theme}
        toggleTheme={toggleTheme}
      />
    );
  }

  // 2. Authentication Pages (Public Accessible)
  if (currentRoute === '/login' || currentRoute === '/signin') {
    return (
      <LoginPage
        navigate={navigate}
        onLogin={() => navigate('/dashboard')}
        theme={theme}
        toggleTheme={toggleTheme}
      />
    );
  }

  if (currentRoute === '/register' || currentRoute === '/signup') {
    return (
      <RegisterPage
        navigate={navigate}
        theme={theme}
        toggleTheme={toggleTheme}
      />
    );
  }

  if (currentRoute === '/forgot-password') {
    return (
      <ForgotPasswordPage
        navigate={navigate}
        theme={theme}
        toggleTheme={toggleTheme}
      />
    );
  }

  if (currentRoute.startsWith('/reset-password')) {
    return (
      <ResetPasswordPage
        navigate={navigate}
        theme={theme}
        toggleTheme={toggleTheme}
      />
    );
  }

  // 3. Route Guard: All subsequent routes (/dashboard, /upload, /attack-chains, etc.) require authentication
  if (!isAuthenticated) {
    return (
      <LoginPage
        navigate={navigate}
        onLogin={() => navigate(currentRoute)}
        theme={theme}
        toggleTheme={toggleTheme}
      />
    );
  }

  // Determine active view & Topbar title
  let content = null;
  let pageTitle = 'Threat Intelligence Dashboard';
  let breadcrumb = 'OPERATIONS';

  if (currentRoute.startsWith('/incident/')) {
    const chainId = currentRoute.split('/')[2] || selectedChainId;
    pageTitle = `Incident Investigation: ${chainId}`;
    breadcrumb = 'INCIDENT DETAIL';
    content = (
      <IncidentDetailPage
        chainId={chainId}
        onBack={() => navigate('/attack-chains')}
        navigate={navigate}
      />
    );
  } else if (currentRoute.startsWith('/reports/')) {
    const reportId = currentRoute.split('/')[2] || selectedReportId;
    pageTitle = `Executive Briefing: ${reportId}`;
    breadcrumb = 'COMMAND BRIEF';
    content = (
      <ReportsPage
        selectedReportId={reportId}
        onBack={() => navigate('/reports')}
        onSelectReport={openReport}
      />
    );
  } else {
    switch (currentRoute) {
      case '/upload':
        pageTitle = 'Alert Feed Ingestion';
        breadcrumb = 'DATA INTAKE';
        content = <UploadPage navigate={navigate} />;
        break;

      case '/attack-chains':
        pageTitle = 'Correlated Attack Chains';
        breadcrumb = 'CORRELATION ENGINE';
        content = <AttackChainsPage onOpenChain={openIncident} />;
        break;

      case '/mitre':
        pageTitle = 'MITRE ATT&CK® Enterprise Matrix';
        breadcrumb = 'DEFENSE MATRIX';
        content = <MitrePage onOpenChain={openIncident} />;
        break;

      case '/risk':
        pageTitle = 'Risk Prioritization Queue';
        breadcrumb = 'COMMAND TRIAGE';
        content = <RiskPage onOpenChain={openIncident} />;
        break;

      case '/recommendations':
        pageTitle = 'Tactical Action Recommendations';
        breadcrumb = 'RESPONSE PLAYBOOKS';
        content = <RecommendationsPage onOpenChain={openIncident} />;
        break;

      case '/reports':
        pageTitle = 'Executive BLUF Intelligence Reports';
        breadcrumb = 'BRIEFINGS';
        content = <ReportsPage onSelectReport={openReport} />;
        break;

      case '/chat':
        pageTitle = 'AI Threat Analyst Copilot';
        breadcrumb = 'ANALYST CHANNEL';
        content = <ChatPage onOpenChain={openIncident} />;
        break;

      case '/analytics':
        pageTitle = 'SOC Operations & Telemetry Analytics';
        breadcrumb = 'METRICS';
        content = <AnalyticsPage />;
        break;

      case '/settings':
        pageTitle = 'Station & Engine Configurations';
        breadcrumb = 'SETTINGS';
        content = <SettingsPage />;
        break;

      case '/dashboard':
      default:
        pageTitle = 'Threat Intelligence Dashboard';
        breadcrumb = 'OPERATIONS OVERVIEW';
        content = (
          <DashboardPage
            navigate={navigate}
            onOpenChain={openIncident}
          />
        );
        break;
    }
  }

  return (
    <div className="app-shell">
      <Sidebar
        currentRoute={currentRoute}
        navigate={navigate}
        collapsed={collapsed}
        setCollapsed={setCollapsed}
      />

      <div className="main-shell">
        <Topbar
          title={pageTitle}
          breadcrumb={breadcrumb}
          onRefresh={() => window.location.reload()}
          navigate={navigate}
          theme={theme}
          setTheme={setTheme}
        />
        <main className="content-body">
          {content}
        </main>
      </div>
    </div>
  );
}

const rootElement = document.getElementById('root');
if (rootElement) {
  createRoot(rootElement).render(
    <ToastProvider>
      <App />
    </ToastProvider>
  );
}
