import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { Bookmark, Check, Eye, Pencil, Star } from 'lucide-react';
import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { getMovie, getMovieStats, searchMovies } from '../api/movies';
import { addWatched, addWatchlist, getWatchlist, removeWatchlist } from '../api/library';
import { deleteReview, getMovieReviews, getMyReviews } from '../api/reviews';
import { getProfile } from '../api/users';
import {
  movieDirector,
  movieGenre,
  movieId,
  moviePoster,
  movieRuntime,
  movieTagline,
  movieTitle,
  movieYear,
} from '../api/types';
import { PosterCard, PosterSkeleton } from '../components/PosterCard';
import { ReviewCard } from '../components/ReviewCard';
import { useToast } from '../components/Toast';
import { useAuthStore } from '../stores/auth';

export function MoviePage() {
  const { imdbId = '' } = useParams();
  const qc = useQueryClient();
  const toast = useToast();
  const nav = useNavigate();
  const signedIn = useAuthStore((s) => !!s.accessToken);
  const [posterOpen, setPosterOpen] = useState(false);

  const movie = useQuery({ queryKey: ['movie', imdbId], queryFn: () => getMovie(imdbId) });
  const stats = useQuery({ queryKey: ['stats', imdbId], queryFn: () => getMovieStats(imdbId), retry: false });
  const reviews = useQuery({ queryKey: ['movie-reviews', imdbId], queryFn: () => getMovieReviews(imdbId), retry: false });
  const profile = useQuery({ queryKey: ['profile'], queryFn: getProfile, enabled: signedIn });
  const myReview = useQuery({ queryKey: ['my-review', imdbId], queryFn: () => getMyReviews(imdbId), enabled: signedIn });
  const watchlist = useQuery({ queryKey: ['watchlist'], queryFn: getWatchlist, enabled: signedIn });

  const saved = watchlist.data?.response.some((x) => x.id === movie.data?.id) || false;
  const fail = (e: unknown) => toast((e as AxiosError<{ detail?: string }>).response?.data?.detail || 'Could not update your diary.');

  const save = useMutation({
    mutationFn: () => (saved ? removeWatchlist(imdbId) : addWatchlist(imdbId)),
    onMutate: async () => {
      await qc.cancelQueries({ queryKey: ['watchlist'] });
      const previous = qc.getQueryData(['watchlist']);
      if (movie.data && !saved) {
        qc.setQueryData(['watchlist'], (old: typeof watchlist.data) =>
          old
            ? {
              ...old,
              response: [
                ...old.response,
                {
                  id: movie.data!.id || -1,
                  title: movieTitle(movie.data!),
                  genre: movieGenre(movie.data!),
                  year: movieYear(movie.data!),
                  plot: movie.data!.plot || movie.data!.Plot || '',
                },
              ],
            }
            : old,
        );
      }
      return { previous };
    },
    onError: (e, _v, ctx) => {
      qc.setQueryData(['watchlist'], ctx?.previous);
      fail(e);
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ['watchlist'] }),
  });

  const watched = useMutation({
    mutationFn: () => addWatched({ omdb_id: imdbId }),
    onSuccess: () => {
      toast('Marked as watched.');
      qc.invalidateQueries({ queryKey: ['stats'] });
      qc.invalidateQueries({ queryKey: ['watched'] });
    },
    onError: fail,
  });

  const removeMyReview = useMutation({
    mutationFn: () => deleteReview(imdbId),
    onSuccess: () => {
      toast('Review deleted.');
      qc.invalidateQueries({ queryKey: ['movie-reviews', imdbId] });
      qc.invalidateQueries({ queryKey: ['my-review', imdbId] });
    },
    onError: fail,
  });

  const genre = movie.data ? movieGenre(movie.data) : '';
  const similar = useQuery({
    queryKey: ['similar', genre],
    enabled: !!genre && genre !== 'Cinema',
    queryFn: async () => {
      const term = genre.split(',')[0]?.trim() || genre;
      const results = await searchMovies(term);
      return results.filter((m) => movieId(m) && movieId(m) !== imdbId).slice(0, 8);
    },
  });

  const action = (fn: () => void) => (signedIn ? fn() : nav('/login'));

  if (movie.isLoading) {
    return (
      <section className="page movie-loading">
        <div className="movie-poster skeleton" />
        <div className="copy-skeleton skeleton" />
      </section>
    );
  }

  if (movie.isError || !movie.data) {
    return (
      <section className="page empty">
        That film couldn&apos;t be found. <Link to="/search">Search films</Link>
      </section>
    );
  }

  const m = movie.data;
  const poster = moviePoster(m);
  const director = movieDirector(m);
  const runtime = movieRuntime(m);
  const tagline = movieTagline(m);
  const username = profile.data?.username;

  return (
    <section className="movie-page">
      {posterOpen && poster && (
        <button type="button" className="poster-lightbox" onClick={() => setPosterOpen(false)} aria-label="Close poster">
          <img src={poster} alt={`${movieTitle(m)} poster enlarged`} />
        </button>
      )}

      <div className="movie-hero">
        {poster ? (
          <button type="button" className="movie-poster-wrap" onClick={() => setPosterOpen(true)} style={{ border: 0, padding: 0, background: 'none', cursor: 'zoom-in' }}>
            <img className="movie-poster" src={poster} alt={`${movieTitle(m)} poster`} />
          </button>
        ) : (
          <div className="movie-poster poster-fallback">{movieTitle(m)}</div>
        )}
        <div className="movie-copy">
          <p className="eyebrow">{m.Type || 'Film'} · {movieYear(m)}</p>
          <h1>{movieTitle(m)}</h1>
          {tagline && <p className="tagline">{tagline}</p>}
          <div className="meta-row">
            {director && <span>Directed by {director}</span>}
            {runtime && <span>{runtime}</span>}
            <span>{genre || 'Cinema'}</span>
          </div>
          {stats.data?.avg_rating != null && (
            <p className="rating-hero">
              {stats.data.avg_rating.toFixed(1)}
              <small> community average · {stats.data.review_count} reviews</small>
            </p>
          )}
          <p className="plot">{m.plot || m.Plot || 'No synopsis available yet.'}</p>
          <div className="actions">
            <button type="button" className={`button ${saved ? 'muted' : ''}`} onClick={() => action(() => save.mutate())}>
              {saved ? <><Check size={17} /> On watchlist</> : <><Bookmark size={17} /> Add to watchlist</>}
            </button>
            <button type="button" className="button ghost" onClick={() => action(() => watched.mutate())}>
              <Eye size={17} /> Mark as watched
            </button>
            <button type="button" className="button gold" onClick={() => action(() => nav(`/review/${imdbId}`))}>
              <Pencil size={17} /> Write a review
            </button>
          </div>
        </div>
      </div>

      {stats.data && (
        <div className="stats-bar">
          <span><Star fill="currentColor" /> {stats.data.avg_rating?.toFixed(1) ?? '—'}<small>average</small></span>
          <span>{stats.data.review_count}<small>reviews</small></span>
          <span>{stats.data.watched_count}<small>watched</small></span>
          <span>{stats.data.watchlist_count}<small>watchlisted</small></span>
        </div>
      )}

      <section className="reviews-section">
        <div className="section-heading">
          <h2>Reviews</h2>
          <span>{reviews.data?.length || 0} from the community</span>
        </div>
        {reviews.isLoading && <div className="review-card skeleton" />}
        {reviews.data?.length
          ? reviews.data.map((r) => (
            <ReviewCard
              key={r.id}
              review={r}
              showLikes
              filmPath={`/film/${imdbId}`}
              canEdit={!!username && r.user_name === username}
              onDelete={myReview.data?.[0]?.id === r.id ? () => removeMyReview.mutate() : undefined}
            />
          ))
          : !reviews.isLoading && <p className="empty">No reviews yet. Be the first to leave a note.</p>}
      </section>

      {similar.data && similar.data.length > 0 && (
        <section className="home-section">
          <div className="section-heading"><h2>Similar films</h2></div>
          <div className="poster-row">
            {similar.isLoading
              ? Array.from({ length: 4 }, (_, i) => <PosterSkeleton key={i} />)
              : similar.data.map((sm) => <PosterCard key={movieId(sm)} movie={sm} />)}
          </div>
        </section>
      )}
    </section>
  );
}
