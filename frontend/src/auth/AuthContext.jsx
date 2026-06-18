import { createContext, useContext, useState, useCallback } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('chronic_user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const login = useCallback((tokenResponse) => {
    localStorage.setItem('chronic_token', tokenResponse.access_token);
    localStorage.setItem('chronic_user', JSON.stringify(tokenResponse));
    setUser(tokenResponse);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('chronic_token');
    localStorage.removeItem('chronic_user');
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoggedIn: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
