/**
 * Custom Self-Hosted Analytics
 * Sends events to our own backend API instead of third-party services.
 */

// Generate unique session ID (persists for browser session)
const getSessionId = () => {
  let sessionId = sessionStorage.getItem('adajoon_session_id');
  if (!sessionId) {
    sessionId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    sessionStorage.setItem('adajoon_session_id', sessionId);
  }
  return sessionId;
};

// Event queue for batching
let eventQueue = [];
let flushTimeout = null;

// Flush events to backend
const flushEvents = async () => {
  if (eventQueue.length === 0) return;
  
  const events = [...eventQueue];
  eventQueue = [];
  
  try {
    await fetch('/api/analytics/batch', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(events),
    });
  } catch (error) {
    if (import.meta.env.DEV) {
      console.error('[Analytics] Failed to send events:', error);
    }
  }
};

// Schedule flush (debounced)
const scheduleFlush = () => {
  if (flushTimeout) clearTimeout(flushTimeout);
  flushTimeout = setTimeout(flushEvents, 5000); // Flush every 5 seconds
};

/**
 * Analytics utility functions
 */
export const analytics = {
  /**
   * Track an event
   */
  track(eventName, properties = {}) {
    const event = {
      event_name: eventName,
      session_id: getSessionId(),
      properties: {
        ...properties,
        timestamp: new Date().toISOString(),
        url: window.location.href,
        path: window.location.pathname,
      },
    };
    
    // Log in development
    if (import.meta.env.DEV) {
      console.log('[Analytics]', eventName, properties);
    }
    
    // Add to queue
    eventQueue.push(event);
    scheduleFlush();
  },

  /**
   * Identify a user (called on login)
   */
  identify(userId, traits = {}) {
    this.track('User Identified', {
      user_id: userId,
      ...traits,
    });
  },

  /**
   * Track page view
   */
  page(pageName, properties = {}) {
    this.track('Page View', {
      page: pageName,
      ...properties,
    });
  },

  /**
   * Reset user (on logout)
   */
  reset() {
    // Generate new session ID
    sessionStorage.removeItem('adajoon_session_id');
    this.track('User Logged Out');
  },

  /**
   * Track user signup
   */
  trackSignup(method, userId) {
    this.track('User Signed Up', {
      method,
      user_id: userId,
    });
  },

  /**
   * Track user login
   */
  trackLogin(method, userId) {
    this.track('User Logged In', {
      method,
      user_id: userId,
    });
  },

  /**
   * Track channel/station play
   */
  trackPlay(itemType, item) {
    this.track('Content Played', {
      item_type: itemType,
      item_id: item.id,
      item_name: item.name,
      item_country: item.country,
      item_category: item.categories || item.tags,
    });
  },

  /**
   * Track search
   */
  trackSearch(query, resultCount, itemType) {
    this.track('Search Performed', {
      query,
      result_count: resultCount,
      item_type: itemType,
    });
  },

  /**
   * Track favorite action
   */
  trackFavorite(action, itemType, item) {
    this.track('Favorite Action', {
      action,
      item_type: itemType,
      item_id: item.id,
      item_name: item.name,
    });
  },

  /**
   * Track vote
   */
  trackVote(voteType, itemType, item) {
    this.track('Vote Cast', {
      vote_type: voteType,
      item_type: itemType,
      item_id: item.id,
      item_name: item.name,
    });
  },

  /**
   * Track share
   */
  trackShare(method, itemType, item) {
    this.track('Content Shared', {
      method,
      item_type: itemType,
      item_id: item.id,
      item_name: item.name,
    });
  },

  /**
   * Track filter change
   */
  trackFilter(filterType, filterValue, itemType) {
    this.track('Filter Applied', {
      filter_type: filterType,
      filter_value: filterValue,
      item_type: itemType,
    });
  },
};

// Flush events before page unload
window.addEventListener('beforeunload', () => {
  flushEvents();
});

// Track initial page load
if (typeof window !== 'undefined') {
  analytics.page('App Loaded');
}

export default analytics;
