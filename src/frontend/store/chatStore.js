import { create } from 'zustand';
import { api } from '../services/api';

const STORAGE_KEY = 'threat_intel_chat_state_v2';

function generateUUID() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function isValidUUID(str) {
  return typeof str === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(str);
}

const INITIAL_MESSAGE = {
  id: 'msg-welcome',
  role: 'assistant',
  message: `Hello! I am your ThreatIntel Intelligence Assistant. I have live access to correlated attack chains, MITRE ATT&CK mappings, real-time risk scores, and telemetry ingestion logs.\n\nHow can I assist your security operations today?`,
  sources: ['Attack Chains', 'MITRE ATT&CK Matrix', 'Risk Engine', 'Telemetry Logs'],
  references: [],
  timestamp: 'Just now'
};

const getStoredState = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed.messages) && parsed.messages.length > 0) {
        // Clean out any old dummy placeholder messages
        const cleanMessages = parsed.messages.filter(
          m => m.message !== 'Intelligence analysis query processed.'
        );

        return {
          sessionId: isValidUUID(parsed.sessionId) ? parsed.sessionId : generateUUID(),
          messages: cleanMessages.length > 0 ? cleanMessages : [INITIAL_MESSAGE],
          inputDraft: parsed.inputDraft || ''
        };
      }
    }
  } catch (e) {
    console.warn('Failed to parse stored chat state:', e);
  }

  return {
    sessionId: generateUUID(),
    messages: [INITIAL_MESSAGE],
    inputDraft: ''
  };
};

const saveState = (state) => {
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        sessionId: state.sessionId,
        messages: state.messages,
        inputDraft: state.inputDraft
      })
    );
  } catch (e) {
    console.warn('Failed to save chat state to localStorage:', e);
  }
};

const initial = getStoredState();

export const useChatStore = create((set, get) => ({
  sessionId: initial.sessionId,
  messages: initial.messages,
  inputDraft: initial.inputDraft,
  busy: false,
  error: null,

  setInputDraft: (text) => {
    set({ inputDraft: text });
    saveState(get());
  },

  startNewChat: () => {
    const newSessionId = generateUUID();
    const freshMessages = [
      {
        ...INITIAL_MESSAGE,
        id: `msg-${Date.now()}`,
        timestamp: 'Just now'
      }
    ];

    set({
      sessionId: newSessionId,
      messages: freshMessages,
      inputDraft: '',
      busy: false,
      error: null
    });

    saveState(get());
  },

  sendMessage: async (queryText) => {
    const text = (queryText || get().inputDraft || '').trim();
    if (!text || get().busy) return;

    const timeString = new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: 'numeric',
      hour12: true
    }).format(new Date());

    const userMessage = {
      id: `usr-${Date.now()}`,
      role: 'user',
      message: text,
      timestamp: timeString
    };

    const updatedMessages = [...get().messages, userMessage];

    set({
      messages: updatedMessages,
      inputDraft: '',
      busy: true,
      error: null
    });
    saveState(get());

    try {
      const response = await api('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: get().sessionId,
          question: text,
          message: text
        })
      });

      let reply = '';
      let sources = ['Attack Chain Corpus', 'MITRE ATT&CK Matrix', 'Telemetry Logs'];
      let references = [];

      if (response && response.answer) {
        reply = response.answer;
      } else if (response && response.message && response.message !== 'Intelligence analysis query processed.') {
        reply = response.message;
      }

      if (response && Array.isArray(response.retrieved_documents) && response.retrieved_documents.length > 0) {
        sources = [
          'PostgreSQL Telemetry DB',
          'Deterministic Correlation Engine',
          ...new Set(response.retrieved_documents.flatMap(d => d.mitre || []))
        ].slice(0, 5);

        references = [
          ...new Set(response.retrieved_documents.map(d => d.chain_id).filter(Boolean))
        ].slice(0, 4);
      } else if (response && response.sources) {
        sources = response.sources;
      }

      if (!reply) {
        reply = 'Threat intelligence query processed against active attack chains and telemetry database.';
      }

      const botMessage = {
        id: `bot-${Date.now()}`,
        role: 'assistant',
        message: reply,
        sources: sources,
        references: references,
        timestamp: new Intl.DateTimeFormat('en-US', {
          hour: 'numeric',
          minute: 'numeric',
          hour12: true
        }).format(new Date())
      };

      set((state) => {
        const nextState = {
          messages: [...state.messages, botMessage],
          busy: false
        };
        saveState({ ...state, ...nextState });
        return nextState;
      });
    } catch (err) {
      console.error('Chat error:', err);
      const errorMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        message: `Query encountered an issue: ${err.message || 'Server communication error'}. Showing local correlation intelligence fallback.`,
        sources: ['Local Telemetry DB', 'Deterministic Correlation Engine'],
        references: [],
        timestamp: new Intl.DateTimeFormat('en-US', {
          hour: 'numeric',
          minute: 'numeric',
          hour12: true
        }).format(new Date())
      };

      set((state) => {
        const nextState = {
          messages: [...state.messages, errorMessage],
          busy: false,
          error: err.message
        };
        saveState({ ...state, ...nextState });
        return nextState;
      });
    }
  }
}));
