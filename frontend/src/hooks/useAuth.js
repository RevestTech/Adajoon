import { createContext, useContext, useState, useEffect, useCallback } from "react";

const TOKEN_KEY = "adajoon_token";
const USER_KEY = "adajoon_user";
const API_BASE = "/api/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const raw = localStorage.getItem(USER_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(false);

  const token = () => localStorage.getItem(TOKEN_KEY);

  const authHeaders = useCallback(() => {
    const t = localStorage.getItem(TOKEN_KEY);
    return t ? { Authorization: `Bearer ${t}` } : {};
  }, []);

  const loginWithGoogle = useCallback(async (credential) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/google`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ credential }),
      });
      if (!res.ok) throw new Error("Login failed");
      const data = await res.json();
      localStorage.setItem(TOKEN_KEY, data.token);
      localStorage.setItem(USER_KEY, JSON.stringify(data.user));
      setUser(data.user);
      return data.user;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setUser(null);
  }, []);

  const fetchFavorites = useCallback(async () => {
    const t = localStorage.getItem(TOKEN_KEY);
    if (!t) return null;
    try {
      const res = await fetch(`${API_BASE}/favorites`, {
        headers: { Authorization: `Bearer ${t}` },
      });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }, []);

  const addFavorite = useCallback(async (itemType, itemId, itemData) => {
    const t = localStorage.getItem(TOKEN_KEY);
    if (!t) return;
    await fetch(`${API_BASE}/favorites`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${t}` },
      body: JSON.stringify({ item_type: itemType, item_id: itemId, item_data: itemData }),
    });
  }, []);

  const removeFavorite = useCallback(async (itemType, itemId) => {
    const t = localStorage.getItem(TOKEN_KEY);
    if (!t) return;
    await fetch(`${API_BASE}/favorites/${itemType}/${itemId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${t}` },
    });
  }, []);

  const syncFavorites = useCallback(async (favorites) => {
    const t = localStorage.getItem(TOKEN_KEY);
    if (!t) return null;
    try {
      const res = await fetch(`${API_BASE}/favorites/sync`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${t}` },
        body: JSON.stringify(favorites),
      });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }, []);

  useEffect(() => {
    const t = localStorage.getItem(TOKEN_KEY);
    if (!t || !user) return;
    fetch(`${API_BASE}/me`, { headers: { Authorization: `Bearer ${t}` } })
      .then((res) => {
        if (!res.ok) { logout(); return null; }
        return res.json();
      })
      .then((data) => {
        if (data) {
          setUser(data);
          localStorage.setItem(USER_KEY, JSON.stringify(data));
        }
      })
      .catch(() => {});
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        loginWithGoogle,
        logout,
        fetchFavorites,
        addFavorite,
        removeFavorite,
        syncFavorites,
        authHeaders,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
