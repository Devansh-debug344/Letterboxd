import React, { useEffect, useState } from 'react';
import axios from 'axios';

function MovieRecommend() {
  const [movies, setMovies] = useState([]);
  const [page, setPage] = useState(1); // for pagination
  const [loading, setLoading] = useState(false);

  const fetchMovies = async (pageNum) => {
    setLoading(true);
    try {
      const res = await axios.get(`https://www.omdbapi.com/?apikey=afb3dcd&s=marvel&page=${pageNum}`);
      if (res.data.Search) {
        setMovies(res.data.Search);
      } else {
        setMovies([]);
      }
    } catch (err) {
      console.error('Failed to load movies:', err);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchMovies(page);
  }, [page]);

  return (
    <div className="min-h-screen bg-gray-100 px-4 py-8">
      <h1 className="text-3xl font-bold text-center mb-8">🎥 Recommended Movies</h1>

      {loading ? (
        <p className="text-center text-gray-600">Loading...</p>
      ) : (
        <div className="max-w-6xl mx-auto grid sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {movies.map((movie) => (
            <div
              key={movie.imdbID}
              className="bg-white rounded-lg shadow hover:shadow-lg transition overflow-hidden"
            >
              <img
                src={movie.Poster !== 'N/A' ? movie.Poster : 'https://via.placeholder.com/300x445?text=No+Image'}
                alt={movie.Title}
                className="w-full h-80 object-cover"
              />
              <div className="p-4">
                <h2 className="text-lg font-semibold">{movie.Title}</h2>
                <p className="text-sm text-gray-600">{movie.Year}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination Controls */}
      <div className="flex justify-center mt-10 gap-4">
        <button
          onClick={() => setPage((p) => Math.max(p - 1, 1))}
          disabled={page === 1}
          className="px-4 py-2 bg-gray-300 rounded disabled:opacity-50"
        >
          ⬅ Prev
        </button>
        <span className="px-4 py-2 bg-white border rounded shadow text-gray-700">
          Page {page}
        </span>
        <button
          onClick={() => setPage((p) => p + 1)}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Next ➡
        </button>
      </div>
    </div>
  );
}

export default MovieRecommend;
