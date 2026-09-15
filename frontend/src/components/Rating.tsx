import { Star } from 'lucide-react';

export function RatingPicker({
  value,
  onChange,
  large = false,
}: {
  value: number;
  onChange: (value: number) => void;
  large?: boolean;
}) {
  const stars = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
  const display = (value * 2).toFixed(0);

  return (
    <div className={`rating-picker ${large ? 'large' : ''}`} aria-label="Your rating">
      {stars.map((n) => {
        const half = n - 0.5;
        const starValue = n / 2;
        const halfValue = half / 2;
        const filled = value >= starValue;
        const halfFilled = !filled && value >= halfValue;
        return (
          <button
            type="button"
            key={n}
            onClick={(e) => {
              const rect = e.currentTarget.getBoundingClientRect();
              const leftHalf = e.clientX - rect.left < rect.width / 2;
              onChange(leftHalf ? halfValue : starValue);
            }}
            aria-label={`${n} of 10`}
          >
            <Star fill={filled ? 'currentColor' : 'none'} />
            {halfFilled && <i />}
          </button>
        );
      })}
      <b>{display}<span style={{ fontSize: 14, fontWeight: 500 }}>/10</span></b>
    </div>
  );
}

export function Stars({ value }: { value: number }) {
  return (
    <span className="stars">
      <Star size={15} fill="currentColor" /> {(value * 2).toFixed(1)}/10
    </span>
  );
}
