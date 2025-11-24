import { createContext, useContext, useState, useEffect } from 'react';
import { login as apiLogin, signup as apiSignup, logout as apiLogout, getCurrentUser } from '../api/auth.js';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check if user is authenticated on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const currentUser = await getCurrentUser();
        if (currentUser) {
          setUser(currentUser);
        }
      } catch (error) {
        console.error('Error checking authentication:', error);
        // If there's an error (not 401), set user to null
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (email, password) => {
    try {
      // Use email as username for API (Django User model uses username)
      const userData = await apiLogin(email, password);
      setUser(userData);
      return userData;
    } catch (error) {
      // Re-throw error so caller can handle it
      throw error;
    }
  };

  const signup = async (email, password1, password2) => {
    try {
      // Use email as username for API (Django User model uses username)
      const userData = await apiSignup(email, password1, password2);
      setUser(userData);
      return userData;
    } catch (error) {
      // Re-throw error so caller can handle it
      throw error;
    }
  };

  const logout = async () => {
    try {
      await apiLogout();
      setUser(null);
    } catch (error) {
      console.error('Error logging out:', error);
      // Even if logout fails, clear local state
      setUser(null);
      // Re-throw error so caller can handle it
      throw error;
    }
  };

  const value = {
    user,
    loading,
    login,
    signup,
    logout,
    isAuthenticated: !!user
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
