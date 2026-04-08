import { useState, useRef, useEffect, useCallback } from "react";
import { aiSearch } from "../api/aiSearch";

const EXAMPLE_QUERIES = {
  tv: [
    "Channels that show live soccer",
    "Persian news channels",
    "Kids cartoon channels",
    "Music video channels",
    "Documentary channels in English",
    "Sports channels from the UK",
  ],
  radio: [
    "Jazz stations from the US",
    "Classical music radio",
    "Persian radio stations",
    "Top 40 pop hits",
    "Rock stations in the UK",
    "Lo-fi beats to study to",
  ],
};

export default function AISearchModal({ mode, onSelect, onClose }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [explanation, setExplanation] = useState("");
  const inputRef = useRef(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Close on Escape
  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose]);

  const handleSearch = useCallback(async (searchQuery) => {
    const q = (searchQuery || query).trim();
    if (!q || q.length < 2) return;

    setLoading(true);
    setError("");
    setResults(null);
    setExplanation("");

    try {
      const data = await aiSearch(q, mode);
      const items = mode === "tv" ? data.channels : data.stations;
      setResults(items || []);
      setExplanation(data.explanation || "");
    } catch (err) {
      setError(err.message || "Search failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [query, mode]);

  const handleSubmit = (e) => {
    e.preventDefault();
    handleSearch();
  };

  const handleExampleClick = (example) => {
    setQuery(example);
    handleSearch(example);
  };

  const handleItemClick = (item) => {
    onSelect(item);
    onClose();
  };

  const examples = EXAMPLE_QUERIES[mode] || EXAMPLE_QUERIES.tv;

  return (
    <div className="ai-search-overlay" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="ai-search-modal">
        <div className="ai-search-header">
          <div className="ai-search-title">
            <svg className="ai-sparkle-icon" width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L14.09 8.26L20 9.27L15.55 13.97L16.91 20L12 16.9L7.09 20L8.45 13.97L4 9.27L9.91 8.26L12 2Z" fill="currentColor" />
            </svg>
            AI Search
          </div>
          <button className="ai-search-close" onClick={onClose} aria-label="Close">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <form className="ai-search-form" onSubmit={handleSubmit}>
          <div className="ai-search-input-wrap">
            <svg className="ai-search-input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
            </svg>
            <input
              ref={inputRef}
              className="ai-search-input"
              type="text"
              placeholder={mode === "tv" ? "Describe what you're looking for..." : "Describe the radio station you want..."}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={loading}
            />
            <button
              type="submit"
              className="ai-search-submit"
              disabled={loading || query.trim().length < 2}
            >
              {loading ? (
                <span className="ai-search-spinner" />
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
              )}
            </button>
          </div>
        </form>

        {!results && !loading && !error && (
          <div className="ai-search-examples">
            <p className="ai-search-examples-label">Try asking:</p>
            <div className="ai-search-examples-list">
              {examples.map((ex) => (
                <button
                  key={ex}
                  className="ai-search-example-chip"
                  onClick={() => handleExampleClick(ex)}
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>
        )}

        {error && (
          <div className="ai-search-error">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" />
            </svg>
            {error}
          </div>
        )}

        {loading && (
          <div className="ai-search-loading">
            <div className="ai-search-loading-dots">
              <span /><span /><span />
            </div>
            <p>Searching with AI...</p>
          </div>
        )}

        {results && !loading && (
          <div className="ai-search-results">
            {explanation && (
              <p className="ai-search-explanation">{explanation}</p>
            )}
            {results.length === 0 ? (
              <p className="ai-search-no-results">No matching {mode === "tv" ? "channels" : "stations"} found. Try a different description.</p>
            ) : (
              <div className="ai-search-results-list">
                {results.map((item) => (
                  <button
                    key={item.id}
                    className="ai-search-result-item"
                    onClick={() => handleItemClick(item)}
                  >
                    <div className="ai-result-icon">
                      {mode === "tv" ? (
                        item.logo ? (
                          <img src={item.logo} alt="" className="ai-result-logo" onError={(e) => { e.target.style.display = "none"; }} />
                        ) : (
                          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                            <rect x="2" y="7" width="20" height="15" rx="2" ry="2" /><polyline points="17 2 12 7 7 2" />
                          </svg>
                        )
                      ) : (
                        item.favicon ? (
                          <img src={item.favicon} alt="" className="ai-result-logo" onError={(e) => { e.target.style.display = "none"; }} />
                        ) : (
                          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                            <circle cx="12" cy="12" r="2" /><path d="M16.24 7.76a6 6 0 0 1 0 8.49" /><path d="M7.76 16.24a6 6 0 0 1 0-8.49" />
                          </svg>
                        )
                      )}
                    </div>
                    <div className="ai-result-info">
                      <span className="ai-result-name">{item.name}</span>
                      <span className="ai-result-meta">
                        {mode === "tv"
                          ? [item.categories, item.country_code].filter(Boolean).join(" · ")
                          : [item.tags, item.country_code].filter(Boolean).join(" · ")
                        }
                      </span>
                    </div>
                    <svg className="ai-result-play" width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                      <polygon points="5 3 19 12 5 21 5 3" />
                    </svg>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
