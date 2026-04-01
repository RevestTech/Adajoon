import { useEffect, useRef, useState } from "react";
import Hls from "hls.js";
import { fetchStreams } from "../api/channels";

export default function VideoPlayer({ channel, onClose }) {
  const videoRef = useRef(null);
  const hlsRef = useRef(null);
  const [streams, setStreams] = useState([]);
  const [activeUrl, setActiveUrl] = useState(channel.stream_url || "");
  const [errorMsg, setErrorMsg] = useState("");

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

    if (activeUrl.includes(".m3u8") && Hls.isSupported()) {
      const hls = new Hls({
        enableWorker: true,
        lowLatencyMode: true,
      });
      hls.loadSource(activeUrl);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, () => video.play().catch(() => {}));
      hls.on(Hls.Events.ERROR, (_, data) => {
        if (data.fatal) setErrorMsg("Stream could not be loaded. It may be offline.");
      });
      hlsRef.current = hls;
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
          <button className="modal-close" onClick={onClose}>×</button>
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
          {streams.length > 1 && (
            <div className="stream-info">
              {streams.map((s, i) => (
                <button
                  key={s.id}
                  className={`stream-select ${s.url === activeUrl ? "active" : ""}`}
                  onClick={() => setActiveUrl(s.url)}
                >
                  Stream {i + 1} ({s.status})
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
