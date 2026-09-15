import { Film, Search, BookOpen, UserRound, Bookmark, Home } from 'lucide-react';
import { Link, NavLink } from 'react-router-dom';

export function AppShell({ children }: { children: React.ReactNode }) {
  const item = ({ isActive }: { isActive: boolean }) => `nav-item ${isActive ? 'active' : ''}`;

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link className="wordmark" to="/home">
          <Film size={19} /> Letterboxd
        </Link>
        <nav>
          <NavLink to="/home" className={item}>
            <Home /> <span>Home</span>
          </NavLink>
          <NavLink to="/search" className={item}>
            <Search /> <span>Search</span>
          </NavLink>
          <NavLink to="/diary" className={item}>
            <BookOpen /> <span>Diary</span>
          </NavLink>
          <NavLink to="/watchlist" className={item}>
            <Bookmark /> <span>Watchlist</span>
          </NavLink>
          <NavLink to="/profile" className={item}>
            <UserRound /> <span>Profile</span>
          </NavLink>
        </nav>
      </header>
      <main>{children}</main>
    </div>
  );
}
