import { createContext, useContext, useState, useEffect, useCallback, useMemo } from "react";
import { startRegistration, startAuthentication } from "@simplewebauthn/browser";
import { authenticatedFetch, getCsrfToken } from "../utils/csrf";
import { analytics } from "../analytics";

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
    if (data?.token) {
      localStorage.setItem(TOKEN_KEY, data.token);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
    localStorage.setItem(USER_KEY, JSON.stringify(data.user));
    setUser(data.user);
    return data.user;
  }, []);

  // --- Google ---
  const loginWithGoogle = useCallback(async (credential) => {
    setLoading(true);
    analytics.trackLoginAttempt("google");
    try {
      const res = await authenticatedFetch(`${API_BASE}/google`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ credential }),
      });
      if (!res.ok) {
        const err = new Error("Login failed");
        err.status = res.status;
        throw err;
      }
      const savedUser = _saveSession(await res.json());
      analytics.trackLogin("google", savedUser.id);
      analytics.identify(savedUser.id, { method: "google" });
      return savedUser;
    } catch (error) {
      analytics.trackLoginFailure("google", error, { status: error?.status });
      throw error;
    } finally {
      setLoading(false);
    }
  }, [_saveSession]);

  // --- Apple ---
  const loginWithApple = useCallback(async (idToken, userName) => {
    setLoading(true);
    analytics.trackLoginAttempt("apple");
    try {
      const res = await authenticatedFetch(`${API_BASE}/apple`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_token: idToken, user_name: userName || "" }),
      });
      if (!res.ok) {
        const err = new Error("Apple login failed");
        err.status = res.status;
        throw err;
      }
      const savedUser = _saveSession(await res.json());
      analytics.trackLogin("apple", savedUser.id);
      analytics.identify(savedUser.id, { method: "apple" });
      return savedUser;
    } catch (error) {
      analytics.trackLoginFailure("apple", error, { status: error?.status });
      throw error;
    } finally {
      setLoading(false);
    }
  }, [_saveSession]);

  // --- Passkey registration (user must be logged in) ---
  const registerPasskey = useCallback(async (name) => {
    const optRes = await authenticatedFetch(`${API_BASE}/passkey/register-options`, {
      method: "POST",
    });
    if (!optRes.ok) throw new Error("Failed to get registration options");
    const { options, challenge_token } = await optRes.json();

    const credential = await startRegistration(options);

    const verRes = await authenticatedFetch(`${API_BASE}/passkey/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ credential, challenge_token, name: name || "Passkey" }),
    });
    if (!verRes.ok) throw new Error("Passkey registration failed");
    return await verRes.json();
  }, []);

  // --- Passkey login (no session required) ---
  const loginWithPasskey = useCallback(async () => {
    setLoading(true);
    analytics.trackLoginAttempt("passkey");
    try {
      const optRes = await authenticatedFetch(`${API_BASE}/passkey/login-options`, { method: "POST" });
      if (!optRes.ok) {
        const err = new Error("Failed to get login options");
        err.status = optRes.status;
        throw err;
      }
      const { options, challenge_token } = await optRes.json();

      const credential = await startAuthentication(options);

      const verRes = await authenticatedFetch(`${API_BASE}/passkey/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ credential, challenge_token }),
      });
      if (!verRes.ok) {
        const err = new Error("Passkey authentication failed");
        err.status = verRes.status;
        throw err;
      }
      const savedUser = _saveSession(await verRes.json());
      analytics.trackLogin("passkey", savedUser.id);
      analytics.identify(savedUser.id, { method: "passkey" });
      return savedUser;
    } catch (error) {
      analytics.trackLoginFailure("passkey", error, { status: error?.status });
      throw error;
    } finally {
      setLoading(false);
    }
  }, [_saveSession]);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setUser(null);
    analytics.reset();
  }, []);

  const fetchFavorites = useCallback(async () => {
    try {
      const res = await authenticatedFetch(`${API_BASE}/favorites`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }, []);

  const addFavorite = useCallback(async (itemType, itemId, itemData) => {
    try {
      await authenticatedFetch(`${API_BASE}/favorites`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ item_type: itemType, item_id: itemId, item_data: itemData }),
      });
    } catch (error) {
      console.error("Failed to add favorite:", error);
    }
  }, []);

  const removeFavorite = useCallback(async (itemType, itemId) => {
    try {
      await authenticatedFetch(`${API_BASE}/favorites/${itemType}/${itemId}`, {
        method: "DELETE",
      });
    } catch (error) {
      console.error("Failed to remove favorite:", error);
    }
  }, []);

  const syncFavorites = useCallback(async (favorites) => {
    try {
      const res = await authenticatedFetch(`${API_BASE}/favorites/sync`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(favorites),
      });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }, []);

  useEffect(() => {
    if (!user) return undefined;
    let cancelled = false;
    authenticatedFetch(`${API_BASE}/me`)
      .then((res) => {
        if (cancelled) return null;
        if (res.status === 401 || res.status === 403) {
          analytics.trackAuthSessionLost("me_unauthorized");
          logout();
          return null;
        }
        if (!res.ok) return null;
        return res.json();
      })
      .then((data) => {
        if (cancelled || !data) return;
        setUser(data);
        localStorage.setItem(USER_KEY, JSON.stringify(data));
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [logout, user?.id]);

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
