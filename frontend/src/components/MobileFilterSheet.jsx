import { useState } from "react";

/**
 * Wraps the existing `.quality-filter` button row so narrow screens get a
 * tap-to-open bottom sheet (with a sticky "Show results" footer) instead of
 * the cramped horizontal-scroll chip row. On wider screens this renders as
 * `display: contents` (see index.css), so the wrapped content lays out
 * exactly as it did before - no behavior or markup change for desktop.
 */
export default function MobileFilterSheet({ children, activeCount = 0, label = "Filters" }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="filter-sheet-root">
      <button type="button" className="filter-sheet-trigger" onClick={() => setOpen(true)}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
          <line x1="4" y1="6" x2="20" y2="6" /><circle cx="9" cy="6" r="2" fill="currentColor" stroke="none" />
          <line x1="4" y1="12" x2="20" y2="12" /><circle cx="15" cy="12" r="2" fill="currentColor" stroke="none" />
          <line x1="4" y1="18" x2="20" y2="18" /><circle cx="11" cy="18" r="2" fill="currentColor" stroke="none" />
        </svg>
        {label}
        {activeCount > 0 && <span className="filter-sheet-trigger-count">{activeCount}</span>}
      </button>

      <div
        className={`filter-sheet-backdrop ${open ? "open" : ""}`}
        onClick={() => setOpen(false)}
        aria-hidden={!open}
      />

      <div className={`filter-sheet ${open ? "open" : ""}`} role="dialog" aria-modal="true" aria-label={label}>
        <div className="filter-sheet-handle" />
        <div className="filter-sheet-body">{children}</div>
        <button type="button" className="filter-sheet-apply" onClick={() => setOpen(false)}>
          Show results
        </button>
      </div>
    </div>
  );
}
