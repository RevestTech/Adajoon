import { useEffect, useRef, useState } from "react";
import {
  clearRadioPopoutStation,
  loadRadioPopoutStation,
} from "../utils/radioPopout";
import "./RadioPopoutWindow.css";

export default function RadioPopoutWindow() {
  const audioRef = useRef(null);
  const [station, setStation] = useState(null);
  const [playing, setPlaying] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [artFailed, setArtFailed] = useState(false);

  useEffect(() => {
    document.title = "Adajoon Radio";
    document.body.classList.add("radio-popout-body");
    return () => document.body.classList.remove("radio-popout-body");
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sid = params.get("sid");
    const loaded = loadRadioPopoutStation(sid);
    if (!loaded) {
      setErrorMsg("Station data expired. Close this window and pop out again.");
      return;
    }
    setStation(loaded);
    document.title = `${loaded.name} · Adajoon`;
  }, []);

  useEffect(() => {
    const audio = audioRef.current;
    const streamUrl = station?.url_resolved || station?.url;
    if (!audio || !streamUrl) return undefined;

    setErrorMsg("");
    setArtFailed(false);
    audio.src = streamUrl;
    audio.play()
      .then(() => setPlaying(true))
      .catch(() => {
        setPlaying(false);
        setErrorMsg("Could not play this station. It may be offline or geo-restricted.");
      });

    const sync = () => setPlaying(!audio.paused);
    audio.addEventListener("play", sync);
    audio.addEventListener("pause", sync);

    return () => {
      audio.removeEventListener("play", sync);
      audio.removeEventListener("pause", sync);
      audio.pause();
      audio.removeAttribute("src");
      audio.load();
      if (station?.id) clearRadioPopoutStation(station.id);
    };
  }, [station]);

  const togglePlay = () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (audio.paused) {
      audio.play().catch(() => setErrorMsg("Playback blocked — press play again."));
    } else {
      audio.pause();
    }
  };

  if (!station && !errorMsg) {
    return (
      <div className="radio-popout">
        <p className="radio-popout__muted">Loading…</p>
      </div>
    );
  }

  return (
    <div className="radio-popout">
      <header className="radio-popout__header">
        <div className="radio-popout__brand">Ada<span>joon</span></div>
        <button
          type="button"
          className="radio-popout__close"
          onClick={() => window.close()}
          aria-label="Close window"
        >
          ×
        </button>
      </header>

      {station && (
        <>
          <div className="radio-popout__art-wrap">
            {station.favicon && !artFailed ? (
              <img
                className="radio-popout__art"
                src={station.favicon}
                alt=""
                referrerPolicy="no-referrer"
                decoding="async"
                onError={() => setArtFailed(true)}
              />
            ) : (
              <div className="radio-popout__art-fallback" aria-hidden>
                ♪
              </div>
            )}
            {playing && !errorMsg && (
              <div className="radio-popout__eq" aria-hidden>
                <span /><span /><span /><span />
              </div>
            )}
          </div>

          <h1 className="radio-popout__title">{station.name}</h1>
          {(station.country || station.country_code) && (
            <p className="radio-popout__meta">
              {station.country || station.country_code}
            </p>
          )}
        </>
      )}

      {errorMsg && <p className="radio-popout__error">{errorMsg}</p>}

      <audio ref={audioRef} className="radio-popout__audio" controls />

      {station && !errorMsg && (
        <button
          type="button"
          className="radio-popout__play"
          onClick={togglePlay}
        >
          {playing ? "Pause" : "Play"}
        </button>
      )}
    </div>
  );
}
