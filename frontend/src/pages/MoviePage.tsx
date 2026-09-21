import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { Bookmark, Check, Clock3, Eye, Star } from 'lucide-react';
import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { getMovie, getMovieCollection, getMovieStats } from '../api/movies';
import { addWatched, addWatchlist, getWatched, getWatchlist, removeWatchlist } from '../api/library';
import { deleteReview, getMovieReviews, getMyReviews } from '../api/reviews';
import { getProfile } from '../api/users';
import { isNotFoundError } from '../api/client';
import { movieDirector, movieGenre, movieId, moviePoster, movieRuntime, movieTagline, movieTitle, movieYear, type Movie } from '../api/types';
import { HorizontalRail } from '../components/HorizontalRail';
import { PosterCard, PosterSkeleton } from '../components/PosterCard';
import { ReviewCard } from '../components/ReviewCard';
import { RatingDisplay, normalizeRating } from '../components/RatingDisplay';
import { useToast } from '../components/Toast';
import { useAuthStore } from '../stores/auth';

const fact = (label: string, value?: string | null) => value ? { label, value } : null;

function Portrait({ name, profile, className }: { name: string; profile?: string | null; className: string }) {
  const [hasImage, setHasImage] = useState(Boolean(profile));
  return hasImage ? <img className={className} src={profile || undefined} alt={`${name} portrait`} loading="lazy" decoding="async" onError={() => setHasImage(false)} /> : <div className={`${className} portrait-fallback`} aria-label={`${name} portrait placeholder`}>{name.slice(0, 1)}</div>;
}

type CrewPerson = { id?: number; name?: string; roles?: string[]; profile?: string | null };

function mergeCrew(m: Movie) {
  const fallback: CrewPerson[] = [
    ...(m.Director || m.director || '').split(',').filter(Boolean).map((name) => ({ name: name.trim(), roles: ['Director'] })),
    ...(m.Writer || '').split(',').filter(Boolean).map((name) => ({ name: name.trim(), roles: ['Writer'] })),
    ...(m.producers ?? []).map((person) => ({ id: person.id, name: person.name, roles: ['Producer'], profile: person.profile })),
  ];
  const people: CrewPerson[] = m.crew?.length
    ? m.crew.map((person): CrewPerson => ({ id: person.id, name: person.name, roles: person.roles, profile: person.profile }))
    : fallback;
  const grouped = new Map<string, { id?: number; name: string; roles: string[]; profile?: string | null }>();
  people.forEach((person: CrewPerson) => {
    if (!person.name) return;
    const key = String(person.id ?? person.name);
    const existing = grouped.get(key);
    if (existing) existing.roles = [...new Set([...existing.roles, ...(person.roles ?? [])])];
    else grouped.set(key, { id: person.id, name: person.name, roles: person.roles ?? [], profile: person.profile });
  });
  return [...grouped.values()];
}

export function MoviePage() {
  const { imdbId = '' } = useParams(); const qc = useQueryClient(); const toast = useToast(); const nav = useNavigate();
  const signedIn = useAuthStore((s) => !!s.accessToken);
  const movie = useQuery({ queryKey: ['movie', imdbId], queryFn: () => getMovie(imdbId), enabled: Boolean(imdbId) });
  const stats = useQuery({ queryKey: ['stats', imdbId], queryFn: () => getMovieStats(imdbId), enabled: Boolean(imdbId), retry: false });
  const reviews = useQuery({ queryKey: ['movie-reviews', imdbId], queryFn: () => getMovieReviews(imdbId), enabled: Boolean(imdbId), retry: false });
  const profile = useQuery({ queryKey: ['profile'], queryFn: getProfile, enabled: signedIn });
  const mine = useQuery({ queryKey: ['my-review', imdbId], queryFn: () => getMyReviews(imdbId), enabled: signedIn });
  const watchlist = useQuery({ queryKey: ['watchlist'], queryFn: getWatchlist, enabled: signedIn });
  const watchedList = useQuery({ queryKey: ['watched'], queryFn: getWatched, enabled: signedIn });
  const recommendations = useQuery({ queryKey: ['movie-recommendations', imdbId], queryFn: () => getMovieCollection('popular') });
  const saved = watchlist.data?.response.some((x) => x.id === movie.data?.id || x.imdb_id === imdbId) || false;
  const isWatched = watchedList.data?.some((x) => x.movie_id === movie.data?.id) || false;
  const fail = (error: unknown) => toast((error as AxiosError<{ detail?: string }>).response?.data?.detail || 'Could not update your diary.');
  const authAction = (action: () => void) => signedIn ? action() : (toast('Sign in to save films and track your diary.'), nav('/login'));
  const save = useMutation({
    mutationFn: (shouldSave: boolean) => shouldSave ? addWatchlist(imdbId) : removeWatchlist(imdbId),
    onMutate: (shouldSave: boolean) => {
      void qc.cancelQueries({ queryKey: ['watchlist'] });
      const previousWatchlist = qc.getQueryData<typeof watchlist.data>(['watchlist']);
      const movieId = movie.data?.id;
      if (movieId != null) {
        qc.setQueryData(['watchlist'], (current: typeof watchlist.data) => {
          if (!current) return current;
          const response = !shouldSave
            ? current.response.filter((item) => item.id !== movieId)
            : current.response.some((item) => item.id === movieId)
              ? current.response
              : [...current.response, { id: movieId, imdb_id: imdbId, title: movieTitle(movie.data!), genre: movieGenre(movie.data!), year: movieYear(movie.data!), plot: movie.data!.plot || movie.data!.Plot || '', poster: moviePoster(movie.data!) }];
          return { ...current, response };
        });
      }
      toast(shouldSave ? 'Added to your watchlist.' : 'Removed from your watchlist.');
      return { previousWatchlist };
    },
    onError: (error, _variables, context) => {
      qc.setQueryData(['watchlist'], context?.previousWatchlist);
      toast((error as AxiosError<{ detail?: string }>).response?.data?.detail || "Couldn't update your watchlist. Please try again.");
    },
    onSuccess: () => { void qc.invalidateQueries({ queryKey: ['watchlist'] }); },
  });
  const watched = useMutation({
    mutationFn: () => addWatched({ omdb_id: imdbId }),
    onMutate: () => {
      void qc.cancelQueries({ queryKey: ['watched'] });
      const previousWatched = qc.getQueryData<Array<{ id: number; movie_id?: number }>>(['watched']);
      const previousStats = qc.getQueryData<{ watched_count: number }>(['stats', imdbId]);
      const previousWatchlist = qc.getQueryData<{ response: Array<{ id: number }> }>(['watchlist']);
      const movieId = movie.data?.id;
      if (movieId != null) {
        qc.setQueryData(['watched'], (current: Array<{ id: number; movie_id?: number }> = []) => current.some((item) => item.movie_id === movieId) ? current : [...current, { id: -Date.now(), movie_id: movieId }]);
        qc.setQueryData(['stats', imdbId], (current: { watched_count: number } | undefined) => current ? { ...current, watched_count: current.watched_count + 1 } : current);
        qc.setQueryData(['watchlist'], (current: { response: Array<{ id: number }> } | undefined) => current ? { ...current, response: current.response.filter((item) => item.id !== movieId) } : current);
      }
      toast('Movie marked as watched ✓');
      return { previousWatched, previousStats, previousWatchlist };
    },
    onError: (error, _variables, context) => {
      qc.setQueryData(['watched'], context?.previousWatched);
      qc.setQueryData(['stats', imdbId], context?.previousStats);
      qc.setQueryData(['watchlist'], context?.previousWatchlist);
      toast((error as AxiosError<{ detail?: string }>).response?.data?.detail || "Couldn't mark this movie as watched. Please try again.");
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['watched'] });
      void qc.invalidateQueries({ queryKey: ['stats', imdbId] });
      void qc.invalidateQueries({ queryKey: ['watchlist'] });
    },
  });
  const deleteMine = useMutation({ mutationFn: () => deleteReview(imdbId), onSuccess: () => { toast('Review deleted.'); qc.invalidateQueries({ queryKey: ['movie-reviews', imdbId] }); qc.invalidateQueries({ queryKey: ['my-review', imdbId] }); }, onError: fail });
  if (movie.isLoading || !imdbId) return <section className="page movie-loading cinematic-loading"><div className="movie-poster skeleton" /><div className="copy-skeleton skeleton" /></section>;
  if (movie.isError && isNotFoundError(movie.error)) return <section className="page empty">That film couldn&apos;t be found. <Link to="/search">Search films</Link></section>;
  if (movie.isError || !movie.data) return <section className="page empty">This film is temporarily unavailable. Please try again shortly.</section>;
  const m = movie.data; const title = movieTitle(m); const poster = moviePoster(m); const genre = movieGenre(m); const director = movieDirector(m); const runtime = movieRuntime(m); const tagline = movieTagline(m);
  const cast: Array<{ id?: number; name?: string; character?: string; profile?: string | null }> = m.cast ?? (m.Actors || m.actors || '').split(',').filter(Boolean).map((name) => ({ name: name.trim() }));
  const facts = [fact('Release date', m.Released || m.released), fact('Runtime', runtime), fact('Language', m.Language || m.language), fact('Country', m.Country), fact('Certification', m.Rated), fact('Genres', genre)].filter(Boolean) as { label: string; value: string }[];
  const crew = mergeCrew(m); const directorPerson = crew.find((person) => person.roles.includes('Director'));
  const recommended = (recommendations.data?.items ?? []).filter((film) => movieId(film) !== imdbId).slice(0, 8); const ownRating = mine.data?.[0]?.rating;
  return <section className="movie-page cinematic-page page-enter">
    <header className="cinematic-hero">{poster && <div className="cinematic-backdrop" style={{ backgroundImage: `url(${poster})` }} aria-hidden="true" />}<div className="cinematic-backdrop-scrim" />
      <div className="cinematic-hero-content">{poster ? <img className="cinematic-poster" src={poster} alt={`${title} poster`} fetchPriority="high" /> : <div className="cinematic-poster poster-fallback">{title}</div>}<div className="cinematic-summary">
        <p className="eyebrow">{m.Type || 'Film'} <span>·</span> {movieYear(m)}</p><h1>{title}</h1>{tagline && <p className="cinematic-tagline">“{tagline}”</p>}
        <div className="cinematic-meta">{m.Rated && <span className="certificate">{m.Rated}</span>}{runtime && <span><Clock3 size={14} /> {runtime}</span>}{genre && <span>{genre}</span>}</div>{director && <p className="director-line">A film by {directorPerson?.id ? <Link to={`/person/${directorPerson.id}`}><strong>{director}</strong></Link> : <strong>{director}</strong>}</p>}
        <div className="cinematic-actions"><button type="button" className={`button cinematic-primary ${saved ? 'muted' : ''}`} onClick={() => authAction(() => save.mutate(!saved))} disabled={save.isPending}>{saved ? <><Check size={17} /> In watchlist</> : <><Bookmark size={17} /> Watchlist</>}</button><button type="button" className={`button ghost ${isWatched ? 'watched' : ''}`} onClick={() => authAction(() => watched.mutate())} disabled={watched.isPending || isWatched}>{isWatched ? <><Check size={17} /> Watched</> : <><Eye size={17} /> Mark watched</>}</button><button type="button" className="circle-action" aria-label="Rate or review this film" onClick={() => authAction(() => nav(`/review/${imdbId}`))}><Star size={19} fill={ownRating ? 'currentColor' : 'none'} /></button></div>
      </div></div>
    </header>
    <div className="cinematic-body"><section className="film-overview"><p className="eyebrow">THE STORY</p><h2>Overview</h2><p className="overview-copy">{m.plot || m.Plot || 'No synopsis is available for this film yet.'}</p>{facts.length > 0 && <dl className="fact-grid">{facts.map((item) => <div key={item.label}><dt>{item.label}</dt><dd>{item.value}</dd></div>)}</dl>}</section>
      <aside className="rating-panel"><p className="eyebrow">COMMUNITY PULSE</p><div className="rating-number">{m.imdbRating ? <RatingDisplay value={Number(m.imdbRating)} /> : <><Star fill="currentColor" /><strong>{normalizeRating(stats.data?.avg_rating, 5)?.toFixed(1) || '—'}</strong><span>/ 10</span></>}</div><p>{stats.data ? `${stats.data.review_count} ${stats.data.review_count === 1 ? 'review' : 'reviews'} from reelroom` : 'Ratings arrive as the community logs this film.'}</p>{ownRating != null ? <div className="your-rating">Your rating <RatingDisplay value={ownRating} scale={5} /></div> : <button type="button" className="rate-link" onClick={() => authAction(() => nav(`/review/${imdbId}`))}>Rate this film <Star size={14} /></button>}{stats.data && <div className="rating-footnotes"><span>{stats.data.watched_count} watched</span><span>{stats.data.watchlist_count} watchlisted</span></div>}</aside>
      {cast.length > 0 && <section className="cast-section"><div className="section-heading"><div><p className="eyebrow">ON SCREEN</p><h2>Cast</h2></div><span>{cast.length} credited</span></div><HorizontalRail labelledBy="cast-rail"><div className="cast-rail">{cast.map((actor, i) => { const card = <article className="cinematic-cast-card" key={`${actor.name}-${i}`}><Portrait name={actor.name || 'Unknown'} profile={actor.profile} className="cast-portrait" /><strong>{actor.name || 'Unknown'}</strong>{actor.character && <span>{actor.character}</span>}</article>; return actor.id ? <Link className="person-card-link" to={`/person/${actor.id}`} key={`${actor.name}-${i}`}>{card}</Link> : card; })}</div></HorizontalRail></section>}
      {crew.length > 0 && <section className="crew-section"><div className="section-heading"><div><p className="eyebrow">BEHIND THE CAMERA</p><h2>Key crew</h2></div></div><div className="crew-list">{crew.map((person) => { const card = <article className="crew-card"><Portrait name={person.name} profile={person.profile} className="crew-portrait" /><strong>{person.name}</strong><span>{person.roles.join(' · ') || 'Crew'}</span></article>; return person.id ? <Link className="person-card-link" to={`/person/${person.id}`} key={person.name}>{card}</Link> : <div key={person.name}>{card}</div>; })}</div></section>}
      {m.trailer && <section className="media-section"><div className="section-heading"><div><p className="eyebrow">WATCH</p><h2>Official trailer</h2></div></div><div className="trailer-frame"><iframe src={`https://www.youtube-nocookie.com/embed/${m.trailer}`} title={`${title} trailer`} loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowFullScreen /></div></section>}
      <section className="reviews-section cinematic-reviews"><div className="section-heading"><div><p className="eyebrow">FROM THE DIARY</p><h2>Reviews</h2></div><span>{reviews.data?.length || 0} from the community</span></div>{reviews.isLoading && <div className="review-card skeleton" />}{reviews.data?.length ? reviews.data.map((review) => <ReviewCard key={review.id} review={review} showLikes filmPath={`/film/${imdbId}`} canEdit={!!profile.data?.username && review.user_name === profile.data.username} onDelete={mine.data?.[0]?.id === review.id ? () => deleteMine.mutate() : undefined} />) : !reviews.isLoading && <p className="empty">No reviews yet. Be the first to leave a note.</p>}</section>
      <section className="recommendations-section"><div className="section-heading"><div><p className="eyebrow">KEEP EXPLORING</p><h2>More to discover</h2></div><Link to="/search">Explore all</Link></div><HorizontalRail labelledBy="recommendation-rail"><div className="poster-row">{recommendations.isLoading ? Array.from({ length: 5 }, (_, i) => <PosterSkeleton key={i} />) : recommended.map((film) => <PosterCard key={movieId(film)} movie={film} />)}</div></HorizontalRail></section>
    </div>
  </section>;
}
