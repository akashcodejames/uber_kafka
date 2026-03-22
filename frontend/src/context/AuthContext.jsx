import { createContext, useCallback, useContext, useEffect, useState } from "react";
import api from "../api/axios";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser]   = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [loading, setLoading] = useState(true);

  // Fetch /auth/me whenever the token changes
  useEffect(() => {
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }

    const fetchUser = async () => {
      try {
        const { data } = await api.get("/auth/me");
        setUser(data);
      } catch {
        // Token invalid or expired
        localStorage.removeItem("token");
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, [token]);

  const login = useCallback((newToken, userData) => {
    localStorage.setItem("token", newToken);
    setToken(newToken);
    setUser(userData);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
