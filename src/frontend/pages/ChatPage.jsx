import React, { useEffect, useRef, useState } from 'react';
import {
  Sparkles,
  RotateCcw,
  Send,
  Bot,
  User,
  Copy,
  Check,
  Shield,
  TrendingUp,
  AlertTriangle,
  Activity,
  FileText,
  ExternalLink
} from 'lucide-react';
import { useChatStore } from '../store/chatStore';

export function ChatPage({ onOpenChain }) {
  const {
    messages,
    inputDraft,
    busy,
    setInputDraft,
    sendMessage,
    startNewChat
  } = useChatStore();

  const [copiedId, setCopiedId] = useState(null);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  // Auto scroll to latest message
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, busy]);

  const handleCopy = (id, text) => {
    navigator.clipboard?.writeText(text);
    setCopiedId(id);
    setTimeout(() => {
      setCopiedId(null);
    }, 2000);
  };

  const suggestions = [
    { label: 'Active Incidents', query: 'What are the current active high-risk incidents?', icon: Shield },
    { label: 'MITRE TTPs', query: 'Which MITRE ATT&CK techniques were detected across the logs?', icon: TrendingUp },
    { label: 'Top Risk Targets', query: 'Which destination assets and IP addresses are under active attack?', icon: AlertTriangle },
    { label: 'Attack Chain Summary', query: 'Provide a structured summary of the detected multi-stage attack chains.', icon: Activity },
    { label: 'Response Playbooks', query: 'What are the immediate tactical remediation recommendations for critical alerts?', icon: FileText },
  ];

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!inputDraft.trim() || busy) return;
    sendMessage(inputDraft);
  };

  const handleSuggestionClick = (query) => {
    if (busy) return;
    sendMessage(query);
  };

  return (
    <div className="ai-assistant-wrapper">
      {/* Top Header Card */}
      <div className="ai-assistant-header">
        <div className="ai-header-left">
          <div className="ai-logo-box">
            <Sparkles size={20} className="ai-logo-icon" />
            <span className="ai-status-dot" title="Model is operational" />
          </div>
          <div className="ai-title-block">
            <div className="ai-title-row">
              <span className="ai-title">ThreatSense AI Assistant</span>
              <span className="ai-live-badge">LIVE MODEL</span>
            </div>
            <p className="ai-subtitle">
              Autonomous threat intelligence queries across attack chains, risks, MITRE tactics & telemetry
            </p>
          </div>
        </div>

        <div className="ai-header-right">
          <button
            type="button"
            className="ai-new-chat-btn"
            onClick={startNewChat}
            title="Start a fresh conversation"
          >
            <RotateCcw size={15} />
            <span>New Chat</span>
          </button>
        </div>
      </div>

      {/* Messages Stream */}
      <div className="ai-messages-container">
        {messages.map((m) => {
          const isUser = m.role === 'user';

          if (isUser) {
            return (
              <div key={m.id || m.timestamp} className="ai-msg-row user">
                <div className="ai-msg-bubble user">
                  <div className="ai-msg-text">{m.message}</div>
                  <div className="ai-msg-footer user">
                    <span>{m.timestamp || 'Just now'}</span>
                  </div>
                </div>
                <div className="ai-avatar user">
                  <User size={18} />
                </div>
              </div>
            );
          }

          // Assistant Message
          return (
            <div key={m.id || m.timestamp} className="ai-msg-row bot">
              <div className="ai-avatar bot">
                <Bot size={20} />
              </div>

              <div className="ai-msg-card bot">
                {/* Message Body */}
                <div className="ai-msg-text">
                  {m.message.split('\n\n').map((paragraph, pIdx) => (
                    <p key={pIdx} style={{ margin: pIdx === 0 ? '0 0 12px 0' : '12px 0' }}>
                      {paragraph}
                    </p>
                  ))}
                </div>

                {/* Knowledge Sources & References Divider */}
                {((m.sources && m.sources.length > 0) || (m.references && m.references.length > 0)) && (
                  <>
                    <div className="ai-card-divider" />
                    <div className="ai-sources-section">
                      {m.sources && m.sources.length > 0 && (
                        <div className="ai-sources-row">
                          <span className="ai-sources-label">Knowledge Sources:</span>
                          <div className="ai-sources-pills">
                            {m.sources.map((source, sIdx) => (
                              <span key={sIdx} className="ai-source-pill">
                                {source}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Quick Pivot References */}
                      {m.references && m.references.length > 0 && (
                        <div className="ai-references-row">
                          <span className="ai-sources-label">Pivots:</span>
                          <div className="ai-sources-pills">
                            {m.references.map((ref, rIdx) => (
                              <button
                                key={rIdx}
                                type="button"
                                className="ai-pivot-btn"
                                onClick={() => onOpenChain && onOpenChain(ref)}
                              >
                                <span>Inspect {ref}</span>
                                <ExternalLink size={12} />
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </>
                )}

                {/* Card Timestamp and Copy Action */}
                <div className="ai-card-meta">
                  <span className="ai-timestamp">{m.timestamp || 'Just now'}</span>
                  <button
                    type="button"
                    className="ai-copy-btn"
                    onClick={() => handleCopy(m.id, m.message)}
                    title="Copy response to clipboard"
                  >
                    {copiedId === m.id ? (
                      <>
                        <Check size={14} className="text-success" />
                        <span style={{ color: 'var(--success-text, #10B981)', fontSize: 11, fontWeight: 600 }}>Copied</span>
                      </>
                    ) : (
                      <Copy size={14} />
                    )}
                  </button>
                </div>
              </div>
            </div>
          );
        })}

        {/* Loading / Searching State */}
        {busy && (
          <div className="ai-msg-row bot">
            <div className="ai-avatar bot">
              <Bot size={20} />
            </div>
            <div className="ai-msg-card bot ai-msg-loading">
              <div className="ai-typing-indicator">
                <span />
                <span />
                <span />
              </div>
              <span className="ai-loading-text">
                Analyzing threat telemetry, evaluating attack vectors & querying vector embeddings...
              </span>
            </div>
          </div>
        )}

        <div ref={scrollRef} />
      </div>

      {/* Bottom Suggestions & Input Section */}
      <div className="ai-bottom-section">
        {/* Suggestion Pills */}
        <div className="ai-suggestions-bar">
          <span className="ai-suggestions-label">SUGGESTIONS:</span>
          <div className="ai-suggestions-list">
            {suggestions.map((item, idx) => {
              const Icon = item.icon;
              return (
                <button
                  key={idx}
                  type="button"
                  className="ai-suggestion-pill"
                  onClick={() => handleSuggestionClick(item.query)}
                  disabled={busy}
                >
                  <Icon size={14} className="ai-suggestion-icon" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Prompt Input Row */}
        <form onSubmit={handleSubmit} className="ai-input-wrapper">
          <input
            ref={inputRef}
            type="text"
            className="ai-chat-input"
            placeholder="Ask about active attack chains, MITRE techniques, or incident risks... (Press Enter)"
            value={inputDraft}
            onChange={(e) => setInputDraft(e.target.value)}
            disabled={busy}
          />
          <button
            type="submit"
            className="ai-ask-btn"
            disabled={busy || !inputDraft.trim()}
          >
            <span>Ask AI</span>
            <Send size={15} />
          </button>
        </form>
      </div>
    </div>
  );
}
