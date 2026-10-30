import { useEffect, useRef, useState } from "react";
import useAds from "../hooks/useAds";

export default function MoviePlayer({ movie, onClose }) {
  const videoRef = useRef(null);
  const adContainerRef = useRef(null);
  const { adPlaying, playPreRoll } = useAds(videoRef, adContainerRef);
  const hlsRef = useRef(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !movie?.stream_url) return;

    let cancelled = false;
    setErrorMsg("");
    setIsLoading(true);

    const loadSource = () => {
      if (cancelled) return;
      const url = movie.stream_url;
      if (url.includes(".m3u8") && !video.canPlayType("application/vnd.apple.mpegurl")) {
        import("hls.js").then(({ default: Hls }) => {
          if (cancelled) return;
          if (!Hls.isSupported()) {
            setIsLoading(false);
            setErrorMsg("This title's stream format isn't supported in your browser.");
            return;
          }
          const hls = new Hls({ enableWorker: true });
          hls.loadSource(url);
          hls.attachMedia(video);
          hls.on(Hls.Events.MANIFEST_PARSED, () =>
            video.play().catch(() => setIsLoading(false))
          );
          hls.on(Hls.Events.ERROR, (_, data) => {
            if (data.fatal) {
              setIsLoading(false);
              setErrorMsg("This title could not be loaded.");
            }
          });
          hlsRef.current = hls;
        }).catch(() => {
          if (cancelled) return;
          setIsLoading(false);
          setErrorMsg("This title could not be loaded.");
        });
      } else {
        video.src = url;
        video.play().catch((err) => {
          setIsLoading(false);
          if (err?.name === "NotAllowedError") return;
          setErrorMsg("This title could not be loaded.");
        });
      }
    };

    playPreRoll().then(loadSource);

    const markPlaying = () => setIsLoading(false);
    const handleNativeError = () => {
      setIsLoading(false);
      setErrorMsg("This title could not be loaded.");
    };
    video.addEventListener("playing", markPlaying);
    video.addEventListener("error", handleNativeError);

    return () => {
      cancelled = true;
      video.removeEventListener("playing", markPlaying);
      video.removeEventListener("error", handleNativeError);
      if (hlsRef.current) {
        hlsRef.current.destroy();
        hlsRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [movie?.id]);

  return (
    <div className="modal-overlay movie-player-modal" role="dialog" aria-modal="true" aria-labelledby="movie-player-title">
      <div className="modal-content movie-player-modal__shell" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 id="movie-player-title">{movie.title}</h3>
          <button className="modal-close" onClick={onClose} aria-label="Close">×</button>
        </div>
        <div className="video-container">
          {errorMsg ? (
            <div className="no-stream channel-modal-no-stream--error">
              <p>{errorMsg}</p>
            </div>
          ) : (
            <>
              {isLoading && (
                <div className="video-loading-overlay" aria-live="polite">
                  <span className="video-loading-spinner" />
                  <span>Loading…</span>
                </div>
              )}
              <video ref={videoRef} controls autoPlay playsInline />
              <div
                ref={adContainerRef}
                className="video-ad-container"
                style={{ display: adPlaying ? "block" : "none" }}
              />
            </>
          )}
        </div>
        {movie.synopsis && <p className="movie-player-synopsis">{movie.synopsis}</p>}
      </div>
    </div>
  );
}
