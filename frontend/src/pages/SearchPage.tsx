import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import { searchMovies } from '../api/movies';
import { getWatchlist, getWatched } from '../api/library';
import { movieId, movieTitle, movieYear } from '../api/types';
import { PosterCard, PosterSkeleton } from '../components/PosterCard';
import { useAuthStore } from '../stores/auth';

type SortKey = 'relevance' | 'rating' | 'year';

export function SearchPage() {
  const [params, setParams] = useSearchParams();
  const initial = params.get('q') ?? '';
  const [term, setTerm] = useState(initial);
  const [genre, setGenre] = useState('');
  const [yearMin, setYearMin] = useState('');
  const [sort, setSort] = useState<SortKey>('relevance');
  const signedIn = useAuthStore((s) => !!s.accessToken);

  const { data, isFetching, isError } = useQuery({
    queryKey: ['search', term],
    queryFn: () => searchMovies(term),
    enabled: term.trim().length >= 2,
  });

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
      <div className="searchbox">
        <Search aria-hidden />
        <input
          autoFocus
          value={term}
          onChange={(e) => onTermChange(e.target.value)}
          placeholder="Search by title or director…"
        />
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
                <PosterCard movie={m} rating={m.imdbRating ? Number(m.imdbRating) : undefined} />
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
