import { useEffect, useRef, useState } from "react";

/**
 * Bottom tab bar for TV/Radio/Map/Movies, shown only on real phones
 * (see .mobile-tab-bar's media query in index.css) in place of the
 * header's .mode-switcher, which is hidden at that width. Mirrors
 * Header.jsx's mode-switcher exactly: same `mode`/`onModeSwitch` props,
 * same four destinations, just laid out as a persistent bottom row
 * instead of a top icon strip.
 *
 * On a phone that isn't installed as a standalone PWA, the browser's
 * own bottom toolbar (Safari/Chrome) is always on screen too, so this
 * bar and the browser's stack into two full rows. Auto-hiding on
 * scroll-down and revealing on scroll-up (the same pattern X/Instagram
 * use on mobile web) keeps that doubled-up footprint to a minimum -
 * it only shows at rest or when the user scrolls back up to navigate.
 */
const TABS = [
  {
    key: "tv",
    label: "TV",
    icon: (filled) => (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={filled ? 0 : 2} strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="7" width="20" height="15" rx="2" ry="2" fill={filled ? "currentColor" : "none"} />
        <polyline points="17 2 12 7 7 2" />
      </svg>
    ),
  },
  {
    key: "radio",
    label: "Radio",
    icon: (filled) => (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="2" fill={filled ? "currentColor" : "none"} />
        <path d="M16.24 7.76a6 6 0 0 1 0 8.49" />
        <path d="M7.76 16.24a6 6 0 0 1 0-8.49" />
      </svg>
    ),
  },
  {
    key: "map",
    label: "Map",
    icon: (filled) => (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" fill={filled ? "currentColor" : "none"} fillOpacity={filled ? 0.18 : 0} />
        <line x1="2" y1="12" x2="22" y2="12" />
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
      </svg>
    ),
  },
  {
    key: "movies",
    label: "Movies",
    icon: (filled) => (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={filled ? 0 : 2} strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="3" width="20" height="18" rx="2" ry="2" fill={filled ? "currentColor" : "none"} />
        {!filled && (
          <>
            <line x1="7" y1="3" x2="7" y2="21" />
            <line x1="17" y1="3" x2="17" y2="21" />
            <line x1="2" y1="9" x2="7" y2="9" />
            <line x1="2" y1="15" x2="7" y2="15" />
            <line x1="17" y1="9" x2="22" y2="9" />
            <line x1="17" y1="15" x2="22" y2="15" />
          </>
        )}
      </svg>
    ),
  },
];

const SCROLL_THRESHOLD = 8;
const TOP_BUFFER = 40;

export default function BottomTabBar({ mode, onModeSwitch }) {
  const [hidden, setHidden] = useState(false);
  const lastRef = useRef({ el: null, top: 0 });

  useEffect(() => {
    // Scroll events don't bubble, but they do reach capture-phase
    // listeners on ancestors - this catches scrolling inside whichever
    // per-mode container (.content-body, the map view, etc.) is active,
    // without needing to know which one that is.
    const onScroll = (e) => {
      const el = e.target;
      if (!el || typeof el.scrollTop !== "number") return;
      const last = lastRef.current;
      if (last.el !== el) {
        lastRef.current = { el, top: el.scrollTop };
        return;
      }
      const delta = el.scrollTop - last.top;
      if (el.scrollTop > TOP_BUFFER && delta > SCROLL_THRESHOLD) setHidden(true);
      else if (delta < -SCROLL_THRESHOLD || el.scrollTop <= TOP_BUFFER) setHidden(false);
      lastRef.current = { el, top: el.scrollTop };
    };
    document.addEventListener("scroll", onScroll, true);
    return () => document.removeEventListener("scroll", onScroll, true);
  }, []);

  return (
    <nav
      className={`mobile-tab-bar${hidden ? " mobile-tab-bar--hidden" : ""}`}
      aria-label="Main navigation"
      aria-hidden={hidden}
    >
      {TABS.map((tab) => {
        const active = mode === tab.key;
        return (
          <button
            key={tab.key}
            type="button"
            className={`mobile-tab-bar-btn ${active ? "active" : ""}`}
            onClick={() => onModeSwitch(tab.key)}
            aria-current={active ? "page" : undefined}
            aria-label={tab.label}
            tabIndex={hidden ? -1 : 0}
          >
            {tab.icon(active)}
            <span className="mobile-tab-bar-label">{tab.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
