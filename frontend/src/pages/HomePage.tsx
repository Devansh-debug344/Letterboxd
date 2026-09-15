import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { getWatchlist } from '../api/library';
import { getMovieReviews } from '../api/reviews';
import { searchMovies } from '../api/movies';
import { movieId } from '../api/types';
import { HomeSearchBar } from '../components/HomeSearchBar';
import { PosterCard, PosterSkeleton } from '../components/PosterCard';
import { ReviewCard } from '../components/ReviewCard';

const TRENDING = ['Oppenheimer', 'Dune', 'Parasite', 'Everything Everywhere All at Once', 'The Batman'];
const POPULAR = [
  'Inception', 'Interstellar', 'The Godfather', 'Pulp Fiction', 'Fight Club',
  'The Dark Knight', 'Forrest Gump', 'Gladiator', 'Whiplash', 'La La Land',
  'Mad Max: Fury Road', 'Get Out', 'Arrival', 'Moonlight', 'Nomadland',
  'The Matrix', 'Goodfellas', 'Spirited Away', 'There Will Be Blood', 'Her',
];

export function HomePage() {
  const trending = useQuery({
    queryKey: ['trending'],
    queryFn: async () => {
      const results = await Promise.all(TRENDING.map(async (title) => (await searchMovies(title))[0]));
      return results.filter(Boolean);
    },
  });

  const popular = useInfiniteQuery({
    queryKey: ['popular-grid'],
    queryFn: async ({ pageParam = 0 }) => {
      const slice = POPULAR.slice(pageParam, pageParam + 5);
      const results = await Promise.all(slice.map(async (title) => (await searchMovies(title))[0]));
      return { items: results.filter(Boolean), next: pageParam + 5 < POPULAR.length ? pageParam + 5 : undefined };
    },
    initialPageParam: 0,
    getNextPageParam: (last) => last.next,
  });

  const watchlist = useQuery({ queryKey: ['watchlist'], queryFn: getWatchlist });

  const communityReviews = useQuery({
    queryKey: ['community-reviews', trending.data?.map((m) => movieId(m)).join(',')],
    enabled: !!trending.data?.length,
    queryFn: async () => {
      const ids = trending.data!.map(movieId).filter(Boolean).slice(0, 4);
      const batches = await Promise.all(ids.map((id) => getMovieReviews(id).catch(() => [])));
      return batches.flat().sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()).slice(0, 6);
    },
  });

  const popularFlat = popular.data?.pages.flatMap((p) => p.items) ?? [];

  return (
    <section className="page home">
      <div className="page-intro">
        <p className="eyebrow">Discovery</p>
        <h1>What are you watching?</h1>
        <p className="lede">Find films, track your watchlist, and read what others thought.</p>
        <HomeSearchBar />
      </div>

      <Section title="Trending now" to="/search">
        {trending.isLoading
          ? Array.from({ length: 5 }, (_, i) => <PosterSkeleton key={i} />)
          : trending.data?.map((m) => <PosterCard key={movieId(m)} movie={m} />)}
      </Section>

      <Section title="Popular on watchlists" to="/watchlist">
        {trending.isLoading
          ? Array.from({ length: 4 }, (_, i) => <PosterSkeleton key={i} />)
          : trending.data?.slice(0, 4).map((m) => <PosterCard key={`wl-${movieId(m)}`} movie={m} />)}
      </Section>

      <section className="home-reviews">
        <div className="section-heading">
          <h2>Recently reviewed</h2>
          <Link to="/search">Explore films <ArrowRight size={15} /></Link>
        </div>
        {communityReviews.isLoading && <div className="review-card skeleton" />}
        {communityReviews.data?.length
          ? communityReviews.data.map((r) => <ReviewCard key={r.id} review={r} showLikes />)
          : !communityReviews.isLoading && (
            <div className="empty">No community reviews yet. Be the first to write one.</div>
          )}
      </section>

      <Section title="Your watchlist" to="/watchlist">
        {watchlist.data?.response.length
          ? watchlist.data.response.slice(0, 6).map((m) => (
            <div className="watch-tile" key={m.id}>
              <b>{m.title}</b>
              <span>{m.year} · {m.genre}</span>
            </div>
          ))
          : (
            <div className="empty inline">
              Nothing on your watchlist yet. <Link to="/search">Find a film</Link>
            </div>
          )}
      </Section>

      <div className="section-heading">
        <h2>Popular movies</h2>
      </div>
      <div className="poster-grid">
        {popular.isLoading
          ? Array.from({ length: 10 }, (_, i) => <PosterSkeleton key={i} />)
          : popularFlat.map((m) => <PosterCard key={movieId(m)} movie={m} />)}
      </div>
      {popular.hasNextPage && (
        <div className="load-more-wrap">
          <button type="button" className="button ghost" disabled={popular.isFetchingNextPage} onClick={() => popular.fetchNextPage()}>
            {popular.isFetchingNextPage ? 'Loading…' : 'Load more'}
          </button>
        </div>
      )}
    </section>
  );
}

function Section({ title, to, children }: { title: string; to: string; children: React.ReactNode }) {
  return (
    <section className="home-section">
      <div className="section-heading">
        <h2>{title}</h2>
        <Link to={to}>See all <ArrowRight size={15} /></Link>
      </div>
      <div className="poster-row">{children}</div>
    </section>
  );
}
