import { useState, useEffect } from "react";
import { fetchRecommendations } from "../api/recommendations";

/**
 * "You might also like" rail for the channel/station detail player.
 * Fetches similar items for the current channel/station and lets the user
 * switch the player straight to one, without closing the modal.
 */
export default function SimilarItemsRail({ itemType, itemId, onSelect }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchRecommendations(itemType, itemId, 10).then((results) => {
      if (!cancelled) {
        setItems(results);
        setLoading(false);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [itemType, itemId]);

  if (!loading && items.length === 0) return null;

  return (
    <div className="similar-rail">
      <div className="similar-rail-title">You might also like</div>
      <div className="similar-rail-track">
        {loading
          ? Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="similar-rail-card similar-rail-card--skeleton" />
            ))
          : items.map((item) => (
              <button
                key={item.id}
                type="button"
                className="similar-rail-card"
                onClick={() => onSelect(item)}
                title={item.name}
              >
                <div className="similar-rail-card-logo">
                  {(item.logo || item.favicon) ? (
                    <img src={item.logo || item.favicon} alt="" loading="lazy" />
                  ) : (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="2" y="7" width="20" height="15" rx="2" ry="2" /><polyline points="17 2 12 7 7 2" />
                    </svg>
                  )}
                </div>
                <span className="similar-rail-card-name">{item.name}</span>
              </button>
            ))}
      </div>
    </div>
  );
}
