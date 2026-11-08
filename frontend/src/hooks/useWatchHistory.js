import { useState, useEffect, useCallback } from "react";
import { authenticatedFetch } from "../utils/csrf";

const API_BASE = "/api";

/**
 * Custom hook for managing server-synced watch history.
 */
export function useWatchHistory(user) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  // Load history from server
  const loadHistory = useCallback(async (itemType = null) => {
    if (!user) return;
    
    setLoading(true);
    try {
      const url = itemType 
        ? `${API_BASE}/history?item_type=${itemType}&limit=50`
        : `${API_BASE}/history?limit=50`;
      
      const response = await authenticatedFetch(url);
      
      if (response.ok) {
        const data = await response.json();
        setHistory(data);
      }
    } catch (error) {
      console.error("Failed to load watch history:", error);
    } finally {
      setLoading(false);
    }
  }, [user]);

  // Record watch event
  const recordWatch = useCallback(async (itemType, item, durationSeconds = 0) => {
    if (!user) return;
    
    try {
      await authenticatedFetch(`${API_BASE}/history/record`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          item_type: itemType,
          item_id: item.id,
          item_name: item.name,
          item_logo: item.logo || item.favicon || "",
          duration_seconds: durationSeconds,
        }),
      });
      
      // Refresh history
      await loadHistory();
    } catch (error) {
      console.error("Failed to record watch history:", error);
    }
  }, [user, loadHistory]);

  // Clear all history
  const clearHistory = useCallback(async (itemType = null) => {
    if (!user) return;
    
    try {
      const url = itemType 
        ? `${API_BASE}/history?item_type=${itemType}`
        : `${API_BASE}/history`;
      
      await authenticatedFetch(url, {
        method: "DELETE",
      });
      
      setHistory([]);
    } catch (error) {
      console.error("Failed to clear watch history:", error);
    }
  }, [user]);

  // Delete specific history item
  const deleteHistoryItem = useCallback(async (historyId) => {
    if (!user) return;
    
    try {
      await authenticatedFetch(`${API_BASE}/history/${historyId}`, {
        method: "DELETE",
      });
      
      setHistory(prev => prev.filter(item => item.id !== historyId));
    } catch (error) {
      console.error("Failed to delete history item:", error);
    }
  }, [user]);

  // Load history when user logs in
  useEffect(() => {
    if (user) {
      loadHistory();
    } else {
      setHistory([]);
    }
  }, [user, loadHistory]);

  // Get recently watched items by type
  const getRecent = useCallback((itemType, limit = 10) => {
    return history
      .filter(item => item.item_type === itemType)
      .slice(0, limit);
  }, [history]);

  return {
    history,
    loading,
    loadHistory,
    recordWatch,
    clearHistory,
    deleteHistoryItem,
    getRecent,
  };
}
