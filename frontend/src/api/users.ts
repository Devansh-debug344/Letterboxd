import api from './client'; import type { Review, UserProfile, UserStats } from './types';
export const getProfile = async () => (await api.get<UserProfile>('/api/user/profile')).data;
export const updateProfile = (data: Partial<Pick<UserProfile, 'username' | 'email'>>) => api.patch('/api/user/profile', data);
export const getUserStats = async (id: string) => (await api.get<UserStats>(`/api/user/${id}/stats`)).data;
export const getUserReviews = async (id: string) => (await api.get<Review[]>(`/api/user/${id}/reviews`, { params: { page: 1, limit: 20 } })).data;
