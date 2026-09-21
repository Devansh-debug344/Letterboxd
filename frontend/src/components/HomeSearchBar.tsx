import { Search, X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { searchMovies } from '../api/movies';
import { movieId, moviePoster, movieTitle, movieYear } from '../api/types';

export function HomeSearchBar({ autoFocus = false }: { autoFocus?: boolean }) {
  const [term, setTerm] = useState('');
  const [debouncedTerm, setDebouncedTerm] = useState('');
  const searchRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const suggestions = useQuery({ queryKey: ['movie-suggestions', debouncedTerm], queryFn: () => searchMovies(debouncedTerm), enabled: debouncedTerm.length >= 2 });

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedTerm(term.trim()), 250);
    return () => window.clearTimeout(timer);
  }, [term]);

  useEffect(() => {
    const close = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) setDebouncedTerm('');
    };
    const escape = (event: KeyboardEvent) => { if (event.key === 'Escape') setDebouncedTerm(''); };
    document.addEventListener('mousedown', close);
    document.addEventListener('keydown', escape);
    return () => { document.removeEventListener('mousedown', close); document.removeEventListener('keydown', escape); };
  }, []);

  const closeSuggestions = () => { setTerm(''); setDebouncedTerm(''); };

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const q = term.trim();
    if (q.length >= 2) navigate(`/search?q=${encodeURIComponent(q)}`);
  };

  return (
    <div className="home-search" ref={searchRef}>
      <form className="searchbox home-hero-search stream-search" onSubmit={submit}>
        <Search aria-hidden />
        <input autoFocus={autoFocus} value={term} onFocus={() => setDebouncedTerm(term.trim())} onChange={(e) => setTerm(e.target.value)} placeholder="Search by title or director…" aria-label="Search films" aria-expanded={!!suggestions.data?.length} aria-controls="movie-suggestions" />
        {term && <button type="button" className="search-clear" onClick={closeSuggestions} aria-label="Clear search"><X size={17}/></button>}
      </form>
      {!term && <p className="search-prompt">Search films, actors and directors</p>}
      {debouncedTerm.length >= 2 && suggestions.data?.length ? (
        <div id="movie-suggestions" className="movie-suggestions" role="listbox" aria-label="Movie suggestions">
          {suggestions.data.slice(0, 6).map((movie) => {
            const id = movieId(movie); const poster = moviePoster(movie);
            if (!id) return null;
            return <Link key={id} to={`/film/${id}`} className="movie-suggestion" role="option" onClick={closeSuggestions}>
              {poster ? <img src={poster} alt="" width="32" height="48" loading="lazy" decoding="async" /> : <span className="suggestion-poster-placeholder" />}
              <span><strong>{movieTitle(movie)}</strong><small>{movieYear(movie)}</small></span>
            </Link>;
          })}
          <button type="button" className="all-results" onClick={() => { const query = debouncedTerm; closeSuggestions(); navigate(`/search?q=${encodeURIComponent(query)}`); }}>See all results for “{debouncedTerm}”</button>
        </div>
      ) : null}
    </div>
  );
}
