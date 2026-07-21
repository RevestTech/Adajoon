/**
 * Custom Self-Hosted Analytics
 * Sends events to our own backend API instead of third-party services.
 */

const getSessionId = () => {
  let sessionId = sessionStorage.getItem("adajoon_session_id");
  if (!sessionId) {
    sessionId = `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
    sessionStorage.setItem("adajoon_session_id", sessionId);
  }
  return sessionId;
};

let eventQueue = [];
let flushTimeout = null;

const baseProps = () => ({
  timestamp: new Date().toISOString(),
  url: typeof window !== "undefined" ? window.location.href : "",
  path: typeof window !== "undefined" ? window.location.pathname : "",
  search: typeof window !== "undefined" ? window.location.search : "",
  referrer: typeof document !== "undefined" ? document.referrer || "" : "",
});

const flushEvents = async ({ keepalive = false } = {}) => {
  if (eventQueue.length === 0) return;

  const events = [...eventQueue];
  eventQueue = [];
  if (flushTimeout) {
    clearTimeout(flushTimeout);
    flushTimeout = null;
  }

  const body = JSON.stringify(events);

  try {
    if (keepalive && typeof navigator !== "undefined" && navigator.sendBeacon) {
      const blob = new Blob([body], { type: "application/json" });
      const ok = navigator.sendBeacon("/api/analytics/batch", blob);
      if (ok) return;
    }

    await fetch("/api/analytics/batch", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body,
      keepalive: Boolean(keepalive),
    });
  } catch (error) {
    if (import.meta.env.DEV) {
      console.error("[Analytics] Failed to send events:", error);
    }
    // Re-queue on failure (best effort)
    eventQueue = events.concat(eventQueue).slice(0, 200);
  }
};

const scheduleFlush = (delayMs = 5000) => {
  if (flushTimeout) clearTimeout(flushTimeout);
  flushTimeout = setTimeout(() => flushEvents(), delayMs);
};

export const analytics = {
  getSessionId,

  track(eventName, properties = {}, { urgent = false } = {}) {
    const event = {
      event_name: eventName,
      session_id: getSessionId(),
      properties: {
        ...baseProps(),
        ...properties,
      },
    };

    if (import.meta.env.DEV) {
      console.log("[Analytics]", eventName, properties);
    }

    eventQueue.push(event);

    if (urgent) {
      flushEvents({ keepalive: true });
    } else {
      scheduleFlush(eventName.startsWith("Auth ") || eventName.includes("Login") ? 500 : 5000);
    }
  },

  flushNow() {
    return flushEvents({ keepalive: true });
  },

  identify(userId, traits = {}) {
    this.track("User Identified", { user_id: userId, ...traits }, { urgent: true });
  },

  page(pageName, properties = {}) {
    this.track("Page View", { page: pageName, ...properties });
  },

  /**
   * Tight screen / surface tracking (mode, map, favorites, etc.)
   */
  trackScreen(screen, properties = {}) {
    this.track("Screen View", {
      screen,
      ...properties,
    });
  },

  trackNavigation(fromScreen, toScreen, properties = {}) {
    this.track("Navigation", {
      from_screen: fromScreen,
      to_screen: toScreen,
      ...properties,
    });
  },

  reset() {
    this.track("User Logged Out", {}, { urgent: true });
    sessionStorage.removeItem("adajoon_session_id");
  },

  trackSignup(method, userId) {
    this.track(
      "User Signed Up",
      { method, user_id: userId },
      { urgent: true }
    );
  },

  trackLogin(method, userId, extra = {}) {
    this.track(
      "User Logged In",
      { method, user_id: userId, success: true, ...extra },
      { urgent: true }
    );
  },

  trackLoginAttempt(method, extra = {}) {
    this.track("Auth Login Attempted", { method, ...extra }, { urgent: true });
  },

  trackLoginFailure(method, error, extra = {}) {
    const message =
      typeof error === "string"
        ? error
        : error?.message || error?.detail || "unknown_error";
    this.track(
      "Auth Login Failed",
      {
        method,
        success: false,
        error: String(message).slice(0, 300),
        ...extra,
      },
      { urgent: true }
    );
  },

  trackAuthSessionLost(reason, extra = {}) {
    this.track(
      "Auth Session Lost",
      { reason, ...extra },
      { urgent: true }
    );
  },

  trackPlay(itemType, item) {
    this.track("Content Played", {
      item_type: itemType,
      item_id: item.id,
      item_name: item.name,
      item_country: item.country || item.country_code,
      item_category: item.categories || item.tags,
    });
  },

  trackSearch(query, resultCount, itemType, extra = {}) {
    this.track("Search Performed", {
      query: String(query || "").slice(0, 200),
      result_count: resultCount,
      item_type: itemType,
      ...extra,
    });
  },

  trackFavorite(action, itemType, item) {
    this.track("Favorite Action", {
      action,
      item_type: itemType,
      item_id: item.id,
      item_name: item.name,
    });
  },

  trackVote(voteType, itemType, item) {
    this.track("Vote Cast", {
      vote_type: voteType,
      item_type: itemType,
      item_id: item.id,
      item_name: item.name,
    });
  },

  trackShare(method, itemType, item) {
    this.track("Content Shared", {
      method,
      item_type: itemType,
      item_id: item.id,
      item_name: item.name,
    });
  },

  trackFilter(filterType, filterValue, itemType) {
    this.track("Filter Applied", {
      filter_type: filterType,
      filter_value: filterValue,
      item_type: itemType,
    });
  },
};

window.addEventListener("beforeunload", () => {
  flushEvents({ keepalive: true });
});

if (typeof window !== "undefined") {
  analytics.page("App Loaded");
}

export default analytics;
