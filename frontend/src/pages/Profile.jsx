/import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { 
  User, 
  Mail, 
  Calendar, 
  Edit3, 
  Save, 
  X, 
  UserCircle,
  Shield,
  Clock,
  CheckCircle
} from 'lucide-react';

function Profile({ token }) {
  const [user, setUser] = useState({ username: '', email: '', joined_at: '' });
  const [editMode, setEditMode] = useState(false);
  const [updatedData, setUpdatedData] = useState({ username: '', email: '' });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  useEffect(() => {
    const fetchProfile = async () => {
      setLoading(true);
      try {
        const response = await axios.get('/api/user/profile', {
          headers: { Authorization: `Bearer ${token}` },
        });
        // With axios, data is already parsed - no need for .json()
        const userData = response.data;
        
        setUser(userData);
        setUpdatedData({ 
          username: userData.username, 
          email: userData.email, 
          joined_at: userData.joined_at 
        });
      } catch (error) {
        alert("Problem in fetching profile");
        console.log(error);
      }
      setLoading(false);
    };

    if (token) fetchProfile();
  }, [token]);

  const handleUpdate = async (e) => {
    e.preventDefault();
    setSaving(true);
    
    try {
      // Correct axios PATCH syntax
      const response = await axios.patch('/api/user/profile', updatedData, {
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      // With axios, data is already parsed
      const userData = response.data;
      
      setUser({ 
        username: userData.username, 
        email: userData.email, 
        joined_at: userData.joined_at 
      });
      
      setEditMode(false);
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
    } catch (error) {
      alert('Failed to update profile');
      console.error(error);
    }
    setSaving(false);
  };

  const calculateDaysJoined = (joinedDate) => {
    if (!joinedDate) return 0;
    const joined = new Date(joinedDate);
    const now = new Date();
    const diffTime = Math.abs(now - joined);
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  };

  const containerVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.6,
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: {
      opacity: 1,
      x: 0,
      transition: {
        duration: 0.5
      }
    }
  };

  const cardVariants = {
    hidden: { scale: 0.9, opacity: 0 },
    visible: {
      scale: 1,
      opacity: 1,
      transition: {
        type: "spring",
        stiffness: 300,
        damping: 30
      }
    }
  };

  const formVariants = {
    hidden: { opacity: 0, scale: 0.95 },
    visible: {
      opacity: 1,
      scale: 1,
      transition: {
        duration: 0.3
      }
    },
    exit: {
      opacity: 0,
      scale: 0.95,
      transition: {
        duration: 0.2
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            className="w-16 h-16 border-4 border-blue-400 border-t-transparent rounded-full mx-auto mb-4"
          />
          <p className="text-white text-lg">Loading your profile...</p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 p-6">
      <div className="max-w-2xl mx-auto">
        {/* Success Notification */}
        <AnimatePresence>
          {showSuccess && (
            <motion.div
              initial={{ opacity: 0, y: -50, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -50, scale: 0.9 }}
              className="fixed top-6 right-6 bg-green-500 text-white px-6 py-3 rounded-xl shadow-lg flex items-center gap-2 z-50"
            >
              <CheckCircle className="w-5 h-5" />
              Profile updated successfully!
            </motion.div>
          )}
        </AnimatePresence>

        {/* Header */}
        <motion.div
          initial={{ y: -50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="text-center mb-12"
        >
          <div className="flex items-center justify-center gap-3 mb-4">
            <motion.div
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            >
              <UserCircle className="w-12 h-12 text-blue-400" />
            </motion.div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
              Your Profile
            </h1>
          </div>
          <p className="text-gray-300">Manage your account information</p>
        </motion.div>

        {/* Profile Card */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="bg-white/10 backdrop-blur-lg rounded-3xl p-8 border border-white/20 shadow-2xl"
        >
          {/* Avatar Section */}
          <motion.div 
            variants={itemVariants}
            className="flex flex-col items-center mb-8"
          >
            <motion.div
              whileHover={{ scale: 1.1 }}
              className="w-24 h-24 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full flex items-center justify-center mb-4 shadow-lg"
            >
              <User className="w-12 h-12 text-white" />
            </motion.div>
            <h2 className="text-2xl font-bold text-white mb-2">{user.username}</h2>
            <div className="flex items-center gap-2 text-gray-300">
              <Shield className="w-4 h-4" />
              <span className="text-sm">Verified Member</span>
            </div>
          </motion.div>

          {/* Stats */}
          <motion.div 
            variants={itemVariants}
            className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8"
          >
            <div className="bg-white/5 rounded-xl p-4 border border-white/10">
              <div className="flex items-center gap-3">
                <Calendar className="w-6 h-6 text-blue-400" />
                <div>
                  <p className="text-gray-400 text-sm">Member Since</p>
                  <p className="text-white font-semibold">
                    {new Date(user.joined_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="bg-white/5 rounded-xl p-4 border border-white/10">
              <div className="flex items-center gap-3">
                <Clock className="w-6 h-6 text-green-400" />
                <div>
                  <p className="text-gray-400 text-sm">Days Active</p>
                  <p className="text-white font-semibold">
                    {calculateDaysJoined(user.joined_at)} days
                  </p>
                </div>
              </div>
            </div>
          </motion.div>

          <AnimatePresence mode="wait">
            {editMode ? (
              /* Edit Form */
              <motion.form
                key="edit-form"
                variants={formVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                onSubmit={handleUpdate}
                className="space-y-6"
              >
                <motion.div variants={itemVariants} className="space-y-2">
                  <label className="text-sm font-medium text-gray-300 flex items-center gap-2">
                    <User className="w-4 h-4" />
                    Username
                  </label>
                  <motion.input
                    whileFocus={{ scale: 1.02 }}
                    type="text"
                    value={updatedData.username}
                    onChange={(e) => setUpdatedData({ ...updatedData, username: e.target.value })}
                    placeholder="Enter your username"
                    className="w-full px-4 py-4 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-all duration-300"
                    required
                  />
                </motion.div>

                <motion.div variants={itemVariants} className="space-y-2">
                  <label className="text-sm font-medium text-gray-300 flex items-center gap-2">
                    <Mail className="w-4 h-4" />
                    Email Address
                  </label>
                  <motion.input
                    whileFocus={{ scale: 1.02 }}
                    type="email"
                    value={updatedData.email}
                    onChange={(e) => setUpdatedData({ ...updatedData, email: e.target.value })}
                    placeholder="Enter your email"
                    className="w-full px-4 py-4 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-all duration-300"
                    required
                  />
                </motion.div>

                <motion.div 
                  variants={itemVariants}
                  className="flex gap-4 pt-4"
                >
                  <motion.button
                    type="submit"
                    disabled={saving}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="flex-1 bg-gradient-to-r from-green-500 to-emerald-500 text-white py-4 px-6 rounded-xl font-semibold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 shadow-lg hover:shadow-green-500/25"
                  >
                    {saving ? (
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
                    type="button"
                    onClick={() => setEditMode(false)}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="px-6 py-4 bg-gray-600 hover:bg-gray-700 text-white rounded-xl font-semibold flex items-center gap-2 transition-all duration-300"
                  >
                    <X className="w-5 h-5" />
                    Cancel
                  </motion.button>
                </motion.div>
              </motion.form>
            ) : (
              /* Profile Display */
              <motion.div
                key="profile-display"
                variants={formVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                className="space-y-6"
              >
                <motion.div variants={itemVariants} className="space-y-4">
                  <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                    <div className="flex items-center gap-3 mb-3">
                      <User className="w-5 h-5 text-blue-400" />
                      <span className="text-gray-400 text-sm font-medium">USERNAME</span>
                    </div>
                    <p className="text-white text-lg font-semibold">{user.username}</p>
                  </div>

                  <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                    <div className="flex items-center gap-3 mb-3">
                      <Mail className="w-5 h-5 text-blue-400" />
                      <span className="text-gray-400 text-sm font-medium">EMAIL</span>
                    </div>
                    <p className="text-white text-lg font-semibold">{user.email}</p>
                  </div>

                  <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                    <div className="flex items-center gap-3 mb-3">
                      <Calendar className="w-5 h-5 text-blue-400" />
                      <span className="text-gray-400 text-sm font-medium">JOINED</span>
                    </div>
                    <p className="text-white text-lg font-semibold">
                      {new Date(user.joined_at).toLocaleDateString('en-US', {
                        weekday: 'long',
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                      })}
                    </p>
                  </div>
                </motion.div>

                <motion.button
                  variants={itemVariants}
                  onClick={() => setEditMode(true)}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full bg-gradient-to-r from-blue-500 to-cyan-500 text-white py-4 px-6 rounded-xl font-semibold flex items-center justify-center gap-2 transition-all duration-300 shadow-lg hover:shadow-blue-500/25"
                >
                  <Edit3 className="w-5 h-5" />
                  Edit Profile
                </motion.button>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </div>
  );
}

export default Profile;
