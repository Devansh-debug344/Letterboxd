import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import Login from './pages/Login';
import Register from './pages/Register';
import Profile from './pages/Profile';
import Watchlist from './pages/Watchlist';
import SearchMovies from './pages/SearchMovies';
import Reviews from './pages/Reviews';
import { useState } from 'react';
import Navbar from './components/Navbar';

import MovieRecommend from './pages/Moviegallery';

function App() {

  const [token, setToken] = useState(localStorage.getItem('token') || '');

  const handleAuthSuccess = (newToken) => {
    localStorage.setItem('token', newToken);
    setToken(newToken);
  };

 

  return (
    <Router>
      <Navbar />
      <div className="p-4">
        <Routes>
          <Route path="/login" element={<Login OnLoginSuccess= {handleAuthSuccess}/>} />
          <Route path="/register" element={<Register/>}  />
           <Route path="/profile" element={<Profile token={token}/>} />
          <Route path="/" element={<SearchMovies  token={token} />}/>
           <Route path="/watchlist" element={<Watchlist token={token} />} />
           <Route path="/reviews" element={<Reviews token={token}/>} />
           <Route path="/movies" element={<MovieRecommend/>} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
