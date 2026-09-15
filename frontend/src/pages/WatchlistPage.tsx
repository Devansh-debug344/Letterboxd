import { useMemo, useState } from 'react';
import { useQueries, useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { getWatchlist } from '../api/library';
import { searchMovies } from '../api/movies';
import { movieId } from '../api/types';
import { PosterCard, PosterSkeleton } from '../components/PosterCard';

type SortKey = 'added' | 'title' | 'year';

export function WatchlistPage() {
  const [sort, setSort] = useState<SortKey>('added');
  const list = useQuery({ queryKey: ['watchlist'], queryFn: getWatchlist });

  const sorted = useMemo(() => {
    const rows = [...(list.data?.response ?? [])];
    if (sort === 'title') rows.sort((a, b) => a.title.localeCompare(b.title));
    if (sort === 'year') rows.sort((a, b) => Number(b.year) - Number(a.year));
    return rows;
  }, [list.data, sort]);

  const details = useQueries({
    queries: sorted.map((x) => ({
      queryKey: ['movie-by-db-title', x.id, x.title],
      queryFn: () => getMovieFromTitle(x.title),
    })),
  });

  return (
    <section className="page">
      <div className="page-intro">
        <p className="eyebrow">Watchlist</p>
        <h1>Films to watch</h1>
        <p className="lede">Everything you&apos;ve saved for later—sort and browse your queue.</p>
      </div>

      {list.data?.response.length ? (
        <div className="filter-bar">
          <select value={sort} onChange={(e) => setSort(e.target.value as SortKey)} aria-label="Sort watchlist">
            <option value="added">Date added</option>
            <option value="title">Title</option>
            <option value="year">Year</option>
          </select>
        </div>
      ) : null}

      {list.isLoading ? (
        <div className="poster-grid">{Array.from({ length: 8 }, (_, i) => <PosterSkeleton key={i} />)}</div>
      ) : list.data?.response.length ? (
        <div className="poster-grid">
          {details.map((item, i) =>
            item.data ? (
              <PosterCard key={sorted[i].id} movie={item.data} />
            ) : (
              <div className="watch-tile large" key={sorted[i].id}>
                <b>{sorted[i].title}</b>
                <span>{sorted[i].year}<br />{sorted[i].genre}</span>
              </div>
            ),
          )}
        </div>
      ) : (
        <div className="empty">
          Your watchlist is empty. <Link to="/search">Find something to watch</Link>
        </div>
      )}
    </section>
  );
}

async function getMovieFromTitle(title: string) {
  const result = await searchMovies(title);
  return result.find((m) => (m.Title || m.title)?.toLowerCase() === title.toLowerCase()) || result[0];
}
