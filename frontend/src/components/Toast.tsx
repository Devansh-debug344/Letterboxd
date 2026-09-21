import { CheckCircle2 } from 'lucide-react';
import { createContext, useContext, useRef, useState } from 'react';

const ToastContext = createContext<(message: string) => void>(() => undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [message, setMessage] = useState('');
  const timeout = useRef<number | undefined>(undefined);

  const toast = (text: string) => {
    window.clearTimeout(timeout.current);
    setMessage(text);
    timeout.current = window.setTimeout(() => setMessage(''), 3400);
  };

  return <ToastContext.Provider value={toast}>{children}{message && <div className="toast" role="status" aria-live="polite"><CheckCircle2 size={17} />{message}</div>}</ToastContext.Provider>;
}
export const useToast = () => useContext(ToastContext);
