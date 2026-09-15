import { Search } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export function HomeSearchBar({ autoFocus = false }: { autoFocus?: boolean }) {
  const [term, setTerm] = useState('');
  const navigate = useNavigate();

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const q = term.trim();
    if (q.length >= 2) navigate(`/search?q=${encodeURIComponent(q)}`);
  };

  return (
    <form className="searchbox home-hero-search" onSubmit={submit}>
      <Search aria-hidden />
      <input
        autoFocus={autoFocus}
        value={term}
        onChange={(e) => setTerm(e.target.value)}
        placeholder="Search by title or director…"
        aria-label="Search films"
      />
    </form>
  );
}
