import { useEffect, useRef, useState } from "react";
import { fetchForYou } from "../api/channels";
import { analytics } from "../analytics";

// analytics.trackPlay() queues its "Content Played" event and flushes it to
// the backend up to 5s later (see scheduleFlush in analytics.js) - wait past
// that before re-fetching, or the backend would still see the old history.
const REFETCH_AFTER_PLAY_MS = 6000;

/**
 * "For You in [Category]" row for the TV or radio home (unfiltered,
 * no-search) view. Built from this browser session's own "Content Played"
 * analytics events - no login, no new tracking, and nothing shown until
 * there's real history.
 *
 * @param {object} props
 * @param {(item: object) => void} props.onSelect
 * @param {(sessionId: string, limit?: number) => Promise<object>} [props.fetchFn]
 *   Defaults to the TV fetcher. Pass `fetchForYouRadio` for the radio row.
 * @param {string} [props.itemsKey] Response field holding the item array
 *   ("channels" for TV, "stations" for radio).
 * @param {string} [props.labelKey] Response field holding the group label
 *   ("category" for TV, "tag" for radio).
 * @param {string} [props.imageField] Item field holding the image URL
 *   ("logo" for channels, "favicon" for stations).
 */
export default function ForYouRow({
  onSelect,
  fetchFn = fetchForYou,
  itemsKey = "channels",
  labelKey = "category",
  imageField = "logo",
}) {
  const [channels, setChannels] = useState([]);
  const [category, setCategory] = useState(null);
  const [loading, setLoading] = useState(true);
  const refetchTimeoutRef = useRef(null);

  const loadRecommendations = () =>
    fetchFn(analytics.getSessionId())
      .then((data) => {
        setChannels(data[itemsKey] || []);
        setCategory(data[labelKey] || null);
      })
      .catch(() => {
        setChannels([]);
      });

  useEffect(() => {
    let cancelled = false;
    fetchFn(analytics.getSessionId())
      .then((data) => {
        if (cancelled) return;
        setChannels(data[itemsKey] || []);
        setCategory(data[labelKey] || null);
      })
      .catch(() => {
        if (!cancelled) setChannels([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
      window.clearTimeout(refetchTimeoutRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetchFn]);

  const handleSelect = (channel) => {
    // The row stays mounted across the player opening and closing, so drop
    // the picked channel immediately instead of waiting on the backend to
    // see it as played - then re-fetch once the play event has flushed.
    setChannels((prev) => prev.filter((c) => c.id !== channel.id));
    onSelect(channel);
    window.clearTimeout(refetchTimeoutRef.current);
    refetchTimeoutRef.current = window.setTimeout(loadRecommendations, REFETCH_AFTER_PLAY_MS);
  };

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
            onClick={() => handleSelect(channel)}
            title={channel.name}
          >
            <div className="similar-rail-card-logo">
              {channel[imageField] ? (
                <img src={channel[imageField]} alt="" loading="lazy" />
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
