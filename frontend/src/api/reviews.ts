import api from './client'; import type { Review } from './types';
export type ReviewInput = { omdb_id: string; rating: number; review?: string; spoiler?: boolean };
export const getMyReviews = async (omdb_id?: string) => (await api.get<Review[]>('/api/review', { params: { omdb_id, page: 1, limit: 20 } })).data;
export const getMovieReviews = async (id: string) => (await api.get<Review[]>(`/api/review/movie/${id}`, { params: { page: 1, limit: 20 } })).data;
export const createReview = (data: ReviewInput) => api.post('/api/review', data);
export const updateReview = (data: Partial<ReviewInput> & { omdb_id: string }) => api.patch('/api/review', data);
export const deleteReview = (omdb_id: string) => api.delete('/api/review', { data: { omdb_id } });
