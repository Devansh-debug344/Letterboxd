import api from './client'; import type { Movie, MovieStats, Person } from './types';
export const searchMovies = async (search: string) => { const { data } = await api.get<Movie[] | Movie>('/api/movies/search', { params: { search } }); return Array.isArray(data) ? data : [data]; };
export const getMovie = async (id: string) => (await api.get<Movie>(`/api/movies/${id}`)).data;
export const getMovieStats = async (id: string) => (await api.get<MovieStats>(`/api/movies/${id}/stats`)).data;
export const getMovieCollection = async (collection: 'trending' | 'popular', page = 1) => (await api.get<{ items: Movie[]; next?: number }>(`/api/movies/discover/${collection}`, { params: { page } })).data;
export const getPerson = async (id: string) => (await api.get<Person>(`/api/movies/person/${id}`)).data;
