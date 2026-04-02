import { useState, useCallback, useRef } from "react";

const API = "/api/auth";

function getAuthHeaders() {
  const t = localStorage.getItem("adajoon_token");
  return t ? { Authorization: `Bearer ${t}` } : {};
}

export function useVotes() {
  const [myVotes, setMyVotes] = useState({});
  const [summaries, setSummaries] = useState({});
  const loadedTypes = useRef(new Set());

  const loadMyVotes = useCallback(async (itemType) => {
    const hdrs = getAuthHeaders();
    if (!hdrs.Authorization) return;
    if (loadedTypes.current.has(itemType)) return;
    try {
      const res = await fetch(`${API}/votes/me?item_type=${itemType}`, { headers: hdrs });
      if (res.ok) {
        const data = await res.json();
        setMyVotes((prev) => ({ ...prev, [itemType]: data }));
        loadedTypes.current.add(itemType);
      }
    } catch { /* ignore */ }
  }, []);

  const loadSummary = useCallback(async (itemType, itemIds) => {
    if (!itemIds.length) return;
    const ids = itemIds.slice(0, 100).join(",");
    try {
      const res = await fetch(`${API}/votes/summary?item_type=${itemType}&item_ids=${encodeURIComponent(ids)}`);
      if (res.ok) {
        const data = await res.json();
        setSummaries((prev) => {
          const updated = { ...prev };
          for (const [id, counts] of Object.entries(data)) {
            updated[`${itemType}:${id}`] = counts;
          }
          return updated;
        });
      }
    } catch { /* ignore */ }
  }, []);

  const submitVote = useCallback(async (itemType, itemId, voteType) => {
    const hdrs = getAuthHeaders();
    if (!hdrs.Authorization) return null;
    try {
      const res = await fetch(`${API}/votes`, {
        method: "POST",
        headers: { ...hdrs, "Content-Type": "application/json" },
        body: JSON.stringify({ item_type: itemType, item_id: itemId, vote_type: voteType }),
      });
      if (!res.ok) return null;
      const result = await res.json();

      setMyVotes((prev) => {
        const typeVotes = { ...(prev[itemType] || {}) };
        const current = typeVotes[itemId] || [];
        if (result.status === "added") {
          typeVotes[itemId] = [...current, voteType];
        } else {
          typeVotes[itemId] = current.filter((v) => v !== voteType);
        }
        return { ...prev, [itemType]: typeVotes };
      });

      setSummaries((prev) => {
        const key = `${itemType}:${itemId}`;
        const existing = { ...(prev[key] || {}) };
        if (result.status === "added") {
          existing[voteType] = (existing[voteType] || 0) + 1;
        } else {
          existing[voteType] = Math.max((existing[voteType] || 1) - 1, 0);
        }
        return { ...prev, [key]: existing };
      });

      return result;
    } catch {
      return null;
    }
  }, []);

  const getMyVotesFor = useCallback((itemType, itemId) => {
    return (myVotes[itemType] || {})[itemId] || [];
  }, [myVotes]);

  const getSummaryFor = useCallback((itemType, itemId) => {
    return summaries[`${itemType}:${itemId}`] || {};
  }, [summaries]);

  const resetLoaded = useCallback(() => {
    loadedTypes.current.clear();
  }, []);

  return { loadMyVotes, loadSummary, submitVote, getMyVotesFor, getSummaryFor, resetLoaded };
}
