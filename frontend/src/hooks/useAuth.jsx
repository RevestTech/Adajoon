import { createContext, useContext, useState, useEffect, useCallback, useMemo } from "react";
import { startRegistration, startAuthentication } from "@simplewebauthn/browser";

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

  const authHeaders = useCallback(() => {
    const t = localStorage.getItem(TOKEN_KEY);
    return t ? { Authorization: `Bearer ${t}` } : {};
  }, []);

  const _saveSession = useCallback((data) => {
    localStorage.setItem(TOKEN_KEY, data.token);
    localStorage.setItem(USER_KEY, JSON.stringify(data.user));
    setUser(data.user);
    return data.user;
  }, []);

  // --- Google ---
  const loginWithGoogle = useCallback(async (credential) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/google`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ credential }),
      });
      if (!res.ok) throw new Error("Login failed");
      return _saveSession(await res.json());
    } finally {
      setLoading(false);
    }
  }, [_saveSession]);

  // --- Apple ---
  const loginWithApple = useCallback(async (idToken, userName) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/apple`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_token: idToken, user_name: userName || "" }),
      });
      if (!res.ok) throw new Error("Apple login failed");
      return _saveSession(await res.json());
    } finally {
      setLoading(false);
    }
  }, [_saveSession]);

  // --- Passkey registration (user must be logged in) ---
  const registerPasskey = useCallback(async (name) => {
    const t = localStorage.getItem(TOKEN_KEY);
    if (!t) throw new Error("Not authenticated");

    const optRes = await fetch(`${API_BASE}/passkey/register-options`, {
      method: "POST",
      headers: { Authorization: `Bearer ${t}` },
    });
    if (!optRes.ok) throw new Error("Failed to get registration options");
    const { options, challenge_token } = await optRes.json();

    const credential = await startRegistration(options);

    const verRes = await fetch(`${API_BASE}/passkey/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${t}` },
      body: JSON.stringify({ credential, challenge_token, name: name || "Passkey" }),
    });
    if (!verRes.ok) throw new Error("Passkey registration failed");
    return await verRes.json();
  }, []);

  // --- Passkey login (no session required) ---
  const loginWithPasskey = useCallback(async () => {
    setLoading(true);
    try {
      const optRes = await fetch(`${API_BASE}/passkey/login-options`, { method: "POST" });
      if (!optRes.ok) throw new Error("Failed to get login options");
      const { options, challenge_token } = await optRes.json();

      const credential = await startAuthentication(options);

      const verRes = await fetch(`${API_BASE}/passkey/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ credential, challenge_token }),
      });
      if (!verRes.ok) throw new Error("Passkey authentication failed");
      return _saveSession(await verRes.json());
    } finally {
      setLoading(false);
    }
  }, [_saveSession]);

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

  const value = useMemo(() => ({
    user,
    loading,
    loginWithGoogle,
    loginWithApple,
    loginWithPasskey,
    registerPasskey,
    logout,
    fetchFavorites,
    addFavorite,
    removeFavorite,
    syncFavorites,
    authHeaders,
  }), [user, loading, loginWithGoogle, loginWithApple, loginWithPasskey, registerPasskey, logout, fetchFavorites, addFavorite, removeFavorite, syncFavorites, authHeaders]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
