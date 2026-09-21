import { Star } from 'lucide-react';

type RatingDisplayProps = {
  value?: number | null;
  scale?: 5 | 10;
  compact?: boolean;
};

export function normalizeRating(value: number | null | undefined, scale: 5 | 10 = 10) {
  if (value == null || !Number.isFinite(value)) return null;
  return scale === 5 ? value * 2 : value;
}

export function formatRating(value: number | null | undefined, scale: 5 | 10 = 10) {
  const normalized = normalizeRating(value, scale);
  return normalized == null ? '—' : `${normalized.toFixed(1)} / 10`;
}

export function RatingDisplay({ value, scale = 10, compact = false }: RatingDisplayProps) {
  const normalized = normalizeRating(value, scale);
  if (normalized == null) return null;
  return <span className={`rating-display${compact ? ' compact' : ''}`}><Star size={compact ? 11 : 14} fill="currentColor" /> {normalized.toFixed(1)} / 10</span>;
}