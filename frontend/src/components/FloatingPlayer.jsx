import { useEffect, useRef, useState, useCallback } from "react";

export default function FloatingPlayer({
  variant = "tv",
  channel,
  station,
  videoRef,
  audioRef,
  countries = [],
  onClose,
  onDock,
}) {
  const isTv = variant === "tv";
  const media = isTv ? channel : station;
  
  const containerRef = useRef(null);
  const [position, setPosition] = useState(() => {
    const saved = localStorage.getItem("adajoon_floating_position");
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return { x: window.innerWidth - 420, y: 80 };
      }
    }
    return { x: window.innerWidth - 420, y: 80 };
  });
  
  const [size, setSize] = useState(() => {
    const saved = localStorage.getItem("adajoon_floating_size");
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return { width: 400, height: 225 };
      }
    }
    return { width: 400, height: 225 };
  });
  
  const [isDragging, setIsDragging] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [resizeStart, setResizeStart] = useState({ x: 0, y: 0, width: 0, height: 0 });

  const getCountryName = (code) => {
    if (!code) return null;
    const country = countries.find(c => c.code === code);
    return country ? country.name : code;
  };

  useEffect(() => {
    localStorage.setItem("adajoon_floating_position", JSON.stringify(position));
  }, [position]);

  useEffect(() => {
    localStorage.setItem("adajoon_floating_size", JSON.stringify(size));
  }, [size]);

  const handleMouseDown = useCallback((e) => {
    if (e.target.closest(".floating-player-resize-handle")) return;
    if (e.target.closest(".floating-player-controls")) return;
    if (e.target.closest("video")) return;
    
    setIsDragging(true);
    setDragStart({
      x: e.clientX - position.x,
      y: e.clientY - position.y,
    });
    e.preventDefault();
  }, [position]);

  const handleResizeMouseDown = useCallback((e) => {
    setIsResizing(true);
    setResizeStart({
      x: e.clientX,
      y: e.clientY,
      width: size.width,
      height: size.height,
    });
    e.preventDefault();
    e.stopPropagation();
  }, [size]);

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (isDragging) {
        const newX = Math.max(0, Math.min(window.innerWidth - size.width, e.clientX - dragStart.x));
        const newY = Math.max(0, Math.min(window.innerHeight - size.height - 100, e.clientY - dragStart.y));
        setPosition({ x: newX, y: newY });
      }
      
      if (isResizing) {
        const deltaX = e.clientX - resizeStart.x;
        const deltaY = e.clientY - resizeStart.y;
        
        const newWidth = Math.max(280, Math.min(800, resizeStart.width + deltaX));
        const newHeight = Math.max(160, Math.min(600, resizeStart.height + deltaY));
        
        setSize({ width: newWidth, height: newHeight });
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      setIsResizing(false);
    };

    if (isDragging || isResizing) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
      return () => {
        document.removeEventListener("mousemove", handleMouseMove);
        document.removeEventListener("mouseup", handleMouseUp);
      };
    }
  }, [isDragging, isResizing, dragStart, resizeStart, size.width, size.height]);

  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [onClose]);

  const togglePlay = () => {
    if (isTv) {
      const video = videoRef?.current;
      if (!video) return;
      if (video.paused) {
        video.play().catch(() => {});
      } else {
        video.pause();
      }
    } else {
      const audio = audioRef?.current;
      if (!audio) return;
      if (audio.paused) {
        audio.play().catch(() => {});
      } else {
        audio.pause();
      }
    }
  };

  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    if (isTv) {
      const video = videoRef?.current;
      if (!video) return;
      const sync = () => setPlaying(!video.paused);
      sync();
      video.addEventListener("play", sync);
      video.addEventListener("pause", sync);
      return () => {
        video.removeEventListener("play", sync);
        video.removeEventListener("pause", sync);
      };
    } else {
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
    }
  }, [videoRef, audioRef, isTv]);

  return (
    <div
      ref={containerRef}
      className={`floating-player ${isDragging ? "dragging" : ""} ${isResizing ? "resizing" : ""}`}
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        width: `${size.width}px`,
        height: `${size.height}px`,
      }}
      role="dialog"
      aria-label={`Floating player: ${media?.name || "Media"}`}
    >
      <div className="floating-player-header" onMouseDown={handleMouseDown}>
        <div className="floating-player-title">
          <span className="floating-player-type">{isTv ? "TV" : "Radio"}</span>
          <span className="floating-player-name">{media?.name || "Unknown"}</span>
        </div>
        <div className="floating-player-controls">
          {isTv && channel?.country_code && (
            <span className="floating-player-meta">
              {getCountryName(channel.country_code)}
            </span>
          )}
          {!isTv && station?.country && (
            <span className="floating-player-meta">
              {station.country}
            </span>
          )}
          <button
            type="button"
            className="floating-player-btn"
            onClick={togglePlay}
            title={playing ? "Pause" : "Play"}
          >
            {playing ? (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="5" width="4" height="14" rx="1" />
                <rect x="14" y="5" width="4" height="14" rx="1" />
              </svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M8 5v14l11-7z" />
              </svg>
            )}
          </button>
          <button
            type="button"
            className="floating-player-btn"
            onClick={onDock}
            title="Dock player back to main view"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="9 15 3 21 3 15" />
              <polyline points="15 9 21 3 21 9" />
              <line x1="21" y1="3" x2="14" y2="10" />
              <line x1="3" y1="21" x2="10" y2="14" />
            </svg>
          </button>
          <button
            type="button"
            className="floating-player-btn floating-player-close"
            onClick={onClose}
            title="Close player"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
      </div>
      
      <div className="floating-player-body">
        {isTv ? (
          videoRef ? (
            <div style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <video
                ref={videoRef}
                controls
                autoPlay
                playsInline
                style={{ width: "100%", height: "100%", objectFit: "contain", display: "block" }}
              />
            </div>
          ) : null
        ) : (
          <div className="floating-player-radio">
            <div className="floating-player-radio-art">
              {station?.favicon ? (
                <img src={station.favicon} alt={station.name} />
              ) : (
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="2" />
                  <path d="M16.24 7.76a6 6 0 0 1 0 8.49" />
                  <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
                  <path d="M7.76 16.24a6 6 0 0 1 0-8.49" />
                  <path d="M4.93 19.07a10 10 0 0 1 0-14.14" />
                </svg>
              )}
            </div>
            {playing && (
              <div className="floating-player-radio-eq">
                <span /><span /><span /><span /><span />
              </div>
            )}
            <audio
              ref={audioRef}
              controls
              style={{ width: "100%", marginTop: "auto" }}
            />
          </div>
        )}
      </div>
      
      <div
        className="floating-player-resize-handle"
        onMouseDown={handleResizeMouseDown}
        title="Drag to resize"
      >
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="15 3 21 3 21 9" />
          <polyline points="9 21 3 21 3 15" />
          <line x1="21" y1="3" x2="11" y2="13" />
          <line x1="3" y1="21" x2="13" y2="11" />
        </svg>
      </div>
    </div>
  );
}
