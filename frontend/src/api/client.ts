import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '../stores/auth';
const API_BASE_URL = 'https://devansh.online';
const api = axios.create({ baseURL: API_BASE_URL });
export const isNotFoundError = (error: unknown) => axios.isAxiosError(error) && error.response?.status === 404;

export const apiErrorMessage = (error: unknown, fallback: string) => {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) => (item && typeof item === 'object' && 'msg' in item ? String((item as { msg: unknown }).msg) : String(item)))
        .filter(Boolean);
      if (messages.length) return messages.join(' · ');
    }
    if (detail != null) return String(detail);
  }
  return fallback;
};
api.interceptors.request.use((config) => { const token = useAuthStore.getState().accessToken; if (token) config.headers.Authorization = `Bearer ${token}`; return config; });
let refreshing: Promise<string> | null = null;
api.interceptors.response.use((r) => r, async (error: AxiosError) => {
  const request = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;
  if (error.response?.status !== 401 || !request || request._retry || request.url?.includes('/api/refresh')) return Promise.reject(error);
  request._retry = true;
  const refreshToken = useAuthStore.getState().refreshToken;
  if (!refreshToken) return Promise.reject(error);
  try { refreshing ??= axios.post(`${api.defaults.baseURL}/api/refresh`, { refresh_token: refreshToken }).then(({ data }) => { useAuthStore.getState().setTokens(data); return data.access_token; }).finally(() => { refreshing = null; }); const token = await refreshing; request.headers.Authorization = `Bearer ${token}`; return api(request); }
  catch (e) { useAuthStore.getState().clear(); return Promise.reject(e); }
});
export default api;
