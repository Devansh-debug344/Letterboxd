import { useState } from 'react';
import { Eye, Heart, Pencil, Star, Trash2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { Review } from '../api/types';

type Props = {
  review: Review;
  showLikes?: boolean;
  canEdit?: boolean;
  onDelete?: () => void;
  filmPath?: string;
};

export function ReviewCard({ review, showLikes = false, canEdit, onDelete, filmPath }: Props) {
  const [shown, setShown] = useState(!review.spoiler);

  return (
    <article className="review-card">
      <div className="review-meta">
        <span className="avatar">{review.user_name?.slice(0, 1).toUpperCase()}</span>
        <div>
          <b>{review.user_name}</b>
          {filmPath && review.movie_name && (
            <small><Link to={filmPath}>{review.movie_name}</Link></small>
          )}
          <small>{new Date(review.updated_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}</small>
        </div>
        <span className="score">
          <Star size={14} fill="currentColor" /> {review.rating.toFixed(1)}
        </span>
      </div>
      {review.spoiler && !shown ? (
        <button type="button" className="spoiler" onClick={() => setShown(true)}>
          <Eye size={16} /> Contains spoilers — show review
        </button>
      ) : (
        review.review && <p>{review.review}</p>
      )}
      <div className="review-actions" style={{ display: 'flex', gap: 12, marginTop: 12, alignItems: 'center' }}>
        {showLikes && (
          <span className="hint" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <Heart size={14} /> {review.likes} helpful
          </span>
        )}
        {canEdit && filmPath && (
          <Link to={`/review/${filmPath.split('/').pop()}`} className="hint" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <Pencil size={14} /> Edit
          </Link>
        )}
        {canEdit && onDelete && (
          <button type="button" className="danger" onClick={onDelete}> <Trash2 size={14} /> Delete</button>
        )}
      </div>
    </article>
  );
}
