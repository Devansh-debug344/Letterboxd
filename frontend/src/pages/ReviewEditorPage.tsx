import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { getMovie } from '../api/movies';
import { createReview, getMyReviews, updateReview } from '../api/reviews';
import { movieTitle } from '../api/types';
import { RatingPicker } from '../components/Rating';
import { ReviewCard } from '../components/ReviewCard';
import { useToast } from '../components/Toast';

const MAX_LEN = 3000;

export function ReviewEditorPage() {
  const { imdbId = '' } = useParams();
  const nav = useNavigate();
  const toast = useToast();
  const qc = useQueryClient();

  const movie = useQuery({ queryKey: ['movie', imdbId], queryFn: () => getMovie(imdbId) });
  const mine = useQuery({ queryKey: ['my-review', imdbId], queryFn: () => getMyReviews(imdbId) });
  const existing = mine.data?.[0];

  const [rating, setRating] = useState(3.5);
  const [text, setText] = useState('');
  const [spoiler, setSpoiler] = useState(false);
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    if (existing && !initialized) {
      setRating(existing.rating);
      setText(existing.review || '');
      setSpoiler(!!existing.spoiler);
      setInitialized(true);
    }
  }, [existing, initialized]);

  const mut = useMutation({
    mutationFn: () =>
      existing
        ? updateReview({ omdb_id: imdbId, rating, review: text, spoiler })
        : createReview({ omdb_id: imdbId, rating, review: text, spoiler }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['my-reviews'] });
      qc.invalidateQueries({ queryKey: ['movie-reviews', imdbId] });
      toast(existing ? 'Review updated.' : 'Review published.');
      nav(`/film/${imdbId}`);
    },
    onError: (e) => toast((e as AxiosError<{ detail?: string }>).response?.data?.detail || 'Could not save review.'),
  });

  const previewReview = {
    id: -1,
    movie_id: 0,
    user_id: 0,
    movie_name: movie.data ? movieTitle(movie.data) : '',
    user_name: 'You',
    rating,
    review: text || 'Your review text will appear here.',
    spoiler,
    likes: 0,
    updated_at: new Date().toISOString(),
  };

  return (
    <section className="page editor">
      <Link className="back" to={`/film/${imdbId}`}>← Back to film</Link>
      <p className="eyebrow">{existing ? 'Edit review' : 'Write a review'}</p>
      <h1>{movie.data ? movieTitle(movie.data) : 'Your thoughts'}</h1>

      <RatingPicker value={rating} onChange={setRating} large />

      <label className="review-text">
        Your review
        <span className="char-count">{text.length} / {MAX_LEN}</span>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value.slice(0, MAX_LEN))}
          maxLength={MAX_LEN}
          placeholder="What stayed with you after the credits rolled?"
        />
      </label>

      <label className="toggle">
        <input type="checkbox" checked={spoiler} onChange={(e) => setSpoiler(e.target.checked)} />
        Contains spoilers
      </label>

      <div className="review-preview">
        <h3>Preview</h3>
        <ReviewCard review={previewReview} />
      </div>

      <button type="button" className="button full" onClick={() => mut.mutate()} disabled={mut.isPending}>
        {mut.isPending ? 'Saving…' : existing ? 'Save review' : 'Save review'}
      </button>
    </section>
  );
}
