import { useEffect, useRef, useState } from "react";
import { fetchChannel, fetchStreams, runHealthCheck } from "../api/channels";
import { fetchEpgNow } from "../api/epg";
import FeedbackBar from "./FeedbackBar";
import MiniPlayer from "./MiniPlayer";
import SimilarItemsRail from "./SimilarItemsRail";
import { useShare } from "../hooks/useShare";

function formatEpgTime(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleTimeString(undefined, {
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

function EpgNowNextStrip({ now, next }) {
  if (!now && !next) return null;
  return (
    <div className="epg-now-next" aria-live="polite">
      {now && (
        <div className="epg-now-next__row epg-now-next__row--now">
          <span className="epg-now-next__label">Now</span>
          <span className="epg-now-next__title">{now.title || "Untitled"}</span>
          <span className="epg-now-next__time">
            {formatEpgTime(now.start_at)}–{formatEpgTime(now.stop_at)}
          </span>
        </div>
      )}
      {next && (
        <div className="epg-now-next__row epg-now-next__row--next">
          <span className="epg-now-next__label">Next</span>
          <span className="epg-now-next__title">{next.title || "Untitled"}</span>
          <span className="epg-now-next__time">
            {formatEpgTime(next.start_at)}–{formatEpgTime(next.stop_at)}
          </span>
        </div>
      )}
    </div>
  );
}

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

export default function VideoPlayer({
  channel,
  countries = [],
  videoRef: externalVideoRef,
  onClose,
  onMinimize,
  onExpand,
  onPopOut,
  minimized = false,
  isFavorite,
  onToggleFavorite,
  isGuest,
  onLogin,
  onGuestNotice,
  myVotes,
  voteSummary,
  onVote,
  onSelectSimilar,
}) {
  const getCountryName = (code) => {
    if (!code) return null;
    const country = countries.find(c => c.code === code);
    return country ? country.name : code;
  };
  const internalVideoRef = useRef(null);
  const videoRef = externalVideoRef || internalVideoRef;
  const hlsRef = useRef(null);
  const stallTimeoutRef = useRef(null);
  const [streams, setStreams] = useState([]);
  const [activeUrl, setActiveUrl] = useState(channel.stream_url || "");
  const [isLoading, setIsLoading] = useState(Boolean(channel.stream_url));
  const [errorMsg, setErrorMsg] = useState("");
  const [triedUrls, setTriedUrls] = useState(() =>
    channel.stream_url ? [channel.stream_url] : []
  );
  const [retryNonce, setRetryNonce] = useState(0);
  const [healthResult, setHealthResult] = useState(null);
  const [checking, setChecking] = useState(false);
  const [shareToast, setShareToast] = useState("");
  const [epgNow, setEpgNow] = useState(null);
  const [epgNext, setEpgNext] = useState(null);
  const { shareTvChannel } = useShare();
  // True once fetchStreams has settled (success or failure) for the current
  // channel, so a stream failure that lands before alternates arrive can
  // wait for them instead of declaring final failure prematurely.
  const streamsSettledRef = useRef(false);
  const pendingFailureRef = useRef(null);
  const latestChannelIdRef = useRef(channel.id);
  latestChannelIdRef.current = channel.id;

  useEffect(() => {
    const channelId = channel.id;
    streamsSettledRef.current = false;
    pendingFailureRef.current = null;
    fetchStreams(channelId)
      .then((result) => {
        if (channelId !== latestChannelIdRef.current) return; // stale response for a channel we've left
        streamsSettledRef.current = true;
        setStreams(result);
        // No primary stream_url, but the channel has alternates - use the
        // first one instead of showing "No stream available" forever.
        setActiveUrl((current) => current || result?.[0]?.url || current);
        if (pendingFailureRef.current) {
          const message = pendingFailureRef.current;
          pendingFailureRef.current = null;
          handleStreamFailure(message, result);
        }
      })
      .catch(() => {
        if (channelId !== latestChannelIdRef.current) return;
        streamsSettledRef.current = true;
        if (pendingFailureRef.current) {
          const message = pendingFailureRef.current;
          pendingFailureRef.current = null;
          handleStreamFailure(message, []);
        }
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [channel.id]);

  // Reset playback state when switching to a different channel without
  // closing the player (e.g. picking a new card while minimized).
  useEffect(() => {
    setStreams([]);
    setActiveUrl(channel.stream_url || "");
    setTriedUrls(channel.stream_url ? [channel.stream_url] : []);
    setErrorMsg("");
    setIsLoading(Boolean(channel.stream_url));
  }, [channel.id]);

  // Record every URL we've attempted so auto-fallback never retries one.
  useEffect(() => {
    if (!activeUrl) return;
    setTriedUrls((prev) => (prev.includes(activeUrl) ? prev : [...prev, activeUrl]));
  }, [activeUrl]);

  useEffect(() => {
    let cancelled = false;
    setEpgNow(null);
    setEpgNext(null);
    fetchEpgNow(channel.id)
      .then((data) => {
        if (cancelled) return;
        setEpgNow(data?.now || null);
        setEpgNext(data?.next || null);
      })
      .catch(() => {
        if (!cancelled) {
          setEpgNow(null);
          setEpgNext(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [channel.id]);

  const streamsRef = useRef(streams);
  useEffect(() => { streamsRef.current = streams; }, [streams]);
  const triedUrlsRef = useRef(triedUrls);
  useEffect(() => { triedUrlsRef.current = triedUrls; }, [triedUrls]);

  // On failure, auto-advance to the next untried stream source instead of
  // just sitting frozen; only show a final error once every source failed.
  // `streamsOverride`, when passed, is the just-resolved streams list (state
  // hasn't committed yet when this is called from the fetchStreams handler).
  const handleStreamFailure = (finalMessage, streamsOverride) => {
    const source = streamsOverride ?? streamsRef.current;
    const candidates = [channel.stream_url, ...source.map((s) => s.url)].filter(Boolean);
    const next = candidates.find((u) => !triedUrlsRef.current.includes(u));
    if (next) {
      setActiveUrl(next);
      return;
    }
    if (!streamsSettledRef.current) {
      // Alternates may still be on the way - wait for them instead of
      // declaring final failure; fetchStreams resolving will retry this.
      pendingFailureRef.current = finalMessage;
      return;
    }
    setIsLoading(false);
    setErrorMsg(finalMessage);
  };

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !activeUrl) return;

    let cancelled = false;
    setErrorMsg("");
    setIsLoading(true);

    if (hlsRef.current) {
      hlsRef.current.destroy();
      hlsRef.current = null;
    }
    if (stallTimeoutRef.current) {
      clearTimeout(stallTimeoutRef.current);
      stallTimeoutRef.current = null;
    }

    const clearStallTimeout = () => {
      if (stallTimeoutRef.current) {
        clearTimeout(stallTimeoutRef.current);
        stallTimeoutRef.current = null;
      }
    };
    const markPlaying = () => {
      clearStallTimeout();
      setIsLoading(false);
    };
    const handleNativeError = () => {
      clearStallTimeout();
      handleStreamFailure("Stream could not be loaded. It may be offline.");
    };

    video.addEventListener("playing", markPlaying);
    video.addEventListener("error", handleNativeError);

    // If nothing starts playing within 15s, treat it as a failed source
    // rather than leaving the player frozen with no feedback.
    stallTimeoutRef.current = setTimeout(() => {
      handleStreamFailure("Stream timed out. It may be offline.");
    }, 15000);

    if (activeUrl.includes(".m3u8") && !video.canPlayType("application/vnd.apple.mpegurl")) {
      import("hls.js").then(({ default: Hls }) => {
        if (cancelled) return;
        if (!Hls.isSupported()) {
          clearStallTimeout();
          handleStreamFailure("This stream format is not supported in your browser.");
          return;
        }
        const hls = new Hls({ enableWorker: true, lowLatencyMode: true });
        hls.loadSource(activeUrl);
        hls.attachMedia(video);
        hls.on(Hls.Events.MANIFEST_PARSED, () => video.play().catch(() => {}));
        hls.on(Hls.Events.ERROR, (_, data) => {
          if (data.fatal) {
            clearStallTimeout();
            handleStreamFailure("Stream could not be loaded. It may be offline.");
          }
        });
        hlsRef.current = hls;
      });
    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = activeUrl;
      video.play().catch(() => {
        clearStallTimeout();
        handleStreamFailure("Stream could not be loaded. It may be offline.");
      });
    } else {
      video.src = activeUrl;
      video.play().catch(() => {
        clearStallTimeout();
        handleStreamFailure("This stream format is not supported in your browser.");
      });
    }

    return () => {
      cancelled = true;
      video.removeEventListener("playing", markPlaying);
      video.removeEventListener("error", handleNativeError);
      clearStallTimeout();
      if (hlsRef.current) {
        hlsRef.current.destroy();
        hlsRef.current = null;
      }
    };
    // retryNonce has no effect on playback logic itself - it only forces
    // this effect to rerun when Retry picks the same URL (e.g. the channel
    // has just one source), which activeUrl alone wouldn't trigger.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeUrl, retryNonce]);

  useEffect(() => {
    const handleKey = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose]);

  const handleSelectSimilar = (item) => {
    fetchChannel(item.id)
      .then((full) => onSelectSimilar?.(full))
      .catch(() => {});
  };

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
    <>
    <div
      className={`modal-overlay channel-player-modal${minimized ? " channel-player-modal-minimized" : ""}`}
      role="dialog"
      aria-modal={!minimized}
      aria-hidden={minimized || undefined}
      aria-labelledby={minimized ? undefined : "player-title"}
    >
      <div className="modal-content channel-player-modal__shell" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header channel-modal-header">
          <div className="channel-modal-header__main">
            <h3 id="player-title">
              {channel.name}
              {channel.alt_names && channel.alt_names !== channel.name && (
                <span className="channel-alt-name"> ({channel.alt_names})</span>
              )}
            </h3>
            {(channel.country_code || channel.categories) && (
              <div className="channel-modal-meta">
                {channel.country_code && (
                  <span className="channel-modal-pill channel-modal-pill--country">
                    {getCountryName(channel.country_code)}
                  </span>
                )}
                {channel.categories && (
                  <span className="channel-modal-pill channel-modal-pill--cats">
                    {channel.categories.replace(/;/g, ", ")}
                  </span>
                )}
                {channel.health_status && (
                  <span className={`channel-modal-pill channel-modal-pill--status ${channel.health_status}`}>
                    {channel.health_status === 'verified' ? '✓ Verified' : 
                     channel.health_status === 'online' ? '● Live' : 
                     channel.health_status}
                  </span>
                )}
              </div>
            )}
            {(channel.network || channel.website) && (
              <div className="channel-modal-info">
                {channel.network && (
                  <span className="channel-info-item">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="12" cy="12" r="10" />
                      <line x1="2" y1="12" x2="22" y2="12" />
                      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                    </svg>
                    {channel.network}
                  </span>
                )}
                {channel.website && (
                  <a 
                    href={channel.website} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className="channel-info-item channel-info-link"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                      <polyline points="15 3 21 3 21 9" />
                      <line x1="10" y1="14" x2="21" y2="3" />
                    </svg>
                    Website
                  </a>
                )}
                {channel.health_checked_at && (
                  <span className="channel-info-item channel-info-validated" title={`Last validated: ${new Date(channel.health_checked_at).toLocaleString()}`}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="12" cy="12" r="10" />
                      <polyline points="12 6 12 12 16 14" />
                    </svg>
                    {new Date(channel.health_checked_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                  </span>
                )}
              </div>
            )}
          </div>
          <div className="channel-modal-header__actions">
            {isGuest ? (
              <button
                type="button"
                className="modal-favorite-btn modal-favorite-btn--guest"
                onClick={() => onGuestNotice?.("Sign in to save favorites.")}
                title="Sign in to save favorites"
                aria-label="Sign in to save favorites"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                </svg>
              </button>
            ) : (
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
            <button
              type="button"
              className="modal-share-btn"
              onClick={async () => {
                const result = await shareTvChannel(channel);
                if (result.success) {
                  setShareToast(result.method === 'native' ? 'Shared!' : 'Link copied!');
                  setTimeout(() => setShareToast(""), 2000);
                } else {
                  setShareToast('Failed to share');
                  setTimeout(() => setShareToast(""), 2000);
                }
              }}
              title="Share this channel"
              aria-label="Share this channel"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="18" cy="5" r="3" />
                <circle cx="6" cy="12" r="3" />
                <circle cx="18" cy="19" r="3" />
                <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
                <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
              </svg>
            </button>
            {typeof onPopOut === "function" && !minimized && (
              <button
                type="button"
                className="modal-popout channel-modal-popout"
                onClick={onPopOut}
                aria-label="Pop out player (floating window)"
                title="Pop Out"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                  <path d="M15 3h6v6" />
                  <path d="M10 14L21 3" />
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                </svg>
              </button>
            )}
            {typeof onMinimize === "function" && (
              <button
                type="button"
                className="modal-minimize channel-modal-minimize"
                onClick={onMinimize}
                aria-label="Minimize player — keep playing"
                title="Minimize (keep playing)"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                  <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
              </button>
            )}
            <button className="modal-close channel-modal-close" onClick={onClose} aria-label="Stop and close player">×</button>
            {shareToast && (
              <div className="share-toast">{shareToast}</div>
            )}
          </div>
        </div>
        {!minimized && (epgNow || epgNext) && (
          <EpgNowNextStrip now={epgNow} next={epgNext} />
        )}
        <div className="modal-body channel-modal-body">
          <div className="channel-modal-stage">
            {activeUrl ? (
              <div className="video-container">
                {errorMsg ? (
                  <div className="no-stream channel-modal-no-stream channel-modal-no-stream--error">
                    <p>{errorMsg}</p>
                    <button
                      type="button"
                      className="channel-modal-retry-btn"
                      onClick={() => {
                        setTriedUrls([]);
                        setErrorMsg("");
                        setActiveUrl(channel.stream_url || streams[0]?.url || "");
                        setRetryNonce((n) => n + 1);
                      }}
                    >
                      Retry
                    </button>
                  </div>
                ) : (
                  <>
                    {isLoading && (
                      <div className="video-loading-overlay" aria-live="polite">
                        <span className="video-loading-spinner" />
                        <span>Connecting to stream…</span>
                      </div>
                    )}
                    <video ref={videoRef} controls autoPlay playsInline />
                  </>
                )}
              </div>
            ) : (
              <div className="channel-modal-empty">
                <div className="channel-modal-empty__art" aria-hidden>
                  <svg className="channel-modal-empty__tv" viewBox="0 0 120 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                      <linearGradient id="chTvGrad" x1="0" y1="0" x2="120" y2="100" gradientUnits="userSpaceOnUse">
                        <stop stopColor="#e94560" stopOpacity="0.9" />
                        <stop offset="1" stopColor="#7c3aed" stopOpacity="0.75" />
                      </linearGradient>
                    </defs>
                    <rect x="12" y="18" width="96" height="64" rx="10" stroke="url(#chTvGrad)" strokeWidth="2.5" fill="rgba(15,15,26,0.6)" />
                    <rect x="22" y="28" width="76" height="44" rx="4" fill="rgba(0,0,0,0.45)" />
                    <path className="channel-modal-empty__static" d="M26 48h68M26 56h52M30 64h60" stroke="rgba(233,69,96,0.25)" strokeWidth="1.2" strokeLinecap="round" />
                    <circle cx="60" cy="88" r="4" fill="url(#chTvGrad)" opacity="0.8" />
                  </svg>
                </div>
                <p className="channel-modal-empty__title">No stream available</p>
                <p className="channel-modal-empty__hint">This channel has no playable URL yet — run a check below or try another listing.</p>
              </div>
            )}
          </div>

          <div className="stream-toolbar channel-modal-toolbar">
            <button
              className={`healthcheck-btn channel-modal-health-btn ${checking ? "checking" : ""}`}
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

          {!minimized && (
            <SimilarItemsRail itemType="tv" itemId={channel.id} onSelect={handleSelectSimilar} />
          )}

          <FeedbackBar
            variant="channel"
            itemType="tv"
            itemId={channel.id}
            myVotes={myVotes || []}
            summary={voteSummary || {}}
            onVote={onVote}
            isGuest={isGuest}
            onLogin={onLogin}
            onGuestNotice={onGuestNotice}
          />
        </div>
      </div>
    </div>
    {minimized && onExpand && (
      <MiniPlayer
        variant="tv"
        channel={channel}
        videoRef={videoRef}
        onExpand={onExpand}
        onStop={onClose}
      />
    )}
    </>
  );
}
