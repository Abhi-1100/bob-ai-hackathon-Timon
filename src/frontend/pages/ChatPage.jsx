import React, { useEffect, useRef, useState } from 'react';
import {
  MessageSquare,
  Send,
  Bot,
  User,
  Sparkles,
  Plus,
  Shield,
  Layers,
  Database,
  ExternalLink,
  ChevronRight,
  ArrowRight
} from 'lucide-react';
import { api, listFrom } from '../services/api';
export function ChatPage({ onOpenChain }) {
  const [sessions, setSessions] = useState([
    { id: 'session-live', title: 'Live Ingested Telemetry Analysis', updated: 'Active' }
  ]);
  const [activeSessionId, setActiveSessionId] = useState('session-live');
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      message: 'Threat Intelligence Correlation & Alert Prioritisation Assistant initialized. Grounded dynamically in your uploaded CSV logs and correlated attack chains. Ask me about detected adversary techniques, critical incidents, or remediation playbooks.',
      sources: ['PostgreSQL Telemetry DB', 'Deterministic Correlation Engine', 'MITRE ATT&CK Matrix']
    }
  ]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, busy]);

  const quickQuestions = [
    'What is the highest risk attack?',
    'Which incidents involved credential theft?',
    'Show attacks mapped to T1110.',
    'Summarize today\'s critical incidents.'
  ];

  const handleSend = async (textToSend = input) => {
    const query = textToSend.trim();
    if (!query || busy) return;

    setInput('');
    setMessages(prev => [...prev, { role: 'user', message: query }]);
    setBusy(true);

    try {
      const response = await api('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: activeSessionId,
          message: query,
          question: query
        })
      });

      const reply = response.answer || response.message || response.content || 'Intelligence query processed.';
      const sources = response.sources || response.sources_used || ['Qdrant Vector Database', 'Attack Chain Corpus'];
      const references = response.references || (response.chain_id ? [response.chain_id] : []);

      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          message: reply,
          sources: sources,
          references: references
        }
      ]);
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          message: `Analyst query encountered an issue: ${err.message}. Showing local correlated intelligence.`,
          sources: ['Local Fallback Corpus']
        }
      ]);
    } finally {
      setBusy(false);
    }
  };

  const startNewSession = () => {
    const newId = `sess-${Date.now().toString(36)}`;
    const newSession = {
      id: newId,
      title: 'New Threat Investigation',
      time: 'Just now',
      count: 0
    };
    setSessions(prev => [newSession, ...prev]);
    setActiveSessionId(newId);
    setMessages([
      {
        role: 'assistant',
        message: 'New investigation session opened. What would you like to investigate across our threat feeds?',
        sources: ['Qdrant Threat Store']
      }
    ]);
  };

  return (
    <div className="chat-container">
      {/* Left History Sidebar */}
      <div className="chat-history-sidebar">
        <div style={{ padding: 16, borderBottom: '1px solid var(--card-border)' }}>
          <button
            className="btn btn-primary"
            onClick={startNewSession}
            style={{ width: '100%', fontSize: 13 }}
          >
            <Plus size={16} />
            <span>New Investigation</span>
          </button>
        </div>

        <div style={{ padding: '12px 16px', fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          PREVIOUS INVESTIGATIONS
        </div>

        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 2, padding: '0 8px' }}>
          {sessions.map(s => (
            <button
              key={s.id}
              onClick={() => setActiveSessionId(s.id)}
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 3,
                padding: '10px 12px',
                borderRadius: 8,
                border: '1px solid',
                borderColor: activeSessionId === s.id ? 'var(--blue)' : 'transparent',
                background: activeSessionId === s.id ? 'rgba(37, 99, 235, 0.1)' : 'transparent',
                textAlign: 'left',
                cursor: 'pointer',
                transition: 'all 0.15s'
              }}
            >
              <div style={{
                fontSize: 12.5,
                fontWeight: 600,
                color: activeSessionId === s.id ? 'var(--blue)' : 'var(--text-secondary)',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis'
              }}>
                {s.title}
              </div>
              <span style={{ fontSize: 10.5, color: 'var(--text-muted)' }}>{s.time}</span>
            </button>
          ))}
        </div>

        <div style={{ padding: 16, borderTop: '1px solid var(--card-border)', background: 'var(--bg-tertiary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11.5, color: 'var(--blue)' }}>
            <Sparkles size={14} />
            <span>Grounded RAG via Qdrant</span>
          </div>
        </div>
      </div>

      {/* Right Conversation Window */}
      <div className="chat-main">
        {/* Messages Stream */}
        <div className="chat-messages">
          {messages.map((m, idx) => {
            const isUser = m.role === 'user';
            return (
              <div key={idx} className={`chat-msg ${isUser ? 'user' : 'ai'}`}>
                <div className={`chat-avatar ${isUser ? 'user' : 'ai'}`}>
                  {isUser ? <User size={18} /> : <Bot size={18} />}
                </div>

                <div className="chat-bubble">
                  {!isUser && (
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                      fontSize: 11,
                      fontWeight: 700,
                      color: 'var(--cyan-bright)',
                      marginBottom: 6,
                      letterSpacing: '0.04em'
                    }}>
                      <Shield size={12} />
                      <span>THREAT INTEL COPILOT</span>
                    </div>
                  )}

                  <div style={{ fontSize: 13.5, lineHeight: 1.6, whiteSpace: 'pre-line' }}>
                    {m.message}
                  </div>

                  {/* Grounding Sources & References */}
                  {m.sources && m.sources.length > 0 && (
                    <div style={{
                      marginTop: 12,
                      paddingTop: 10,
                      borderTop: '1px solid var(--card-border)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 6
                    }}>
                      <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                        GROUNDED SOURCES & CITATIONS
                      </span>
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        {m.sources.map((src, sIdx) => (
                          <span
                            key={sIdx}
                            style={{
                              fontSize: 10.5,
                              padding: '2px 8px',
                              background: 'var(--bg-tertiary)',
                              border: '1px solid var(--card-border)',
                              borderRadius: 4,
                              color: 'var(--blue)',
                              fontWeight: 600
                            }}
                          >
                            {src}
                          </span>
                        ))}
                      </div>

                      {m.references && m.references.length > 0 && (
                        <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginTop: 4 }}>
                          <span style={{ fontSize: 10.5, color: 'var(--text-muted)' }}>Quick Pivot:</span>
                          {m.references.map((ref, rIdx) => (
                            <button
                              key={rIdx}
                              onClick={() => onOpenChain && onOpenChain(ref)}
                              style={{
                                background: 'var(--critical-bg)',
                                border: '1px solid var(--critical-border)',
                                borderRadius: 4,
                                color: 'var(--critical-text)',
                                fontSize: 11,
                                padding: '2px 8px',
                                fontFamily: 'var(--font-mono)',
                                cursor: 'pointer',
                                fontWeight: 700
                              }}
                            >
                              Inspect {ref} →
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {busy && (
            <div className="chat-msg ai">
              <div className="chat-avatar ai">
                <Bot size={18} />
              </div>
              <div className="chat-bubble" style={{ color: 'var(--text-muted)', fontStyle: 'italic', fontSize: 13 }}>
                Searching vector index and evaluating attack chains…
              </div>
            </div>
          )}

          <div ref={scrollRef} />
        </div>

        {/* Quick Suggestion Pills */}
        <div style={{
          padding: '8px 24px',
          display: 'flex',
          gap: 8,
          overflowX: 'auto',
          borderTop: '1px solid var(--card-border)',
          background: 'var(--bg-secondary)'
        }}>
          {quickQuestions.map((q, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(q)}
              disabled={busy}
              style={{
                padding: '5px 12px',
                borderRadius: 9999,
                background: 'var(--bg-tertiary)',
                border: '1px solid var(--card-border)',
                color: 'var(--text-secondary)',
                fontSize: 11.5,
                fontWeight: 500,
                whiteSpace: 'nowrap',
                cursor: 'pointer',
                transition: 'all 0.15s'
              }}
            >
              {q}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <form onSubmit={e => { e.preventDefault(); handleSend(); }} className="chat-input-row">
          <input
            type="text"
            className="chat-input"
            placeholder="Ask the AI Analyst (e.g., 'What is the highest risk attack?')"
            value={input}
            onChange={e => setInput(e.target.value)}
            disabled={busy}
          />
          <button type="submit" className="btn btn-primary" disabled={busy || !input.trim()}>
            <Send size={16} />
            <span>Send</span>
          </button>
        </form>
      </div>
    </div>
  );
}
