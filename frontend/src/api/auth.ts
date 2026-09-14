import api from './client';
export type Tokens = { access_token: string; refresh_token: string; token_type: string };
export const login = async (username: string, password: string) => (await api.post<Tokens>('/api/login', new URLSearchParams({ username, password }), { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } })).data;
export const register = async (data: { username: string; email: string; password: string }) => (await api.post('/api/user', data)).data;
export const sendOtp = (phone_number: string) => api.post('/api/otp/send', { phone_number });
export const verifyOtp = async (phone_number: string, code: string) => (await api.post<Tokens>('/api/otp/verify', { phone_number, code })).data;
export const logout = () => api.post('/api/logout');
