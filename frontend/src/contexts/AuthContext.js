import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { auth } from '../lib/api';
import { clearTokens, setTokens } from '../lib/apiClient';

const AuthContext = createContext({});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token') || localStorage.getItem('access_token'));

  const getPayload = useCallback((response) => response?.data?.data || response?.data || {}, []);

  const logout = useCallback(() => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      auth.logout(refreshToken).catch(() => {});
    }
    clearTokens();
    setToken(null);
    setUser(null);
  }, []);

  const loadUser = useCallback(async () => {
    try {
      const response = await auth.getMe();
      const payload = getPayload(response);
      setUser(payload?.user || payload || null);
    } catch (error) {
      console.error('Failed to load user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  }, [getPayload, logout]);

  useEffect(() => {
    if (token) {
      loadUser();
    } else {
      setLoading(false);
    }
  }, [token, loadUser]);

  const login = useCallback(async (email, password) => {
    const response = await auth.login({ email, password });
    const payload = getPayload(response);
    const accessToken = payload?.access_token || payload?.token || null;
    const refreshToken = payload?.refresh_token || null;
    const userData = payload?.user || null;
    if (!accessToken || !userData) {
      throw new Error('Invalid login response');
    }
    setTokens({ access_token: accessToken, refresh_token: refreshToken });
    setToken(accessToken);
    setUser(userData);
    return userData;
  }, [getPayload]);

  const register = useCallback(async (data) => {
    const response = await auth.register(data);
    const payload = getPayload(response);
    const accessToken = payload?.access_token || payload?.token || null;
    const refreshToken = payload?.refresh_token || null;
    const userData = payload?.user || null;
    if (!accessToken || !userData) {
      throw new Error('Invalid registration response');
    }
    setTokens({ access_token: accessToken, refresh_token: refreshToken });
    setToken(accessToken);
    setUser(userData);
    return userData;
  }, [getPayload]);

  const loginWithToken = useCallback((accessToken, userData) => {
    setTokens({ access_token: accessToken });
    setToken(accessToken);
    setUser(userData);
  }, []);

  const value = useMemo(() => ({
    user,
    loading,
    login,
    register,
    logout,
    loginWithToken,
    isAuthenticated: !!user,
  }), [user, loading, login, register, logout, loginWithToken]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
