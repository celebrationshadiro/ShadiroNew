import React, { createContext, useContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { auth } from '../services/api';

const AuthContext = createContext({});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUser();
  }, []);

  const getPayload = (response) => response?.data?.data || response?.data || {};

  const loadUser = async () => {
    try {
      const token = await AsyncStorage.getItem('token');
      if (token) {
        const response = await auth.getMe();
        const payload = getPayload(response);
        setUser(payload?.user || payload || null);
      }
    } catch (error) {
      console.error('Failed to load user:', error);
      await logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    const response = await auth.login({ email, password });
    const payload = getPayload(response);
    const accessToken = payload?.access_token || payload?.token || null;
    const userData = payload?.user || null;
    if (!accessToken || !userData) {
      throw new Error('Invalid login response');
    }
    await AsyncStorage.setItem('token', accessToken);
    setUser(userData);
    return userData;
  };

  const register = async (data) => {
    const response = await auth.register(data);
    const payload = getPayload(response);
    const accessToken = payload?.access_token || payload?.token || null;
    const userData = payload?.user || null;
    if (!accessToken || !userData) {
      throw new Error('Invalid registration response');
    }
    await AsyncStorage.setItem('token', accessToken);
    setUser(userData);
    return userData;
  };

  const logout = async () => {
    await AsyncStorage.removeItem('token');
    setUser(null);
  };

  const role = user?.role || 'user';

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        role,
        isAuthenticated: !!user,
        isVendor: role === 'vendor',
        isAdmin: role === 'admin',
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
