import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './components/AppShell';
import { useAuthStore } from './stores/auth';
import { DiaryPage } from './pages/DiaryPage';
import { HomePage } from './pages/HomePage';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { MoviePage } from './pages/MoviePage';
import { ProfilePage } from './pages/ProfilePage';
import { RegisterPage } from './pages/RegisterPage';
import { ReviewEditorPage } from './pages/ReviewEditorPage';
import { SearchPage } from './pages/SearchPage';
import { SettingsPage } from './pages/SettingsPage';
import { WatchlistPage } from './pages/WatchlistPage';

function Protected({ children }: { children: React.ReactNode }) {
  return useAuthStore((s) => s.accessToken) ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  return <Routes>
    <Route path="/" element={<LandingPage />} />
    <Route path="/login" element={<LoginPage />} />
    <Route path="/register" element={<RegisterPage />} />
    <Route path="/film/:imdbId" element={<AppShell><MoviePage /></AppShell>} />
    <Route path="/search" element={<AppShell><SearchPage /></AppShell>} />
    <Route path="/home" element={<Protected><AppShell><HomePage /></AppShell></Protected>} />
    <Route path="/watchlist" element={<Protected><AppShell><WatchlistPage /></AppShell></Protected>} />
    <Route path="/diary" element={<Protected><AppShell><DiaryPage /></AppShell></Protected>} />
    <Route path="/review/:imdbId" element={<Protected><AppShell><ReviewEditorPage /></AppShell></Protected>} />
    <Route path="/profile" element={<Protected><AppShell><ProfilePage /></AppShell></Protected>} />
    <Route path="/u/:userId" element={<AppShell><ProfilePage /></AppShell>} />
    <Route path="/settings" element={<Protected><AppShell><SettingsPage /></AppShell></Protected>} />
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>;
}
