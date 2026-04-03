import { useEffect, useState } from "react";
import FeedbackBar from "./FeedbackBar";
import { useShare } from "../hooks/useShare";

export default function RadioPlayer({
  station,
  onClose,
  onMinimize,
  audioRef,
  minimized = false,
  isFavorite,
  onToggleFavorite,
  isGuest,
  onLogin,
  onGuestNotice,
  myVotes,
  voteSummary,
  onVote,
}) {
  const [playing, setPlaying] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [shareToast, setShareToast] = useState("");
  const { shareRadioStation } = useShare();

  const streamUrl = station.url_resolved || station.url;

  useEffect(() => {
    const audio = audioRef?.current;
    if (!audio || !streamUrl) return;

    setErrorMsg("");
    audio.src = streamUrl;
    audio.play()
      .then(() => setPlaying(true))
      .catch(() => setErrorMsg("Could not play this station. It may be offline or geo-restricted."));

    return () => {
      audio.pause();
      audio.src = "";
    };
  }, [streamUrl, audioRef]);

  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose]);

  useEffect(() => {
    const audio = audioRef?.current;
    if (!audio) return;
    const sync = () => setPlaying(!audio.paused);
    sync();
    audio.addEventListener("play", sync);
    audio.addEventListener("pause", sync);
    return () => {
      audio.removeEventListener("play", sync);
      audio.removeEventListener("pause", sync);
    };
  }, [audioRef, streamUrl]);

  const tags = station.tags ? station.tags.split(",").map((t) => t.trim()).filter(Boolean) : [];

  const showAudioControls = !minimized && !errorMsg;

  return (
    <div
      className={`modal-overlay${minimized ? " radio-modal-minimized" : ""}`}
      role="dialog"
      aria-modal={!minimized}
      aria-hidden={minimized || undefined}
      aria-labelledby={minimized ? undefined : "radio-player-title"}
    >
      <div className="modal-content radio-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h3 id="radio-player-title">{station.name}</h3>
            <span className="radio-player-meta">
              {station.country}
              {station.language && ` · ${station.language}`}
              {station.codec && ` · ${station.codec}`}
              {station.bitrate > 0 && ` · ${station.bitrate} kbps`}
              {station.health_status && (
                <span className={`radio-status-badge ${station.health_status}`}>
                  {station.health_status === 'verified' ? ' · ✓ Verified' : 
                   station.health_status === 'online' ? ' · ● Live' : 
                   ` · ${station.health_status}`}
                </span>
              )}
            </span>
            {station.health_checked_at && (
              <span className="radio-player-validated" title={`Last validated: ${new Date(station.health_checked_at).toLocaleString()}`}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
                Last checked: {new Date(station.health_checked_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}
              </span>
            )}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            {isGuest ? (
              <button
                type="button"
                className="favorite-btn favorite-btn--guest"
                onClick={() => {
                  onGuestNotice?.("Sign in to save favorites.");
                  onLogin?.();
                }}
                title="Sign in to save favorites"
                aria-label="Sign in to save favorites"
                style={{ position: "static" }}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                </svg>
              </button>
            ) : (
              <button
                className={`favorite-btn ${isFavorite ? "favorited" : ""}`}
                onClick={onToggleFavorite}
                title={isFavorite ? "Remove from favorites" : "Add to favorites"}
                style={{ position: "static" }}
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
                const result = await shareRadioStation(station);
                if (result.success) {
                  setShareToast(result.method === 'native' ? 'Shared!' : 'Link copied!');
                  setTimeout(() => setShareToast(""), 2000);
                } else {
                  setShareToast('Failed to share');
                  setTimeout(() => setShareToast(""), 2000);
                }
              }}
              title="Share this station"
              aria-label="Share this station"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="18" cy="5" r="3" />
                <circle cx="6" cy="12" r="3" />
                <circle cx="18" cy="19" r="3" />
                <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
                <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
              </svg>
            </button>
            {typeof onMinimize === "function" && (
              <button
                type="button"
                className="modal-minimize"
                onClick={onMinimize}
                aria-label="Minimize player — keep playing"
                title="Minimize (keep playing)"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                  <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
              </button>
            )}
            <button className="modal-close" onClick={onClose} aria-label="Stop and close player">×</button>
            {shareToast && (
              <div className="share-toast">{shareToast}</div>
            )}
          </div>
        </div>
        <div className="radio-player-body">
          <div className="radio-player-visual">
            {station.favicon ? (
              <img
                className="radio-player-art"
                src={station.favicon}
                alt={station.name}
                onError={(e) => { e.target.style.display = "none"; }}
              />
            ) : (
              <div className="radio-player-art-placeholder">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="2" />
                  <path d="M16.24 7.76a6 6 0 0 1 0 8.49" />
                  <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
                  <path d="M7.76 16.24a6 6 0 0 1 0-8.49" />
                  <path d="M4.93 19.07a10 10 0 0 1 0-14.14" />
                </svg>
              </div>
            )}
            {playing && !errorMsg && (
              <div className="radio-eq">
                <span /><span /><span /><span /><span />
              </div>
            )}
          </div>

          {errorMsg ? (
            <div className="no-stream">{errorMsg}</div>
          ) : null}
          <audio
            ref={audioRef}
            controls={showAudioControls}
            className={showAudioControls ? undefined : "radio-audio-hidden"}
            style={showAudioControls ? { width: "100%" } : undefined}
          />

          {tags.length > 0 && (
            <div className="radio-tags">
              {tags.map((t) => (
                <span key={t} className="channel-tag">{t}</span>
              ))}
            </div>
          )}

          <FeedbackBar
            itemType="radio"
            itemId={station.id}
            myVotes={myVotes || []}
            summary={voteSummary || {}}
            onVote={onVote}
            isGuest={isGuest}
            onLogin={onLogin}
            onGuestNotice={onGuestNotice}
          />

          {station.homepage && (
            <a
              href={station.homepage}
              target="_blank"
              rel="noopener noreferrer"
              className="radio-homepage-link"
            >
              Visit station website
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
