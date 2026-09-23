import { CheckCircle2, AlertTriangle } from 'lucide-react';
import { createContext, useContext, useRef, useState } from 'react';

type ToastMessage = { text: string; tone: 'success' | 'error' };

const ToastContext = createContext<{ toast: (text: string, tone?: 'success' | 'error') => void; }>({
  toast: () => undefined,
});

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [message, setMessage] = useState<ToastMessage | null>(null);
  const timeout = useRef<number | undefined>(undefined);

  const toast = (text: string, tone: 'success' | 'error' = 'success') => {
    const safe = String(text ?? '').trim();
    if (!safe) return;
    window.clearTimeout(timeout.current);
    setMessage({ text: safe, tone });
    timeout.current = window.setTimeout(() => setMessage(null), 3400);
  };

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      {message && (
        <div className={`toast ${message.tone === 'error' ? 'toast-error' : ''}`} role="status" aria-live="polite">
          {message.tone === 'error' ? <AlertTriangle size={17} /> : <CheckCircle2 size={17} />}
          {message.text}
        </div>
      )}
    </ToastContext.Provider>
  );
}
export const useToast = () => useContext(ToastContext).toast;
