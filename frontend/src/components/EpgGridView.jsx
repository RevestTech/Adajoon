import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchEpgScheduleBatch } from "../api/epg";
import { formatClockTime } from "../utils/epgTime";

const WINDOW_HOURS = 4;
const HOUR_MARKS = Array.from({ length: WINDOW_HOURS + 1 }, (_, i) => i);

function roundDownToHalfHour(date) {
  const d = new Date(date);
  d.setMinutes(d.getMinutes() < 30 ? 0 : 30, 0, 0);
  return d;
}

function clampProgrammeToWindow(programme, windowStart, windowEnd) {
  const start = new Date(programme.start_at);
  const stop = new Date(programme.stop_at);
  const clampedStart = start < windowStart ? windowStart : start;
  const clampedStop = stop > windowEnd ? windowEnd : stop;
  const totalMs = windowEnd.getTime() - windowStart.getTime();
  const leftPct = ((clampedStart.getTime() - windowStart.getTime()) / totalMs) * 100;
  const widthPct = ((clampedStop.getTime() - clampedStart.getTime()) / totalMs) * 100;
  return { leftPct, widthPct: Math.max(widthPct, 1) };
}

export default function EpgGridView({ channels, onClose, onSelectChannel }) {
  const [windowStart, setWindowStart] = useState(() => roundDownToHalfHour(new Date()));
  const [schedule, setSchedule] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const windowEnd = useMemo(
    () => new Date(windowStart.getTime() + WINDOW_HOURS * 3600_000),
    [windowStart]
  );

  const channelIds = useMemo(() => channels.map((ch) => ch.id), [channels]);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchEpgScheduleBatch(channelIds, {
        from: windowStart.toISOString(),
        to: windowEnd.toISOString(),
      });
      setSchedule(data.items || {});
    } catch (err) {
      setError(err.message || "Failed to load the TV guide");
    } finally {
      setLoading(false);
    }
  }, [channelIds, windowStart, windowEnd]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose]);

  const nowPct =
    ((Date.now() - windowStart.getTime()) / (windowEnd.getTime() - windowStart.getTime())) * 100;

  return (
    <div className="epg-grid-overlay" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="epg-grid-modal">
        <div className="epg-grid-header">
          <h2>TV Guide</h2>
          <div className="epg-grid-nav">
            <button
              type="button"
              onClick={() => setWindowStart((d) => new Date(d.getTime() - WINDOW_HOURS * 3600_000))}
            >
              ← Earlier
            </button>
            <button
              type="button"
              onClick={() => setWindowStart(roundDownToHalfHour(new Date()))}
            >
              Now
            </button>
            <button
              type="button"
              onClick={() => setWindowStart((d) => new Date(d.getTime() + WINDOW_HOURS * 3600_000))}
            >
              Later →
            </button>
          </div>
          <button className="epg-grid-close" onClick={onClose} aria-label="Close TV guide">×</button>
        </div>

        <div className="epg-grid-timebar">
          <div className="epg-grid-timebar-spacer" />
          <div className="epg-grid-timebar-marks">
            {HOUR_MARKS.map((h) => (
              <span key={h} className="epg-grid-timemark" style={{ left: `${(h / WINDOW_HOURS) * 100}%` }}>
                {formatClockTime(new Date(windowStart.getTime() + h * 3600_000).toISOString())}
              </span>
            ))}
          </div>
        </div>

        {error && <div className="epg-grid-error">{error}</div>}

        <div className="epg-grid-body">
          {loading && channels.length === 0 ? null : (
            <>
              {nowPct >= 0 && nowPct <= 100 && (
                <div className="epg-grid-now-line" style={{ left: `calc(160px + (100% - 160px) * ${nowPct / 100})` }} />
              )}
              {channels.map((ch) => {
                const programmes = schedule[ch.id] || [];
                return (
                  <div key={ch.id} className="epg-grid-row">
                    <button
                      type="button"
                      className="epg-grid-channel"
                      onClick={() => onSelectChannel?.(ch)}
                    >
                      {ch.logo ? (
                        <img src={ch.logo} alt="" className="epg-grid-channel-logo" />
                      ) : (
                        <span className="epg-grid-channel-logo epg-grid-channel-logo--placeholder" />
                      )}
                      <span className="epg-grid-channel-name">{ch.name}</span>
                    </button>
                    <div className="epg-grid-timeline">
                      {programmes.length === 0 ? (
                        <span className="epg-grid-noinfo">No schedule info</span>
                      ) : (
                        programmes.map((p) => {
                          const { leftPct, widthPct } = clampProgrammeToWindow(p, windowStart, windowEnd);
                          return (
                            <button
                              type="button"
                              key={p.id}
                              className="epg-grid-programme"
                              style={{ left: `${leftPct}%`, width: `${widthPct}%` }}
                              title={p.title}
                              onClick={() => onSelectChannel?.(ch)}
                            >
                              {p.title || "Untitled"}
                            </button>
                          );
                        })
                      )}
                    </div>
                  </div>
                );
              })}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
