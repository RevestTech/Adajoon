import { useEffect, useRef, useState } from "react";

export default function RadioPlayer({ station, onClose, isFavorite, onToggleFavorite }) {
  const audioRef = useRef(null);
  const [playing, setPlaying] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const streamUrl = station.url_resolved || station.url;

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !streamUrl) return;

    audio.src = streamUrl;
    audio.play()
      .then(() => setPlaying(true))
      .catch(() => setErrorMsg("Could not play this station. It may be offline or geo-restricted."));

    return () => {
      audio.pause();
      audio.src = "";
    };
  }, [streamUrl]);

  useEffect(() => {
    const handleKey = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose]);

  const tags = station.tags ? station.tags.split(",").map((t) => t.trim()).filter(Boolean) : [];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content radio-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h3>{station.name}</h3>
            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
              {station.country}
              {station.language && ` · ${station.language}`}
              {station.codec && ` · ${station.codec}`}
              {station.bitrate > 0 && ` · ${station.bitrate} kbps`}
            </span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
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
            <button className="modal-close" onClick={onClose}>×</button>
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
          ) : (
            <audio ref={audioRef} controls style={{ width: "100%", marginTop: 16 }} />
          )}

          {tags.length > 0 && (
            <div className="radio-tags">
              {tags.map((t) => (
                <span key={t} className="channel-tag">{t}</span>
              ))}
            </div>
          )}

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
