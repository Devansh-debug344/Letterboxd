import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Star, Edit3, Trash2, Send, Heart, Calendar, User, Film } from 'lucide-react';

import axios from 'axios';

function Reviews({ token }) {
  const [reviews, setReviews] = useState([]);
  const [movie, setMovie] = useState('');
  const [text, setText] = useState('');
  const [editText, setEditText] = useState({});
  const [likes, setLikes] = useState({});
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const headers = {
    Authorization: `Bearer ${token}`
  };

  const fetchReviews = async () => {
    setLoading(true);
    try {
      const res = await axios.get('/review/', { headers });
      setReviews(res.data);
    } catch (error) {
      console.error("Failed to fetch reviews", error);
    }
    setLoading(false);
  };

  const postReview = async () => {
    if (!movie.trim() || !text.trim()) return;
    
    setIsSubmitting(true);
    try {
      await axios.post(
        '/review/',
        { movie_name: movie, review: text, likes: 0 },
        { headers }
      );
      setMovie('');
      setText('');
      fetchReviews();
    } catch (err) {
      alert(err.response?.data?.detail || 'Review failed');
    }
    setIsSubmitting(false);
  };

  const updateReview = async (movie_name) => {
    try {
      await axios.patch(
        '/review/',
        {
          movie_name,
          review: editText[movie_name] || '',
          likes: likes[movie_name] || 0
        },
        { headers }
      );
      setEditingId(null);
      fetchReviews();
    } catch (err) {
      alert(err.response?.data?.detail || 'Update failed');
    }
  };

  const deleteReview = async (movie_name) => {
    try {
      await axios.delete(
        '/review/',
        {
          data: { movie_name },
          headers
        }
      );
      fetchReviews();
    } catch (err) {
      alert('Delete failed');
    }
  };

  const renderStars = (rating) => {
    const stars = Math.min(Math.floor(rating / 10), 5);
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={`w-4 h-4 ${i < stars ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'}`}
      />
    ));
  };

  useEffect(() => {
    fetchReviews();
  }, []);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const cardVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        type: "spring",
        stiffness: 300,
        damping: 30
      }
    },
    exit: {
      x: -300,
      opacity: 0,
      transition: {
        duration: 0.3
      }
    }
  };

  const formVariants = {
    hidden: { scale: 0.95, opacity: 0 },
    visible: {
      scale: 1,
      opacity: 1,
      transition: {
        type: "spring",
        stiffness: 400,
        damping: 25
      }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ y: -50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="text-center mb-12"
        >
          <div className="flex items-center justify-center gap-3 mb-4">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            >
              <Film className="w-10 h-10 text-purple-400" />
            </motion.div>
            <h1 className="text-5xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              CineReviews
            </h1>
          </div>
          <p className="text-gray-300 text-lg">Share your thoughts on the latest movies</p>
        </motion.div>

        {/* Review Form */}
        <motion.div
          variants={formVariants}
          initial="hidden"
          animate="visible"
          className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 mb-12 border border-white/20 shadow-2xl"
        >
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
            <Edit3 className="w-6 h-6 text-purple-400" />
            Write a Review
          </h2>
          
          <div className="space-y-6">
            <motion.div
              whileFocus={{ scale: 1.02 }}
              className="relative"
            >
              <input
                value={movie}
                onChange={(e) => setMovie(e.target.value)}
                placeholder="Movie title..."
                className="w-full px-4 py-4 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent transition-all duration-300"
              />
              <Film className="absolute right-4 top-4 w-5 h-5 text-gray-400" />
            </motion.div>

            <motion.div
              whileFocus={{ scale: 1.02 }}
              className="relative"
            >
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Share your thoughts about this movie..."
                rows={4}
                className="w-full px-4 py-4 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent transition-all duration-300 resize-none"
              />
            </motion.div>

            <motion.button
              onClick={postReview}
              disabled={isSubmitting || !movie.trim() || !text.trim()}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white py-4 px-6 rounded-xl font-semibold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 shadow-lg hover:shadow-purple-500/25"
            >
              {isSubmitting ? (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
                />
              ) : (
                <>
                  <Send className="w-5 h-5" />
                  Post Review
                </>
              )}
            </motion.button>
          </div>
        </motion.div>

        {/* Reviews List */}
        {loading ? (
          <div className="flex justify-center items-center py-12">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              className="w-12 h-12 border-4 border-purple-400 border-t-transparent rounded-full"
            />
          </div>
        ) : (
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="space-y-6"
          >
            <AnimatePresence>
              {reviews.map((rev, i) => (
                <motion.div
                  key={`${rev.movie_name}-${i}`}
                  variants={cardVariants}
                  layout
                  className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 shadow-xl hover:shadow-2xl transition-all duration-300"
                >
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-xl font-bold text-white">{rev.movie_name}</h3>
                        <div className="flex gap-1">
                          {renderStars(rev.likes)}
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-4 text-sm text-gray-300 mb-3">
                        <span className="flex items-center gap-1">
                          <User className="w-4 h-4" />
                          {rev.user_name}
                        </span>
                        <span className="flex items-center gap-1">
                          <Calendar className="w-4 h-4" />
                          {new Date(rev.updated_at).toLocaleDateString()}
                        </span>
                        <span className="flex items-center gap-1">
                          <Heart className="w-4 h-4 text-red-400" />
                          {rev.likes}
                        </span>
                      </div>
                    </div>
                  </div>

                  <p className="text-gray-200 leading-relaxed mb-6">{rev.review}</p>

                  {editingId === rev.movie_name && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="space-y-4 mb-6"
                    >
                      <textarea
                        placeholder="Edit your review..."
                        value={editText[rev.movie_name] || ''}
                        onChange={(e) => setEditText(prev => ({ ...prev, [rev.movie_name]: e.target.value }))}
                        className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-400 resize-none"
                        rows={3}
                      />
                      <input
                        type="number"
                        placeholder="Likes count"
                        value={likes[rev.movie_name] || ''}
                        onChange={(e) => setLikes(prev => ({ ...prev, [rev.movie_name]: parseInt(e.target.value) || 0 }))}
                        className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-400"
                      />
                    </motion.div>
                  )}

                  <div className="flex gap-3">
                    <motion.button
                      onClick={() => {
                        if (editingId === rev.movie_name) {
                          updateReview(rev.movie_name);
                        } else {
                          setEditingId(rev.movie_name);
                          setEditText(prev => ({ ...prev, [rev.movie_name]: rev.review }));
                          setLikes(prev => ({ ...prev, [rev.movie_name]: rev.likes }));
                        }
                      }}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className={`px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition-all duration-300 ${
                        editingId === rev.movie_name
                          ? 'bg-green-500 hover:bg-green-600 text-white'
                          : 'bg-amber-500 hover:bg-amber-600 text-white'
                      }`}
                    >
                      <Edit3 className="w-4 h-4" />
                      {editingId === rev.movie_name ? 'Save' : 'Edit'}
                    </motion.button>

                    {editingId === rev.movie_name && (
                      <motion.button
                        onClick={() => setEditingId(null)}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg font-medium transition-all duration-300"
                      >
                        Cancel
                      </motion.button>
                    )}

                    <motion.button
                      onClick={() => deleteReview(rev.movie_name)}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium flex items-center gap-2 transition-all duration-300"
                    >
                      <Trash2 className="w-4 h-4" />
                      Delete
                    </motion.button>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.div>
        )}

        {reviews.length === 0 && !loading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-12"
          >
            <Film className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-400 text-lg">No reviews yet. Be the first to share your thoughts!</p>
          </motion.div>
        )}
      </div>
    </div>
  );
}

export default Reviews;
