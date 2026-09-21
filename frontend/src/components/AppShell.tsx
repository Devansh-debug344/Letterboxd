import { Film, Search, BookOpen, UserRound, Bookmark, Home } from 'lucide-react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { useEffect, useState } from 'react';

export function AppShell({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const [navigating, setNavigating] = useState(false);
  useEffect(() => { const timer = window.setTimeout(() => setNavigating(false), 240); return () => window.clearTimeout(timer); }, [location.pathname]);
  const item = ({ isActive }: { isActive: boolean }) => `nav-item ${isActive ? 'active' : ''}`;

  return (
    <div className="app-shell">
      {navigating && <div className="route-progress" aria-label="Loading page" />}
      <header className="topbar">
        <Link className="wordmark" to="/home">
          <Film size={19} /> Letterboxd
        </Link>
        <nav>
          <NavLink to="/home" className={item} onClick={() => setNavigating(true)}>
            <Home /> <span>Home</span>
          </NavLink>
          <NavLink to="/search" className={item} onClick={() => setNavigating(true)}>
            <Search /> <span>Search</span>
          </NavLink>
          <NavLink to="/diary" className={item} onClick={() => setNavigating(true)}>
            <BookOpen /> <span>Diary</span>
          </NavLink>
          <NavLink to="/watchlist" className={item} onClick={() => setNavigating(true)}>
            <Bookmark /> <span>Watchlist</span>
          </NavLink>
          <NavLink to="/profile" className={item} onClick={() => setNavigating(true)}>
            <UserRound /> <span>Profile</span>
          </NavLink>
        </nav>
      </header>
      <main>{children}</main>
    </div>
  );
}
