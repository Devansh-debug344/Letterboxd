import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Home, 
  Bookmark, 
  MessageSquare, 
  User, 
  LogOut, 
  LogIn, 
  UserPlus,
  Menu,
  X,
  Film,
  Zap
} from 'lucide-react';
import useRazorpay from "../hooks/useRazorpay";

function Navbar() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [activeTab, setActiveTab] = useState(window.location.pathname);
  const { openPayment } = useRazorpay();

  useEffect(() => {
    const token = localStorage.getItem('token');
    setIsLoggedIn(!!token);
  }, []);

  const navigate = (path) => {
    setActiveTab(path);
    setIsMobileMenuOpen(false);
    window.location.pathname = path;
  };

  const logout = () => {
    localStorage.removeItem('token');
    setIsLoggedIn(false);
    navigate('/login');
  };

  const handleUpgrade = () => {
    openPayment({
      amount: 199,
      name: "Letterboxd Pro",
      description: "Monthly subscription",
      onSuccess: (res) => {
        alert("Payment done! ID: " + res.razorpay_payment_id);
      },
    });
  };

  const navItems = isLoggedIn ? [
    { path: '/', label: 'Home', icon: Home },
    { path: '/watchlist', label: 'Watchlist', icon: Bookmark },
    { path: '/reviews', label: 'Reviews', icon: MessageSquare },
    { path: '/profile', label: 'Profile', icon: User },
  ] : [];

  const authItems = isLoggedIn ? [
    { action: logout, label: 'Logout', icon: LogOut, type: 'button' }
  ] : [
    { path: '/login', label: 'Login', icon: LogIn, type: 'link' },
    { path: '/register', label: 'Register', icon: UserPlus, type: 'link' }
  ];

  const navVariants = {
    hidden: { y: -100, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: { duration: 0.6, ease: "easeOut" }
    }
  };

  const mobileMenuVariants = {
    hidden: {
      opacity: 0,
      height: 0,
      transition: { duration: 0.3, ease: "easeInOut" }
    },
    visible: {
      opacity: 1,
      height: "auto",
      transition: { duration: 0.3, ease: "easeInOut" }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: { opacity: 1, x: 0, transition: { duration: 0.3 } }
  };

  const NavLink = ({ item, isMobile = false }) => {
    const isActive = activeTab === item.path;
    const IconComponent = item.icon;

    if (item.type === 'button') {
      return (
        <motion.button
          onClick={item.action}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl font-medium transition-all duration-300 ${
            isMobile 
              ? 'w-full text-left bg-red-500/20 text-red-300 hover:bg-red-500/30' 
              : 'bg-red-500/20 text-red-300 hover:bg-red-500/30'
          }`}
        >
          <IconComponent className="w-4 h-4" />
          {item.label}
        </motion.button>
      );
    }

    return (
      <motion.button
        onClick={() => navigate(item.path)}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className={`relative flex items-center gap-2 px-4 py-2 rounded-xl font-medium transition-all duration-300 ${
          isActive
            ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg'
            : 'text-gray-300 hover:text-white hover:bg-white/10'
        } ${isMobile ? 'w-full text-left' : ''}`}
      >
        <IconComponent className="w-4 h-4" />
        {item.label}
        
        {isActive && (
          <motion.div
            layoutId="activeTab"
            className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl -z-10"
            initial={false}
          />
        )}
      </motion.button>
    );
  };

  return (
    <motion.nav
      variants={navVariants}
      initial="hidden"
      animate="visible"
      className="sticky top-0 z-50 bg-slate-900/95 backdrop-blur-lg border-b border-white/10 shadow-xl"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">

          {/* Logo */}
          <motion.div
            whileHover={{ scale: 1.05 }}
            onClick={() => navigate('/')}
            className="flex items-center gap-3 cursor-pointer"
          >
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
              className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center"
            >
              <Film className="w-5 h-5 text-white" />
            </motion.div>
            <span className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              MovieApp
            </span>
          </motion.div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-2">
            {navItems.map((item, index) => (
              <motion.div
                key={item.path}
                variants={itemVariants}
                initial="hidden"
                animate="visible"
                transition={{ delay: index * 0.1 }}
              >
                <NavLink item={item} />
              </motion.div>
            ))}
          </div>

          {/* Desktop Auth + Upgrade */}
          <div className="hidden md:flex items-center space-x-2">
            {isLoggedIn && (
              <motion.button
                onClick={handleUpgrade}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="flex items-center gap-2 px-4 py-2 rounded-xl font-medium bg-gradient-to-r from-yellow-500 to-orange-500 text-white shadow-lg hover:opacity-90 transition-all duration-300"
              >
                <Zap className="w-4 h-4" />
                Upgrade ₹199
              </motion.button>
            )}
            {authItems.map((item, index) => (
              <motion.div
                key={item.path || item.label}
                variants={itemVariants}
                initial="hidden"
                animate="visible"
                transition={{ delay: (navItems.length + index) * 0.1 }}
              >
                <NavLink item={item} />
              </motion.div>
            ))}
          </div>

          {/* Mobile Menu Button */}
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-2 rounded-lg bg-white/10 text-white hover:bg-white/20 transition-colors"
          >
            <AnimatePresence mode="wait">
              {isMobileMenuOpen ? (
                <motion.div
                  key="close"
                  initial={{ rotate: -90, opacity: 0 }}
                  animate={{ rotate: 0, opacity: 1 }}
                  exit={{ rotate: 90, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <X className="w-5 h-5" />
                </motion.div>
              ) : (
                <motion.div
                  key="menu"
                  initial={{ rotate: 90, opacity: 0 }}
                  animate={{ rotate: 0, opacity: 1 }}
                  exit={{ rotate: -90, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <Menu className="w-5 h-5" />
                </motion.div>
              )}
            </AnimatePresence>
          </motion.button>
        </div>

        {/* Mobile Menu */}
        <AnimatePresence>
          {isMobileMenuOpen && (
            <motion.div
              variants={mobileMenuVariants}
              initial="hidden"
              animate="visible"
              exit="hidden"
              className="md:hidden overflow-hidden bg-slate-800/50 backdrop-blur-lg rounded-xl mt-2 mb-4 border border-white/10"
            >
              <div className="p-4 space-y-2">
                {navItems.map((item, index) => (
                  <motion.div
                    key={item.path}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0, transition: { delay: index * 0.1 } }}
                  >
                    <NavLink item={item} isMobile />
                  </motion.div>
                ))}

                {navItems.length > 0 && (
                  <motion.div
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: 1 }}
                    transition={{ delay: navItems.length * 0.1 }}
                    className="h-px bg-white/20 my-4"
                  />
                )}

                {/* Mobile Upgrade Button */}
                {isLoggedIn && (
                  <motion.button
                    onClick={handleUpgrade}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="w-full flex items-center gap-2 px-4 py-2 rounded-xl font-medium bg-gradient-to-r from-yellow-500 to-orange-500 text-white"
                  >
                    <Zap className="w-4 h-4" />
                    Upgrade ₹199
                  </motion.button>
                )}

                {authItems.map((item, index) => (
                  <motion.div
                    key={item.path || item.label}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0, transition: { delay: (navItems.length + index + 1) * 0.1 } }}
                  >
                    <NavLink item={item} isMobile />
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.nav>
  );
}

export default Navbar;
