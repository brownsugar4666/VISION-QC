import { createContext, useContext, useState, useEffect } from 'react';
import api from '../api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('vqc_user')); } catch { return null; }
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('vqc_token');
    if (token) {
      api.get('/auth/me')
        .then((r) => { setUser(r.data); localStorage.setItem('vqc_user', JSON.stringify(r.data)); })
        .catch(() => { localStorage.removeItem('vqc_token'); localStorage.removeItem('vqc_user'); setUser(null); })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (username, password) => {
    const form = new URLSearchParams();
    form.append('username', username);
    form.append('password', password);
    const r = await api.post('/auth/login', form, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });
    localStorage.setItem('vqc_token', r.data.access_token);
    localStorage.setItem('vqc_user', JSON.stringify(r.data.user));
    setUser(r.data.user);
    return r.data.user;
  };

  const logout = () => {
    localStorage.removeItem('vqc_token');
    localStorage.removeItem('vqc_user');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
