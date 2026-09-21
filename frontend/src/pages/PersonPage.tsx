import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, CalendarDays, MapPin } from 'lucide-react';
import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { getPerson } from '../api/movies';
import { isNotFoundError } from '../api/client';
import type { PersonCredit } from '../api/types';
import { HorizontalRail } from '../components/HorizontalRail';
import { PosterCard, PosterSkeleton } from '../components/PosterCard';

function ProfileImage({ name, src }: { name: string; src?: string | null }) {
  const [hasImage, setHasImage] = useState(Boolean(src));
  return hasImage ? <img className="person-profile-image" src={src || undefined} alt={`${name} portrait`} onError={() => setHasImage(false)} /> : <div className="person-profile-image person-profile-fallback" aria-label={`${name} portrait placeholder`}>{name.slice(0, 1)}</div>;
}

function CreditCard({ credit }: { credit: PersonCredit }) {
  const title = credit.Title || credit.title || 'Untitled film';
  return <Link className="filmography-credit" to={`/film/${credit.imdbID || credit.imdb_id || credit.id}`}>
    {credit.Poster && credit.Poster !== 'N/A' ? <img src={credit.Poster} alt={`${title} poster`} loading="lazy" /> : <div className="filmography-poster-fallback">{title}</div>}
    <div className="filmography-credit-copy"><strong>{title}</strong><span>{credit.Year || credit.year || 'Year unknown'}</span><small>{credit.characters?.length ? credit.characters.join(', ') : credit.roles.join(' · ')}</small></div>
  </Link>;
}

export function PersonPage() {
  const { personId = '' } = useParams();
  const person = useQuery({ queryKey: ['person', personId], queryFn: () => getPerson(personId), enabled: Boolean(personId) });
  const [expanded, setExpanded] = useState(false);
  const [filter, setFilter] = useState('All');
  if (person.isLoading || !personId) return <section className="person-page person-loading page-enter"><div className="person-profile-image skeleton" /><div className="person-loading-copy skeleton" /></section>;
  if (person.isError && isNotFoundError(person.error)) return <section className="page empty">That person couldn&apos;t be found. <Link to="/search">Search films</Link></section>;
  if (person.isError || !person.data) return <section className="page empty">This person is temporarily unavailable. Please try again shortly.</section>;
  const profile = person.data;
  const biography = profile.biography?.trim();
  const sectionFor = (roles: string[]) => roles.some((role) => role === 'Acting') ? 'Acting' : roles.some((role) => /director/i.test(role)) ? 'Directing' : roles.some((role) => /writer|screenplay/i.test(role)) ? 'Writing' : roles.some((role) => /producer/i.test(role)) ? 'Production' : 'Other';
  const filtered = filter === 'All' ? profile.filmography : profile.filmography.filter((credit) => sectionFor(credit.roles) === filter);
  const grouped = filtered.reduce<Record<string, PersonCredit[]>>((groups, credit) => { const key = sectionFor(credit.roles); (groups[key] ||= []).push(credit); return groups; }, {});
  const filters = ['All', 'Acting', 'Directing', 'Writing', 'Production', 'Other'];
  return <section className="person-page page-enter">
    <Link className="back person-back" to="/search"><ArrowLeft size={15} /> Explore films</Link>
    <header className="person-hero"><ProfileImage name={profile.name} src={profile.profile} /><div className="person-hero-copy"><p className="eyebrow">THE FILM UNIVERSE</p><h1>{profile.name}</h1><p className="person-profession">{profile.known_for_department || 'Film professional'}</p><div className="person-facts">{profile.birthday && <span><CalendarDays size={14} /> Born {profile.birthday}</span>}{profile.place_of_birth && <span><MapPin size={14} /> {profile.place_of_birth}</span>}</div></div></header>
    {biography && <section className="person-biography"><div className="section-heading"><div><p className="eyebrow">IN THEIR WORDS</p><h2>Biography</h2></div></div><p className={expanded ? '' : 'biography-collapsed'}>{biography}</p>{biography.length > 420 && <button type="button" className="text-button" onClick={() => setExpanded((value) => !value)}>{expanded ? 'Read less' : 'Read more'}</button>}</section>}
    {profile.known_for.length > 0 && <section className="person-known-for"><div className="section-heading"><div><p className="eyebrow">A LIFE IN FILM</p><h2>Known for</h2></div></div><HorizontalRail labelledBy="known-for-rail"><div className="person-poster-row">{profile.known_for.map((credit) => <PosterCard key={credit.id || credit.imdbID} movie={credit} />)}</div></HorizontalRail></section>}
    <section className="person-filmography"><div className="section-heading"><div><p className="eyebrow">THE WORK</p><h2>Filmography</h2></div><span>{profile.filmography.length} credits</span></div><div className="filmography-filters" role="tablist" aria-label="Filmography filters">{filters.map((item) => <button key={item} type="button" className={filter === item ? 'active' : ''} onClick={() => setFilter(item)}>{item}</button>)}</div>{Object.keys(grouped).length ? Object.entries(grouped).map(([role, credits]) => <section className="filmography-group" key={role}><h3>{role}</h3><div className="filmography-list">{credits.map((credit) => <CreditCard key={credit.id || credit.imdbID} credit={credit} />)}</div></section>) : <p className="empty">No filmography credits are available.</p>}</section>
  </section>;
}

export function PersonSkeletons() { return <div>{Array.from({ length: 4 }, (_, index) => <PosterSkeleton key={index} />)}</div>; }