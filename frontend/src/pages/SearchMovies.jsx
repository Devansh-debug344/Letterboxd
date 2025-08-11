import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, 
  Film, 
  Plus, 
  Star, 
  Calendar, 
  MessageCircle, 
  Send, 
  CheckCircle, 
  AlertCircle, 
  Loader2,
  Heart,
  User,
  Clock
} from 'lucide-react';
import axios from 'axios';

function SearchMovies({ token }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [allReviews, setAllReviews] = useState([]);
  const [newReviews, setNewReviews] = useState({});
  const [isSearching, setIsSearching] = useState(false);
  const [isSubmittingReview, setIsSubmittingReview] = useState({});
  const [isSavingMovie, setIsSavingMovie] = useState({});
  const [message, setMessage] = useState(null);
  const [expandedReviews, setExpandedReviews] = useState({});

  // Search OMDb API
  const searchOMDb = async () => {
    if (!query.trim()) return;
    
    setIsSearching(true);
    setMessage(null);
    
    try {
      const res = await axios.get(`https://www.omdbapi.com/?apikey=afb3dcd&s=${query}`);
      if (res.data.Search) {
        setResults(res.data.Search);
        setMessage({ text: `Found ${res.data.Search.length} movies`, type: 'success' });
      } else {
        setResults([]);
        setMessage({ text: 'No movies found. Try a different search term.', type: 'info' });
      }
    } catch (error) {
      console.error('Search error:', error);
      setMessage({ text: 'Search failed. Please try again.', type: 'error' });
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  // Handle Enter key press
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      searchOMDb();
    }
  };

  // Save movie to watchlist
  const saveMovie = async (title, imdbID) => {
    setIsSavingMovie(prev => ({ ...prev, [imdbID]: true }));
    
    try {
      await axios.post(
        'https://letterboxd-1.onrender.com/watchlist/',
        { movie_name: title },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setMessage({ text: `"${title}" saved to watchlist!`, type: 'success' });
    } catch (error) {
      console.error('Save error:', error);
      if (error.response?.status === 400) {
        setMessage({ text: `"${title}" is already in your watchlist`, type: 'info' });
      } else {
        setMessage({ text: 'Failed to save movie. Please try again.', type: 'error' });
      }
    } finally {
      setIsSavingMovie(prev => ({ ...prev, [imdbID]: false }));
    }
  };

  // Fetch all reviews
  const fetchReviews = async () => {
    try {
      const res = await axios.get('https://letterboxd-1.onrender.com/review/');
      setAllReviews(res.data);
    } catch (error) {
      console.error('Failed to fetch reviews', error);
    }
  };

  useEffect(() => {
    fetchReviews();
  }, []);

  // Handle review input change
  const handleReviewChange = (title, value) => {
    setNewReviews(prev => ({
      ...prev,
      [title]: value,
    }));
  };

  // Submit review
  const submitReview = async (title) => {
    const reviewText = newReviews[title]?.trim();
    if (!reviewText) return;

    setIsSubmittingReview(prev => ({ ...prev, [title]: true }));
    
    try {
      await axios.post(
        'https://letterboxd-1.onrender.com/review/',
        {
          movie_name: title,
          review: reviewText,
          likes: 0,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );
      setMessage({ text: 'Review submitted successfully!', type: 'success' });
      setNewReviews(prev => ({ ...prev, [title]: '' }));
      fetchReviews();
    } catch (error) {
      console.error('Review error:', error);
      if (error.response?.status === 400) {
        setMessage({ text: 'You have already reviewed this movie', type: 'info' });
      } else {
        setMessage({ text: 'Failed to submit review. Please try again.', type: 'error' });
      }
    } finally {
      setIsSubmittingReview(prev => ({ ...prev, [title]: false }));
    }
  };

  // Toggle review expansion
  const toggleReviewExpansion = (movieTitle) => {
    setExpandedReviews(prev => ({
      ...prev,
      [movieTitle]: !prev[movieTitle]
    }));
  };

  // Clear message after timeout
  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => setMessage(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        duration: 0.6,
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  };

  const movieCardVariants = {
    hidden: { opacity: 0, scale: 0.9 },
    visible: { 
      opacity: 1, 
      scale: 1,
      transition: { duration: 0.3 }
    },
    hover: { 
      scale: 1.02,
      transition: { duration: 0.2 }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 p-4">
      {/* Background blur effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-400/20 rounded-full blur-3xl"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-400/20 rounded-full blur-3xl"></div>
      </div>

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="relative max-w-6xl mx-auto"
      >
        {/* Header */}
        <motion.div variants={itemVariants} className="text-center mb-8">
          <motion.div
            className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center mx-auto mb-6"
            whileHover={{ rotate: 360, scale: 1.1 }}
            transition={{ duration: 0.8 }}
          >
            <Film className="w-10 h-10 text-white" />
          </motion.div>
          <h1 className="text-5xl font-bold text-white mb-4 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            🎬 Movie Discovery
          </h1>
          <p className="text-gray-300 text-lg">Discover, save, and review your favorite movies</p>
        </motion.div>

        {/* Search Section */}
        <motion.div 
          variants={itemVariants}
          className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-8 mb-8 shadow-2xl"
        >
          <div className="flex gap-4">
            <div className="relative flex-1">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <Search className="h-6 w-6 text-gray-400" />
              </div>
              <motion.input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Search for movies..."
                className="w-full pl-12 pr-4 py-4 bg-white/5 border border-white/20 backdrop-blur-sm rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 transition-all duration-300 text-lg"
                whileFocus={{ scale: 1.02 }}
                disabled={isSearching}
              />
            </div>
            <motion.button
              onClick={searchOMDb}
              disabled={isSearching || !query.trim()}
              className="bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold py-4 px-8 rounded-xl shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 flex items-center space-x-2 min-w-[140px]"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {isSearching ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Searching...</span>
                </>
              ) : (
                <>
                  <Search className="w-5 h-5" />
                  <span>Search</span>
                </>
              )}
            </motion.button>
          </div>
        </motion.div>

        {/* Message Display */}
        <AnimatePresence>
          {message && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className={`mb-6 p-4 rounded-xl flex items-center space-x-2 ${
                message.type === 'success' 
                  ? 'bg-green-500/20 border border-green-500/30 text-green-300' 
                  : message.type === 'error'
                  ? 'bg-red-500/20 border border-red-500/30 text-red-300'
                  : 'bg-blue-500/20 border border-blue-500/30 text-blue-300'
              }`}
            >
              {message.type === 'success' ? (
                <CheckCircle className="w-5 h-5" />
              ) : message.type === 'error' ? (
                <AlertCircle className="w-5 h-5" />
              ) : (
                <Film className="w-5 h-5" />
              )}
              <span>{message.text}</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Results Grid */}
        <AnimatePresence>
          {results.length > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            >
              {results.map((movie, index) => {
                const movieReviews = allReviews.filter(r => r.movie_name === movie.Title);
                const isExpanded = expandedReviews[movie.Title];
                const displayedReviews = isExpanded ? movieReviews : movieReviews.slice(0, 2);
                
                return (
                  <motion.div
                    key={movie.imdbID}
                    variants={movieCardVariants}
                    initial="hidden"
                    animate="visible"
                    whileHover="hover"
                    transition={{ delay: index * 0.1 }}
                    className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl overflow-hidden shadow-2xl"
                  >
                    {/* Movie Poster */}
                    <div className="relative h-64 bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center">
                      {movie.Poster !== 'N/A' ? (
                        <img 
                          src={movie.Poster} 
                          alt={movie.Title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <Film className="w-16 h-16 text-gray-500" />
                      )}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent"></div>
                    </div>

                    {/* Movie Info */}
                    <div className="p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <h3 className="text-xl font-bold text-white mb-2 line-clamp-2">
                            {movie.Title}
                          </h3>
                          <div className="flex items-center space-x-4 text-gray-300 text-sm">
                            <div className="flex items-center space-x-1">
                              <Calendar className="w-4 h-4" />
                              <span>{movie.Year}</span>
                            </div>
                            <div className="flex items-center space-x-1">
                              <Film className="w-4 h-4" />
                              <span>{movie.Type}</span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Save to Watchlist Button */}
                      {token && (
                        <motion.button
                          onClick={() => saveMovie(movie.Title, movie.imdbID)}
                          disabled={isSavingMovie[movie.imdbID]}
                          className="w-full bg-gradient-to-r from-green-500 to-emerald-500 text-white font-semibold py-3 px-4 rounded-xl shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 flex items-center justify-center space-x-2 mb-4"
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                        >
                          {isSavingMovie[movie.imdbID] ? (
                            <>
                              <Loader2 className="w-4 h-4 animate-spin" />
                              <span>Saving...</span>
                            </>
                          ) : (
                            <>
                              <Plus className="w-4 h-4" />
                              <span>Add to Watchlist</span>
                            </>
                          )}
                        </motion.button>
                      )}

                      {/* Reviews Section */}
                      <div className="border-t border-white/10 pt-4">
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="font-semibold text-white flex items-center space-x-2">
                            <MessageCircle className="w-4 h-4" />
                            <span>Reviews ({movieReviews.length})</span>
                          </h4>
                          {movieReviews.length > 2 && (
                            <motion.button
                              onClick={() => toggleReviewExpansion(movie.Title)}
                              className="text-blue-400 hover:text-blue-300 text-sm transition-colors"
                              whileHover={{ scale: 1.05 }}
                            >
                              {isExpanded ? 'Show Less' : 'Show All'}
                            </motion.button>
                          )}
                        </div>

                        {/* Existing Reviews */}
                        <div className="space-y-2 mb-4 max-h-48 overflow-y-auto">
                          <AnimatePresence>
                            {displayedReviews.length > 0 ? (
                              displayedReviews.map((review, idx) => (
                                <motion.div
                                  key={idx}
                                  initial={{ opacity: 0, height: 0 }}
                                  animate={{ opacity: 1, height: 'auto' }}
                                  exit={{ opacity: 0, height: 0 }}
                                  className="bg-white/5 border border-white/10 rounded-lg p-3"
                                >
                                  <div className="flex items-center space-x-2 mb-2">
                                    <User className="w-4 h-4 text-gray-400" />
                                    <span className="font-medium text-blue-300 text-sm">
                                      {review.user_name}
                                    </span>
                                    <div className="flex items-center space-x-1 text-gray-400">
                                      <Heart className="w-3 h-3" />
                                      <span className="text-xs">{review.likes || 0}</span>
                                    </div>
                                  </div>
                                  <p className="text-gray-300 text-sm leading-relaxed">
                                    {review.review}
                                  </p>
                                </motion.div>
                              ))
                            ) : (
                              <motion.p
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="text-gray-500 text-sm italic text-center py-4"
                              >
                                No reviews yet. Be the first to review!
                              </motion.p>
                            )}
                          </AnimatePresence>
                        </div>

                        {/* Add Review */}
                        {token && (
                          <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="space-y-3"
                          >
                            <div className="relative">
                              <textarea
                                placeholder="Share your thoughts about this movie..."
                                value={newReviews[movie.Title] || ''}
                                onChange={(e) => handleReviewChange(movie.Title, e.target.value)}
                                className="w-full p-3 bg-white/5 border border-white/20 backdrop-blur-sm rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 transition-all duration-300 resize-none"
                                rows="3"
                                disabled={isSubmittingReview[movie.Title]}
                              />
                            </div>
                            <motion.button
                              onClick={() => submitReview(movie.Title)}
                              disabled={isSubmittingReview[movie.Title] || !newReviews[movie.Title]?.trim()}
                              className="w-full bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold py-2 px-4 rounded-lg shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 flex items-center justify-center space-x-2"
                              whileHover={{ scale: 1.02 }}
                              whileTap={{ scale: 0.98 }}
                            >
                              {isSubmittingReview[movie.Title] ? (
                                <>
                                  <Loader2 className="w-4 h-4 animate-spin" />
                                  <span>Submitting...</span>
                                </>
                              ) : (
                                <>
                                  <Send className="w-4 h-4" />
                                  <span>Submit Review</span>
                                </>
                              )}
                            </motion.button>
                          </motion.div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Empty State */}
        {!isSearching && results.length === 0 && query && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-16"
          >
            <Film className="w-24 h-24 text-gray-500 mx-auto mb-4" />
            <h3 className="text-2xl font-semibold text-white mb-2">No movies found</h3>
            <p className="text-gray-400">Try searching with different keywords</p>
          </motion.div>
        )}

        {/* Welcome State */}
        {!query && results.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-16"
          >
            <div className="bg-white/5 backdrop-blur-xl border border-white/20 rounded-2xl p-12 max-w-2xl mx-auto">
              <Search className="w-24 h-24 text-blue-400 mx-auto mb-6" />
              <h3 className="text-3xl font-semibold text-white mb-4">Start Your Movie Journey</h3>
              <p className="text-gray-300 text-lg mb-6">
                Search for any movie, add it to your watchlist, and share your reviews with the community
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div className="flex items-center space-x-2 text-gray-400">
                  <Search className="w-4 h-4 text-blue-400" />
                  <span>Search movies</span>
                </div>
                <div className="flex items-center space-x-2 text-gray-400">
                  <Plus className="w-4 h-4 text-green-400" />
                  <span>Save to watchlist</span>
                </div>
                <div className="flex items-center space-x-2 text-gray-400">
                  <MessageCircle className="w-4 h-4 text-purple-400" />
                  <span>Write reviews</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}

export default SearchMovies;
