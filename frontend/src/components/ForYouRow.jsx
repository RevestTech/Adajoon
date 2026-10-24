import { useEffect, useState } from "react";
import { fetchForYou } from "../api/channels";
import { analytics } from "../analytics";

/**
 * "For You in [Category]" row for the TV home (unfiltered, no-search) view.
 * Built from this browser session's own "Content Played" analytics events -
 * no login, no new tracking, and nothing shown until there's real history.
 */
export default function ForYouRow({ onSelect }) {
  const [channels, setChannels] = useState([]);
  const [category, setCategory] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchForYou(analytics.getSessionId())
      .then((data) => {
        if (cancelled) return;
        setChannels(data.channels || []);
        setCategory(data.category || null);
      })
      .catch(() => {
        if (!cancelled) setChannels([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading || channels.length === 0) return null;

  return (
    <div className="similar-rail for-you-row">
      <div className="similar-rail-title">For You in {category}</div>
      <div className="similar-rail-track">
        {channels.map((channel) => (
          <button
            key={channel.id}
            type="button"
            className="similar-rail-card"
            onClick={() => onSelect(channel)}
            title={channel.name}
          >
            <div className="similar-rail-card-logo">
              {channel.logo ? (
                <img src={channel.logo} alt="" loading="lazy" />
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="7" width="20" height="15" rx="2" ry="2" /><polyline points="17 2 12 7 7 2" />
                </svg>
              )}
            </div>
            <span className="similar-rail-card-name">{channel.name}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
