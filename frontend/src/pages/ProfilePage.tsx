import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { getWatched, getWatchlist } from '../api/library';
import { searchMovies } from '../api/movies';
import { getMyReviews } from '../api/reviews';
import { getProfile, getUserReviews, getUserStats } from '../api/users';
import { movieId } from '../api/types';
import { PosterCard, PosterSkeleton } from '../components/PosterCard';
import { ReviewCard } from '../components/ReviewCard';

type Tab = 'watched' | 'watchlist' | 'reviews' | 'stats';

export function ProfilePage() {
  const { userId } = useParams();
  const me = !userId;
  const [tab, setTab] = useState<Tab>('watched');

  const profile = useQuery({ queryKey: ['profile'], queryFn: getProfile, enabled: me });
  const stats = useQuery({ queryKey: ['user-stats', userId], queryFn: () => getUserStats(userId!), enabled: !me });
  const myStats = useQuery({
    queryKey: ['my-stats-inline'],
    enabled: me,
    queryFn: async () => {
      const [w, r, wl] = await Promise.all([
        getWatched(),
        getMyReviews(),
        getWatchlist(),
      ]);
      const ratings = w.filter((x) => x.rating != null).map((x) => x.rating!);
      const avg = ratings.length ? ratings.reduce((a, b) => a + b, 0) / ratings.length : null;
      return { watched: w.length, reviews: r.length, watchlist: wl.response.length, avg_rating: avg };
    },
  });

  const reviews = useQuery({
    queryKey: ['profile-reviews', userId],
    queryFn: () => (me ? getMyReviews() : getUserReviews(userId!)),
    enabled: me || !!userId,
  });

  const watchlist = useQuery({ queryKey: ['watchlist'], queryFn: getWatchlist, enabled: me });
  const watched = useQuery({ queryKey: ['watched'], queryFn: getWatched, enabled: me });

  const s = me ? myStats.data : stats.data;
  const displayName = me ? (profile.data?.username || '…') : `Member #${userId}`;
  const joined = me && profile.data?.joined_at
    ? new Date(profile.data.joined_at).toLocaleDateString(undefined, { month: 'long', year: 'numeric' })
    : null;

  const genreChart = useMemo(() => {
    const counts: Record<string, number> = {};
    watchlist.data?.response.forEach((m) => {
      m.genre.split(',').forEach((g) => {
        const key = g.trim();
        if (key) counts[key] = (counts[key] || 0) + 1;
      });
    });
    return Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 6);
  }, [watchlist.data]);

  return (
    <section className="page profile">
      <div className="profile-cover" aria-hidden />
      <div className="profile-head">
        <div className="profile-avatar">{displayName.slice(0, 1).toUpperCase()}</div>
        <div>
          <p className="eyebrow">{me ? 'Your profile' : 'Member profile'}</p>
          <h1>{displayName}</h1>
          {joined && <p className="hint">Joined {joined}</p>}
          {me ? (
            <Link to="/settings">Edit profile</Link>
          ) : (
            <button type="button" className="button gold" disabled title="Coming soon">Follow</button>
          )}
        </div>
      </div>

      {s && (
        <div className="profile-stats">
          <span><b>{s.watched}</b> movies watched</span>
          <span><b>{s.avg_rating?.toFixed(1) ?? '—'}</b> avg rating</span>
          <span><b>{s.reviews}</b> reviews</span>
          <span><b>{'watchlist' in s ? s.watchlist : '—'}</b> watchlist</span>
        </div>
      )}

      <div className="profile-tabs" role="tablist">
        {(['watched', 'watchlist', 'reviews', 'stats'] as Tab[]).map((t) => (
          <button
            key={t}
            type="button"
            role="tab"
            aria-selected={tab === t}
            className={`profile-tab ${tab === t ? 'active' : ''}`}
            onClick={() => setTab(t)}
          >
            {t === 'stats' ? 'Stats' : t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {tab === 'watched' && (
        me && watched.isLoading ? (
          <div className="poster-grid">{Array.from({ length: 6 }, (_, i) => <PosterSkeleton key={i} />)}</div>
        ) : me && watched.data?.length ? (
          <WatchedGrid items={watched.data} />
        ) : (
          <div className="empty">No watched films yet.</div>
        )
      )}

      {tab === 'watchlist' && (
        me && watchlist.isLoading ? (
          <div className="poster-grid">{Array.from({ length: 6 }, (_, i) => <PosterSkeleton key={i} />)}</div>
        ) : me && watchlist.data?.response.length ? (
          <WatchlistGrid titles={watchlist.data.response.map((x) => x.title)} />
        ) : (
          <div className="empty">Watchlist is empty. <Link to="/search">Find films</Link></div>
        )
      )}

      {tab === 'reviews' && (
        reviews.data?.length
          ? reviews.data.map((r) => <ReviewCard key={r.id} review={r} showLikes />)
          : <div className="empty">No reviews here yet.</div>
      )}

      {tab === 'stats' && me && (
        genreChart.length ? (
          <div className="diary-list">
            <p className="eyebrow">Watchlist by genre</p>
            {genreChart.map(([name, count]) => (
              <div className="diary-line" key={name}>
                <span>{count} films</span>
                <b>{name}</b>
                <em style={{ width: `${Math.min(100, count * 12)}%`, maxWidth: 120, height: 6, background: 'var(--gold)', borderRadius: 3, display: 'block' }} />
              </div>
            ))}
          </div>
        ) : (
          <div className="empty">Add films to your watchlist to see genre stats.</div>
        )
      )}
    </section>
  );
}

function WatchlistGrid({ titles }: { titles: string[] }) {
  const posters = useQuery({
    queryKey: ['profile-watchlist-posters', titles.join('|')],
    queryFn: async () => {
      const results = await Promise.all(titles.map(async (title) => {
        const found = await searchMovies(title);
        return found.find((m) => (m.Title || m.title)?.toLowerCase() === title.toLowerCase()) || found[0];
      }));
      return results.filter(Boolean);
    },
  });

  if (posters.isLoading) {
    return <div className="poster-grid">{Array.from({ length: titles.length }, (_, i) => <PosterSkeleton key={i} />)}</div>;
  }

  return (
    <div className="poster-grid">
      {posters.data?.map((m) => <PosterCard key={movieId(m)} movie={m} />)}
    </div>
  );
}

function WatchedGrid({ items }: { items: Array<{ title?: string; movie_id?: number; rating?: number | null }> }) {
  const posters = useQuery({
    queryKey: ['profile-watched-posters', items.map((i) => i.title).join('|')],
    queryFn: async () => {
      const results = await Promise.all(
        items.map(async (item) => {
          if (!item.title) return null;
          const found = await searchMovies(item.title);
          return found.find((m) => (m.Title || m.title)?.toLowerCase() === item.title!.toLowerCase()) || found[0];
        }),
      );
      return results.map((m, i) => ({ movie: m, rating: items[i].rating }));
    },
  });

  if (posters.isLoading) {
    return <div className="poster-grid">{Array.from({ length: items.length }, (_, i) => <PosterSkeleton key={i} />)}</div>;
  }

  return (
    <div className="poster-grid">
      {posters.data?.map(({ movie, rating }, i) =>
        movie ? <PosterCard key={movieId(movie) || i} movie={movie} rating={rating ?? undefined} /> : null,
      )}
    </div>
  );
}
