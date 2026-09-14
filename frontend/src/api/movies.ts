import api from './client'; import type { Movie, MovieStats } from './types';
export const searchMovies = async (search: string) => { const { data } = await api.get<Movie[] | Movie>('/api/movies/search', { params: { search } }); return Array.isArray(data) ? data : [data]; };
export const getMovie = async (id: string) => (await api.get<Movie>(`/api/movies/${id}`)).data;
export const getMovieStats = async (id: string) => (await api.get<MovieStats>(`/api/movies/${id}/stats`)).data;
