import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Bookmark, 
  Eye, 
  EyeOff, 
  Star, 
  Save, 
  Trash2, 
  StickyNote, 
  Film,
  Clock,
  CheckCircle,
  Play
} from 'lucide-react';

function Watchlist({ token }) {
  const [list, setList] = useState([]);
  const [editableData, setEditableData] = useState({});
  const [loading, setLoading] = useState(false);
  const [savingItems, setSavingItems] = useState({});

  const fetchList = async () => {
    setLoading(true);
    try {
      const res = await axios.get('/api/watchlist/', {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      setList(res.data);

      // Set local edit state
      const initialData = {};
      res.data.forEach(item => {
        initialData[item.movie_name] = {
          note: item.note || '',
          rating: item.rating || '',
          status: item.status || 'unwatched',
        };
      });
      setEditableData(initialData);
    } catch (error) {
      console.error('Failed to fetch watchlist', error);
    }
    setLoading(false);
  };

  const saveChanges = async (movie_name) => {
    setSavingItems(prev => ({ ...prev, [movie_name]: true }));
    try {
      const raw = editableData[movie_name];
      const payload = { movie_name };

      if (raw.note && raw.note.trim()) {
        payload.note = raw.note.trim();
      }

      if (raw.status && raw.status.trim()) {
        payload.status = raw.status.trim();
      }

      if (raw.rating !== '' && !isNaN(raw.rating)) {
        payload.rating = parseFloat(raw.rating);
      }

      await axios.patch('/api/watchlist/', payload, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      fetchList();
    } catch (error) {
      console.error("Failed to update item:", error.response?.data || error);
      alert("Failed to update");
    }
    setSavingItems(prev => ({ ...prev, [movie_name]: false }));
  };

  const deleteItem = async (movie_name) => {
    try {
      await axios.delete('/api/watchlist/', {
        headers: {
          Authorization: `Bearer ${token}`
        },
        data: { movie_name }
      });
      fetchList();
    } catch (error) {
      alert("Failed to delete");
      console.log('Failed to delete item', error);
    }
  };

  const renderStars = (rating) => {
    const stars = Math.min(Math.max(Math.floor(rating || 0), 0), 5);
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={`w-4 h-4 ${i < stars ? 'fill-yellow-400 text-yellow-400' : 'text-gray-400'}`}
      />
    ));
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'watched':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'unwatched':
        return <Clock className="w-5 h-5 text-orange-400" />;
      default:
        return <Play className="w-5 h-5 text-blue-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'watched':
        return 'from-green-500 to-emerald-500';
      case 'unwatched':
        return 'from-orange-500 to-amber-500';
      default:
        return 'from-blue-500 to-cyan-500';
    }
  };

  useEffect(() => {
    if (token) fetchList();
  }, [token]);

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
    hidden: { y: 20, opacity: 0, scale: 0.95 },
    visible: {
      y: 0,
      opacity: 1,
      scale: 1,
      transition: {
        type: "spring",
        stiffness: 300,
        damping: 30
      }
    },
    exit: {
      x: -300,
      opacity: 0,
      scale: 0.8,
      transition: {
        duration: 0.3
      }
    }
  };

  const headerVariants = {
    hidden: { y: -50, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        duration: 0.6,
        ease: "easeOut"
      }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-900 to-slate-900 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div
          variants={headerVariants}
          initial="hidden"
          animate="visible"
          className="text-center mb-12"
        >
          <div className="flex items-center justify-center gap-3 mb-4">
            <motion.div
              animate={{ rotate: [0, 10, -10, 0] }}
              transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            >
              <Bookmark className="w-10 h-10 text-indigo-400" />
            </motion.div>
            <h1 className="text-5xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              My Watchlist
            </h1>
          </div>
          <p className="text-gray-300 text-lg">Keep track of movies you want to watch</p>
          
          {/* Stats */}
          <div className="flex justify-center gap-8 mt-8">
            <div className="text-center">
              <div className="text-2xl font-bold text-white">
                {list.filter(item => editableData[item.movie_name]?.status === 'watched').length}
              </div>
              <div className="text-sm text-gray-400">Watched</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-white">
                {list.filter(item => editableData[item.movie_name]?.status === 'unwatched').length}
              </div>
              <div className="text-sm text-gray-400">To Watch</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-white">{list.length}</div>
              <div className="text-sm text-gray-400">Total</div>
            </div>
          </div>
        </motion.div>

        {/* Loading State */}
        {loading ? (
          <div className="flex justify-center items-center py-12">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              className="w-12 h-12 border-4 border-indigo-400 border-t-transparent rounded-full"
            />
          </div>
        ) : (
          /* Watchlist Items */
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="space-y-6"
          >
            <AnimatePresence>
              {list.map((item) => {
                const itemData = editableData[item.movie_name] || {};
                const isSaving = savingItems[item.movie_name];
                
                return (
                  <motion.div
                    key={item.movie_id}
                    variants={cardVariants}
                    layout
                    className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 shadow-xl hover:shadow-2xl transition-all duration-300"
                  >
                    {/* Movie Header */}
                    <div className="flex items-center justify-between mb-6">
                      <div className="flex items-center gap-3">
                        <Film className="w-6 h-6 text-indigo-400" />
                        <h3 className="text-xl font-bold text-white">{item.movie_name}</h3>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {getStatusIcon(itemData.status)}
                        <span className={`px-3 py-1 rounded-full text-sm font-medium bg-gradient-to-r ${getStatusColor(itemData.status)} text-white`}>
                          {itemData.status?.charAt(0).toUpperCase() + itemData.status?.slice(1)}
                        </span>
                      </div>
                    </div>

                    {/* Rating Display */}
                    {itemData.rating && (
                      <div className="flex items-center gap-2 mb-4">
                        <span className="text-gray-300 text-sm">Your Rating:</span>
                        <div className="flex gap-1">
                          {renderStars(itemData.rating)}
                        </div>
                        <span className="text-yellow-400 font-semibold ml-2">
                          {itemData.rating}/5
                        </span>
                      </div>
                    )}

                    {/* Note Display */}
                    {itemData.note && (
                      <div className="mb-6 p-4 bg-white/5 rounded-xl border border-white/10">
                        <div className="flex items-start gap-2">
                          <StickyNote className="w-4 h-4 text-yellow-400 mt-1" />
                          <p className="text-gray-200 text-sm leading-relaxed">{itemData.note}</p>
                        </div>
                      </div>
                    )}

                    {/* Edit Form */}
                    <div className="space-y-4">
                      {/* Status Selector */}
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-300 flex items-center gap-2">
                          <Eye className="w-4 h-4" />
                          Watch Status
                        </label>
                        <motion.select
                          whileFocus={{ scale: 1.02 }}
                          value={itemData.status || 'unwatched'}
                          onChange={(e) =>
                            setEditableData(prev => ({
                              ...prev,
                              [item.movie_name]: {
                                ...prev[item.movie_name],
                                status: e.target.value
                              }
                            }))
                          }
                          className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent transition-all duration-300"
                        >
                          <option value="unwatched" className="bg-gray-800">Unwatched</option>
                          <option value="watched" className="bg-gray-800">Watched</option>
                        </motion.select>
                      </div>

                      {/* Note Input */}
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-300 flex items-center gap-2">
                          <StickyNote className="w-4 h-4" />
                          Notes
                        </label>
                        <motion.textarea
                          whileFocus={{ scale: 1.02 }}
                          placeholder="Add your thoughts about this movie..."
                          value={itemData.note || ''}
                          onChange={(e) =>
                            setEditableData(prev => ({
                              ...prev,
                              [item.movie_name]: {
                                ...prev[item.movie_name],
                                note: e.target.value
                              }
                            }))
                          }
                          rows={3}
                          className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent transition-all duration-300 resize-none"
                        />
                      </div>

                      {/* Rating Input */}
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-300 flex items-center gap-2">
                          <Star className="w-4 h-4" />
                          Rating (1-5)
                        </label>
                        <motion.input
                          whileFocus={{ scale: 1.02 }}
                          type="number"
                          min="1"
                          max="5"
                          step="0.1"
                          placeholder="Rate this movie..."
                          value={itemData.rating || ''}
                          onChange={(e) =>
                            setEditableData(prev => ({
                              ...prev,
                              [item.movie_name]: {
                                ...prev[item.movie_name],
                                rating: e.target.value
                              }
                            }))
                          }
                          className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent transition-all duration-300"
                        />
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3 mt-6">
                      <motion.button
                        onClick={() => saveChanges(item.movie_name)}
                        disabled={isSaving}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className="flex-1 bg-gradient-to-r from-green-500 to-emerald-500 text-white py-3 px-6 rounded-xl font-semibold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 shadow-lg hover:shadow-green-500/25"
                      >
                        {isSaving ? (
                          <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                            className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
                          />
                        ) : (
                          <>
                            <Save className="w-5 h-5" />
                            Save Changes
                          </>
                        )}
                      </motion.button>

                      <motion.button
                        onClick={() => deleteItem(item.movie_name)}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className="px-6 py-3 bg-gradient-to-r from-red-500 to-rose-500 text-white rounded-xl font-semibold flex items-center gap-2 transition-all duration-300 shadow-lg hover:shadow-red-500/25"
                      >
                        <Trash2 className="w-5 h-5" />
                        Remove
                      </motion.button>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </motion.div>
        )}

        {/* Empty State */}
        {list.length === 0 && !loading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-12"
          >
            <Bookmark className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-400 text-lg mb-2">Your watchlist is empty</p>
            <p className="text-gray-500">Start adding movies you want to watch!</p>
          </motion.div>
        )}
      </div>
    </div>
  );
}

export default Watchlist;
