import React, { createContext, useContext, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertTriangle, XCircle, Info, X } from 'lucide-react';

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const showToast = useCallback((message, type = 'success', duration = 4000) => {
    const id = Math.random().toString(36).substring(7);
    setToasts((prev) => [...prev, { id, message, type }]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, duration);
  }, []);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div
        style={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          zIndex: 9999,
          display: 'flex',
          flexDirection: 'column',
          gap: 10,
          pointerEvents: 'none',
        }}
      >
        <AnimatePresence>
          {toasts.map((toast) => (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              style={{
                pointerEvents: 'auto',
                minWidth: 280,
                maxWidth: 420,
                background: 'var(--card, #0F172A)',
                color: 'var(--text-primary, #FFFFFF)',
                border: '1px solid var(--card-border, #1E293B)',
                borderRadius: 12,
                padding: '12px 16px',
                boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 12,
                backdropFilter: 'blur(16px)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                {toast.type === 'success' && <CheckCircle2 size={18} color="#10B981" />}
                {toast.type === 'error' && <XCircle size={18} color="#EF4444" />}
                {toast.type === 'warning' && <AlertTriangle size={18} color="#F59E0B" />}
                {toast.type === 'info' && <Info size={18} color="#3B82F6" />}
                <span style={{ fontSize: 13, fontWeight: 500 }}>{toast.message}</span>
              </div>

              <button
                onClick={() => removeToast(toast.id)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-muted, #94A3B8)',
                  cursor: 'pointer',
                  padding: 2,
                  display: 'flex',
                }}
              >
                <X size={14} />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    // Fallback if rendered outside provider
    return {
      showToast: (msg) => console.log('[Toast]', msg),
    };
  }
  return context;
}

export default ToastProvider;
