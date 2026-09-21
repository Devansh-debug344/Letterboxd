import { useEffect, useMemo, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, X } from 'lucide-react';
import { Link, useSearchParams } from 'react-router-dom';
import { searchMovies } from '../api/movies';
import { getWatchlist, getWatched } from '../api/library';
import { movieId, moviePoster, movieTitle, movieYear } from '../api/types';
import { PosterCard, PosterSkeleton } from '../components/PosterCard';
import { useAuthStore } from '../stores/auth';

type SortKey = 'relevance' | 'rating' | 'year';

export function SearchPage() {
  const [params, setParams] = useSearchParams();
  const initial = params.get('q') ?? '';
  const [term, setTerm] = useState(initial);
  const [debouncedTerm, setDebouncedTerm] = useState(initial);
  const [suggestionsOpen, setSuggestionsOpen] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);
  const [genre, setGenre] = useState('');
  const [yearMin, setYearMin] = useState('');
  const [sort, setSort] = useState<SortKey>('relevance');
  const signedIn = useAuthStore((s) => !!s.accessToken);

  const { data, isFetching, isError } = useQuery({
    queryKey: ['search', debouncedTerm],
    queryFn: () => searchMovies(debouncedTerm),
    enabled: debouncedTerm.trim().length >= 2,
  });

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedTerm(term.trim()), 300);
    return () => window.clearTimeout(timer);
  }, [term]);

  useEffect(() => {
    const close = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) setSuggestionsOpen(false);
    };
    const escape = (event: KeyboardEvent) => { if (event.key === 'Escape') setSuggestionsOpen(false); };
    document.addEventListener('mousedown', close);
    document.addEventListener('keydown', escape);
    return () => { document.removeEventListener('mousedown', close); document.removeEventListener('keydown', escape); };
  }, []);

  const closeSuggestions = () => setSuggestionsOpen(false);

  const watchlist = useQuery({ queryKey: ['watchlist'], queryFn: getWatchlist, enabled: signedIn });
  const watched = useQuery({ queryKey: ['watched'], queryFn: getWatched, enabled: signedIn });

  const watchlistTitles = new Set(watchlist.data?.response.map((x) => x.title.toLowerCase()) ?? []);
  const watchedTitles = new Set(watched.data?.map((x) => x.title?.toLowerCase()).filter(Boolean) ?? []);

  const results = useMemo(() => {
    let list = [...(data ?? [])];
    if (genre) {
      list = list.filter((m) => (m.Genre || m.genre || '').toLowerCase().includes(genre.toLowerCase()));
    }
    if (yearMin) {
      const y = Number(yearMin);
      list = list.filter((m) => Number(movieYear(m)) >= y);
    }
    if (sort === 'rating') {
      list.sort((a, b) => Number(b.imdbRating || 0) - Number(a.imdbRating || 0));
    } else if (sort === 'year') {
      list.sort((a, b) => Number(movieYear(b)) - Number(movieYear(a)));
    }
    return list;
  }, [data, genre, yearMin, sort]);

  const onTermChange = (value: string) => {
    setTerm(value);
    setSuggestionsOpen(true);
    if (value.trim().length >= 2) {
      setParams({ q: value.trim() });
    } else {
      setParams({});
    }
  };

  return (
    <section className="page">
      <div className="page-intro">
        <p className="eyebrow">Discover</p>
        <h1>Search results</h1>
      </div>
      <div className="home-search" ref={searchRef}>
        <div className="searchbox stream-search">
          <Search aria-hidden />
          <input autoFocus value={term} onFocus={() => { setDebouncedTerm(term.trim()); setSuggestionsOpen(true); }} onChange={(e) => onTermChange(e.target.value)} placeholder="Search by title or director…" aria-label="Search films" aria-expanded={suggestionsOpen && !!data?.length} aria-controls="search-suggestions" />
          {term && <button type="button" className="search-clear" onClick={() => { setTerm(''); setDebouncedTerm(''); setSuggestionsOpen(false); setParams({}); }} aria-label="Clear search"><X size={17}/></button>}
        </div>
        {suggestionsOpen && debouncedTerm.length >= 2 && data?.length && (
          <div id="search-suggestions" className="movie-suggestions search-page-suggestions" role="listbox" aria-label="Movie suggestions">
            {data.slice(0, 5).map((movie) => {
              const id = movieId(movie); const poster = moviePoster(movie);
              if (!id) return null;
              return <Link key={id} to={`/film/${id}`} className="movie-suggestion" role="option" onClick={closeSuggestions}>
                {poster ? <img src={poster} alt="" width="32" height="48" loading="lazy" decoding="async" /> : <span className="suggestion-poster-placeholder" />}
                <span><strong>{movieTitle(movie)}</strong><small>{movieYear(movie)}</small></span>
              </Link>;
            })}
          </div>
        )}
      </div>

      {term.trim().length >= 2 && (
        <div className="filter-bar">
          <input placeholder="Filter genre…" value={genre} onChange={(e) => setGenre(e.target.value)} aria-label="Filter by genre" />
          <input placeholder="Year from…" value={yearMin} onChange={(e) => setYearMin(e.target.value.replace(/\D/g, ''))} aria-label="Minimum year" />
          <select value={sort} onChange={(e) => setSort(e.target.value as SortKey)} aria-label="Sort results">
            <option value="relevance">Sort: relevance</option>
            <option value="rating">Sort: rating</option>
            <option value="year">Sort: year</option>
          </select>
        </div>
      )}

      {isError && <p className="empty">No films found. Try a different title.</p>}
      {term.length > 0 && term.length < 2 && <p className="hint">Type at least two characters.</p>}

      <div className="poster-grid">
        {isFetching
          ? Array.from({ length: 10 }, (_, i) => <PosterSkeleton key={i} />)
          : results.map((m) => {
            const id = movieId(m);
            const titleKey = movieTitle(m).toLowerCase();
            const onWatchlist = watchlistTitles.has(titleKey);
            const seen = watchedTitles.has(titleKey);
            return (
              <div key={id || movieTitle(m)} className="search-card-wrap">
                <PosterCard movie={m} rating={m.imdbRating ? Number(m.imdbRating) : undefined} ratingScale={10} />
                {signedIn && (onWatchlist || seen) && (
                  <p className="hint" style={{ marginTop: 6, fontSize: 11 }}>
                    {onWatchlist && 'On watchlist'}
                    {onWatchlist && seen && ' · '}
                    {seen && 'Watched'}
                  </p>
                )}
              </div>
            );
          })}
      </div>
    </section>
  );
}
