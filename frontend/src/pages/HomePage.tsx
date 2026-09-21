import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { getWatchlist } from '../api/library';
import { getMovieReviews } from '../api/reviews';
import { getMovieCollection, searchMovies } from '../api/movies';
import { movieId } from '../api/types';
import { HomeSearchBar } from '../components/HomeSearchBar';
import { PosterCard, PosterSkeleton } from '../components/PosterCard';
import { ReviewCard } from '../components/ReviewCard';

const FALLBACK_TRENDING = ['Oppenheimer', 'Dune', 'Parasite', 'The Batman', 'Everything Everywhere All at Once'];
const FALLBACK_POPULAR = ['Inception', 'Interstellar', 'The Godfather', 'Pulp Fiction', 'Fight Club', 'The Dark Knight', 'Forrest Gump', 'Gladiator', 'Whiplash', 'La La Land'];

async function fallbackCollection(titles: string[], page = 1) {
  const slice = titles.slice((page - 1) * 5, page * 5);
  const items = (await Promise.allSettled(slice.map(async (title) => (await searchMovies(title))[0])))
    .flatMap((result) => result.status === 'fulfilled' && result.value ? [result.value] : []);
  return { items, next: page * 5 < titles.length ? page + 1 : undefined };
}

export function HomePage() {
  const trending = useQuery({
    queryKey: ['trending'],
    // The collection endpoint is fast, while this fallback keeps the feed
    // usable with an older deployed backend during a rolling deployment.
    queryFn: () => getMovieCollection('trending').catch(() => fallbackCollection(FALLBACK_TRENDING)),
  });

  const popular = useInfiniteQuery({
    queryKey: ['popular-grid'],
    queryFn: ({ pageParam = 1 }) => getMovieCollection('popular', pageParam).catch(() => fallbackCollection(FALLBACK_POPULAR, pageParam)),
    initialPageParam: 1,
    getNextPageParam: (last) => last.next,
  });

  const watchlist = useQuery({ queryKey: ['watchlist'], queryFn: getWatchlist });

  const communityReviews = useQuery({
    queryKey: ['community-reviews', trending.data?.items.map(movieId).join(',')],
    enabled: !!trending.data?.items.length,
    queryFn: async () => {
      const ids = trending.data!.items.map(movieId).filter(Boolean).slice(0, 4);
      const batches = await Promise.all(ids.map((id) => getMovieReviews(id).catch(() => [])));
      return batches.flat().sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()).slice(0, 6);
    },
  });

  const popularFlat = (popular.data?.pages.flatMap((p) => p.items) ?? []).filter((movie, index, movies) =>
    movies.findIndex((candidate) => movieId(candidate) === movieId(movie)) === index,
  );

  return (
    <section className="page home">
      <div className="page-intro home-masthead">
        <p className="eyebrow">Film diary · community · discovery</p>
        <h1>Find your next<br/>great film.</h1>
        <p className="lede">Log what you watch, build your watchlist and follow the conversation around cinema.</p>
        <HomeSearchBar />
      </div>

      <Section title="Trending now" to="/search">
        {trending.isLoading
          ? Array.from({ length: 5 }, (_, i) => <PosterSkeleton key={i} />)
          : trending.data?.items.slice(0, 6).map((m) => <PosterCard key={movieId(m)} movie={m} priority />)}
      </Section>

      <Section title="Popular on watchlists" to="/watchlist">
        {trending.isLoading
          ? Array.from({ length: 4 }, (_, i) => <PosterSkeleton key={i} />)
          : trending.data?.items.slice(6, 10).map((m) => <PosterCard key={`wl-${movieId(m)}`} movie={m} />)}
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
            <PosterCard key={m.id} movie={{ imdb_id: m.imdb_id, title: m.title, year: m.year, poster: m.poster }} />
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
      {popular.isError && <p className="hint load-error">Couldn&apos;t load that page. Please try again.</p>}
      {popular.hasNextPage && (
        <div className="load-more-wrap">
          <button type="button" className="button ghost" disabled={popular.isFetchingNextPage} onClick={() => popular.fetchNextPage()}>
            {popular.isFetchingNextPage ? 'Loading…' : 'Load more films'}
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
