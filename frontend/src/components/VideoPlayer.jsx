import { useEffect, useRef, useState } from "react";
import { fetchStreams, runHealthCheck } from "../api/channels";
import FeedbackBar from "./FeedbackBar";

function healthCheckPresentation(status) {
  const s = status || "unknown";
  const table = {
    verified: { label: "Verified", resultClass: "status-verified", dotClass: "verified" },
    manifest_only: { label: "Manifest only", resultClass: "status-manifest", dotClass: "manifest_only" },
    online: { label: "Online", resultClass: "status-live-partial", dotClass: "online" },
    offline: { label: "Offline", resultClass: "status-offline", dotClass: "offline" },
    timeout: { label: "Slow", resultClass: "status-timeout", dotClass: "timeout" },
    error: { label: "Error", resultClass: "status-error", dotClass: "error" },
    unknown: { label: "Unknown", resultClass: "status-unknown", dotClass: "unknown" },
    geo_blocked: { label: "Geo blocked", resultClass: "status-geo_blocked", dotClass: "geo_blocked" },
  };
  return table[s] || table.unknown;
}

function HealthCheckResultRow({ result }) {
  const pres = healthCheckPresentation(result.status);
  return (
    <div className={`healthcheck-result ${pres.resultClass}`}>
      <span className={`status-dot ${pres.dotClass}`} />
      <span className="healthcheck-status">{pres.label}</span>
      <span className="healthcheck-detail">
        {result.response_time_ms > 0 && `${result.response_time_ms}ms`}
        {result.detail && ` · ${result.detail}`}
      </span>
    </div>
  );
}

export default function VideoPlayer({ channel, onClose, isFavorite, onToggleFavorite, isGuest, onLogin, myVotes, voteSummary, onVote }) {
  const videoRef = useRef(null);
  const hlsRef = useRef(null);
  const [streams, setStreams] = useState([]);
  const [activeUrl, setActiveUrl] = useState(channel.stream_url || "");
  const [errorMsg, setErrorMsg] = useState("");
  const [healthResult, setHealthResult] = useState(null);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    fetchStreams(channel.id).then(setStreams).catch(() => {});
  }, [channel.id]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !activeUrl) return;

    setErrorMsg("");

    if (hlsRef.current) {
      hlsRef.current.destroy();
      hlsRef.current = null;
    }

    if (activeUrl.includes(".m3u8") && !video.canPlayType("application/vnd.apple.mpegurl")) {
      let cancelled = false;
      import("hls.js").then(({ default: Hls }) => {
        if (cancelled || !Hls.isSupported()) return;
        const hls = new Hls({ enableWorker: true, lowLatencyMode: true });
        hls.loadSource(activeUrl);
        hls.attachMedia(video);
        hls.on(Hls.Events.MANIFEST_PARSED, () => video.play().catch(() => {}));
        hls.on(Hls.Events.ERROR, (_, data) => {
          if (data.fatal) setErrorMsg("Stream could not be loaded. It may be offline.");
        });
        hlsRef.current = hls;
      });
      return () => { cancelled = true; if (hlsRef.current) { hlsRef.current.destroy(); hlsRef.current = null; } };
    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = activeUrl;
      video.play().catch(() => {});
    } else {
      video.src = activeUrl;
      video.play().catch(() => setErrorMsg("This stream format is not supported in your browser."));
    }

    return () => {
      if (hlsRef.current) {
        hlsRef.current.destroy();
        hlsRef.current = null;
      }
    };
  }, [activeUrl]);

  useEffect(() => {
    const handleKey = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose]);

  const handleHealthCheck = async () => {
    setChecking(true);
    setHealthResult(null);
    try {
      const result = await runHealthCheck(channel.id);
      setHealthResult(result);
    } catch {
      setHealthResult({ status: "error", detail: "Check failed", response_time_ms: 0 });
    } finally {
      setChecking(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h3>{channel.name}</h3>
            {channel.country_code && (
              <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                {channel.country_code}
                {channel.categories && ` · ${channel.categories.replace(/;/g, ", ")}`}
              </span>
            )}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            {!isGuest && (
              <button
                className={`modal-favorite-btn ${isFavorite ? "favorited" : ""}`}
                onClick={onToggleFavorite}
                title={isFavorite ? "Remove from favorites" : "Add to favorites"}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill={isFavorite ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                </svg>
              </button>
            )}
            <button className="modal-close" onClick={onClose}>×</button>
          </div>
        </div>
        <div className="modal-body">
          {activeUrl ? (
            <div className="video-container">
              {errorMsg ? (
                <div className="no-stream">{errorMsg}</div>
              ) : (
                <video ref={videoRef} controls autoPlay />
              )}
            </div>
          ) : (
            <div className="no-stream">
              No stream available for this channel.
            </div>
          )}

          <div className="stream-toolbar">
            <button
              className={`healthcheck-btn ${checking ? "checking" : ""}`}
              onClick={handleHealthCheck}
              disabled={checking}
            >
              {checking ? (
                <>
                  <span className="healthcheck-spinner" />
                  Checking...
                </>
              ) : (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                  </svg>
                  Check Stream
                </>
              )}
            </button>

            {healthResult && <HealthCheckResultRow result={healthResult} />}

            {streams.length > 1 && (
              <div className="stream-switcher">
                {streams.map((s, i) => (
                  <button
                    key={s.id}
                    className={`stream-select ${s.url === activeUrl ? "active" : ""}`}
                    onClick={() => setActiveUrl(s.url)}
                  >
                    Stream {i + 1}
                  </button>
                ))}
              </div>
            )}
          </div>

          <FeedbackBar
            itemType="tv"
            itemId={channel.id}
            myVotes={myVotes || []}
            summary={voteSummary || {}}
            onVote={onVote}
            isGuest={isGuest}
            onLogin={onLogin}
          />
        </div>
      </div>
    </div>
  );
}
