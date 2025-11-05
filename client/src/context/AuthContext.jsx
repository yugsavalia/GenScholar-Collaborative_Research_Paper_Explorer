import { createContext, useContext, useState, useEffect } from 'react';
import { storage } from '../utils/storage';
import { STORAGE_KEYS } from '../utils/constants';

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

  useEffect(() => {
    const authData = storage.get(STORAGE_KEYS.AUTH);
    if (authData) {
      setUser(authData);
    }
    setLoading(false);
  }, []);

  const login = (email, password) => {
    const userData = { email, loggedInAt: new Date().toISOString() };
    storage.set(STORAGE_KEYS.AUTH, userData);
    setUser(userData);
    return userData;
  };

  const logout = () => {
    storage.remove(STORAGE_KEYS.AUTH);
    setUser(null);
  };

  const value = {
    user,
    loading,
    login,
    logout,
    isAuthenticated: !!user
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
