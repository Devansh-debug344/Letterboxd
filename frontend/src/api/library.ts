import api from './client'; import type { WatchedItem, WatchlistResponse } from './types';
export const getWatchlist = async () => (await api.get<WatchlistResponse>('/api/watchlist')).data;
export const addWatchlist = (omdb_id: string) => api.post('/api/watchlist', { omdb_id });
export const removeWatchlist = (omdb_id: string) => api.delete('/api/watchlist', { data: { omdb_id } });
export const getWatched = async () => (await api.get<WatchedItem[]>('/api/watched')).data;
export const addWatched = (data: { omdb_id: string; rating?: number; watched_at?: string }) => api.post('/api/watched', data);
export const removeWatched = (omdb_id: string) => api.delete(`/api/watched/${omdb_id}`);
