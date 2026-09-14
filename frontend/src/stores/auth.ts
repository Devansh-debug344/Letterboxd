import { create } from 'zustand';
type Tokens = { access_token: string; refresh_token: string };
type Auth = { accessToken: string | null; refreshToken: string | null; setTokens: (tokens: Tokens) => void; clear: () => void };
const saved = typeof localStorage === 'undefined' ? null : localStorage.getItem('reel_tokens');
const initial = saved ? JSON.parse(saved) as Tokens : null;
export const useAuthStore = create<Auth>((set) => ({ accessToken: initial?.access_token ?? null, refreshToken: initial?.refresh_token ?? null, setTokens: (tokens) => { localStorage.setItem('reel_tokens', JSON.stringify(tokens)); set({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token }); }, clear: () => { localStorage.removeItem('reel_tokens'); set({ accessToken: null, refreshToken: null }); } }));
