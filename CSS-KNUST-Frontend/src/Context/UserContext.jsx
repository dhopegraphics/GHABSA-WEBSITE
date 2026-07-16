import React, { createContext, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

export const UserContext = createContext();

export const UserProvider = ({ children }) => {
  
  const navigate = useNavigate()

  const [user, setUser] = useState(() => {
    const storedUser = localStorage.getItem('user');
    return storedUser ? JSON.parse(storedUser) : null;
  });

  useEffect(() => {
    if (user) {
      localStorage.setItem('user', JSON.stringify(user));
    }
  }, [user]);

  const login = (access, refresh, user) => {
    const userData = { access, refresh, user };
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
  };

  const updateAccessToken = (access) => {
    const updatedUser = { access, refresh:user?.refresh, user:user?.user };
    localStorage.setItem('user', JSON.stringify(updatedUser));
    setUser(updatedUser);
  };

  const logout = useCallback(() => {
    setUser(null);
    localStorage.removeItem('user');
    navigate('/');
  }, [navigate]);

  // Listen for auth:logout events from api.js when token refresh fails
  useEffect(() => {
    const handleAuthLogout = () => {
      logout();
    };

    window.addEventListener('auth:logout', handleAuthLogout);
    return () => {
      window.removeEventListener('auth:logout', handleAuthLogout);
    };
  }, [logout]);

  return (
    <UserContext.Provider value={{ user, login, logout, updateAccessToken }}>
      {children}
    </UserContext.Provider>
  );
};
