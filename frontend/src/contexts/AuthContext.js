import React, { createContext, useContext, useState, useEffect } from 'react';
import { mockAuth } from '../utils/mockData';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in on app start
    const token = localStorage.getItem('authToken');
    const userData = localStorage.getItem('userData');
    
    if (token && userData) {
      setUser(JSON.parse(userData));
      setIsAuthenticated(true);
    }
    setLoading(false);
  }, []);

  const login = async (username, password, totpCode = null) => {
    try {
      setLoading(true);
      
      // Mock authentication
      const result = await mockAuth.login(username, password, totpCode);
      
      if (result.success) {
        setUser(result.user);
        setIsAuthenticated(true);
        localStorage.setItem('authToken', result.token);
        localStorage.setItem('userData', JSON.stringify(result.user));
        return { success: true };
      } else {
        return { success: false, error: result.error, requiresTOTP: result.requiresTOTP };
      }
    } catch (error) {
      return { success: false, error: 'Authentication failed' };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setIsAuthenticated(false);
    setUser(null);
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');
  };

  const value = {
    isAuthenticated,
    user,
    loading,
    login,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};