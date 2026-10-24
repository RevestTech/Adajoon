import { useEffect } from "react";
import { WHATS_NEW, formatReleaseDate } from "../data/whatsNew";

export default function WhatsNewModal({ onClose }) {
  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose]);

  return (
    <div className="modal-overlay whats-new-overlay" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="modal-content whats-new-modal">
        <div className="whats-new-header">
          <h3>What's New</h3>
          <button className="whats-new-close" onClick={onClose} aria-label="Close">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
        <div className="whats-new-body">
          {WHATS_NEW.map((release) => (
            <div key={release.version} className="whats-new-release">
              <div className="whats-new-release-header">
                <span className="whats-new-version">v{release.version}</span>
                <span className="whats-new-date">{formatReleaseDate(release.date)}</span>
              </div>
              <ul className="whats-new-highlights">
                {release.highlights.map((h, i) => (
                  <li key={i}>{h}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
