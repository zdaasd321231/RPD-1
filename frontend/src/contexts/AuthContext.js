import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../utils/api';
import { toast } from 'sonner';

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
    
    if (token) {
      // Verify token with backend
      verifyToken();
    } else {
      setLoading(false);
    }
  }, []);

  const verifyToken = async () => {
    try {
      const userData = await authAPI.getCurrentUser();
      setUser(userData);
      setIsAuthenticated(true);
    } catch (error) {
      // Token is invalid
      localStorage.removeItem('authToken');
      localStorage.removeItem('userData');
      setIsAuthenticated(false);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password, totpCode = null) => {
    try {
      setLoading(true);
      
      const response = await authAPI.login(username, password, totpCode);
      
      setUser(response.user || { username });
      setIsAuthenticated(true);
      localStorage.setItem('authToken', response.access_token);
      localStorage.setItem('userData', JSON.stringify(response.user || { username }));
      
      return { success: true };
      
    } catch (error) {
      let errorMessage = 'Authentication failed';
      let requiresTOTP = false;
      
      if (error.response?.status === 400 && error.response?.headers?.['x-require-totp']) {
        requiresTOTP = true;
        errorMessage = 'Please enter your 2FA code';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }
      
      return { 
        success: false, 
        error: errorMessage,
        requiresTOTP 
      };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setIsAuthenticated(false);
    setUser(null);
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');
    toast.success('Logged out successfully');
  };

  const updateUser = async () => {
    try {
      const userData = await authAPI.getCurrentUser();
      setUser(userData);
      localStorage.setItem('userData', JSON.stringify(userData));
    } catch (error) {
      console.error('Error updating user data:', error);
    }
  };

  const changePassword = async (currentPassword, newPassword) => {
    try {
      await authAPI.changePassword(currentPassword, newPassword);
      toast.success('Password changed successfully');
      return { success: true };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to change password';
      toast.error(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  const setup2FA = async () => {
    try {
      const response = await authAPI.setup2FA();
      return { success: true, data: response };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to setup 2FA';
      toast.error(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  const enable2FA = async (totpCode) => {
    try {
      await authAPI.enable2FA(totpCode);
      await updateUser(); // Refresh user data
      toast.success('Two-factor authentication enabled');
      return { success: true };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to enable 2FA';
      toast.error(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  const value = {
    isAuthenticated,
    user,
    loading,
    login,
    logout,
    updateUser,
    changePassword,
    setup2FA,
    enable2FA
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};