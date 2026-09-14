import { createContext, useContext, useState } from 'react';
const ToastContext = createContext<(message: string) => void>(() => undefined);
export function ToastProvider({ children }: { children: React.ReactNode }) { const [message, setMessage] = useState(''); const toast = (text: string) => { setMessage(text); window.setTimeout(() => setMessage(''), 3400); }; return <ToastContext.Provider value={toast}>{children}{message && <div className="toast">{message}</div>}</ToastContext.Provider>; }
export const useToast = () => useContext(ToastContext);
