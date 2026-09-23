import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { apiErrorMessage } from '../api/client';
import { createReview, deleteReview, getMyReviews, updateReview } from '../api/reviews';
import { RatingPicker } from './Rating';
import { useToast } from './Toast';

const MAX_LEN = 3000;

export function ReviewComposeBox({ imdbId }: { imdbId: string }) {
  const qc = useQueryClient();
  const toast = useToast();
  const mine = useQuery({ queryKey: ['my-review', imdbId], queryFn: () => getMyReviews(imdbId) });
  const existing = mine.data?.[0];

  const [rating, setRating] = useState(existing?.rating ?? 3.5);
  const [text, setText] = useState(existing?.review ?? '');
  const [spoiler, setSpoiler] = useState(!!existing?.spoiler);
  const [synced, setSynced] = useState(false);

  useEffect(() => {
    if (existing && !synced) {
      setRating(existing.rating);
      setText(existing.review ?? '');
      setSpoiler(!!existing.spoiler);
      setSynced(true);
    }
  }, [existing, synced]);

  const refresh = () => {
    void qc.invalidateQueries({ queryKey: ['movie-reviews', imdbId] });
    void qc.invalidateQueries({ queryKey: ['my-review', imdbId] });
    void qc.invalidateQueries({ queryKey: ['my-reviews'] });
    void qc.invalidateQueries({ queryKey: ['stats', imdbId] });
  };

  const save = useMutation({
    mutationFn: () =>
      existing
        ? updateReview({ omdb_id: imdbId, rating, review: text, spoiler })
        : createReview({ omdb_id: imdbId, rating, review: text, spoiler }),
    onSuccess: () => {
      refresh();
      setSynced(false);
      toast(existing ? 'Review updated.' : 'Review published.');
    },
    onError: (e) => toast(apiErrorMessage(e, 'Could not save review.'), 'error'),
  });

  const remove = useMutation({
    mutationFn: () => deleteReview(imdbId),
    onSuccess: () => {
      refresh();
      setRating(3.5);
      setText('');
      setSpoiler(false);
      setSynced(false);
      toast('Review deleted.');
    },
    onError: (e) => toast(apiErrorMessage(e, 'Could not delete review.'), 'error'),
  });

  const busy = save.isPending || remove.isPending;

  return (
    <form
      className="review-compose"
      onSubmit={(e) => {
        e.preventDefault();
        save.mutate();
      }}
    >
      <div className="review-compose-head">
        <p className="eyebrow">{existing ? 'YOUR REVIEW' : 'WRITE A REVIEW'}</p>
        {existing && (
          <button type="button" className="compose-delete" onClick={() => remove.mutate()} disabled={busy}>
            <Trash2 size={14} /> Delete
          </button>
        )}
      </div>
      <RatingPicker value={rating} onChange={setRating} />
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
      <button type="submit" className="button gold" disabled={busy}>
        {save.isPending ? 'Saving…' : existing ? 'Save review' : 'Publish review'}
      </button>
    </form>
  );
}