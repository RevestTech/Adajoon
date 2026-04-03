import mixpanel from 'mixpanel-browser';

// Initialize Mixpanel (set token in .env or disable for development)
const MIXPANEL_TOKEN = import.meta.env.VITE_MIXPANEL_TOKEN || '';
const IS_PRODUCTION = import.meta.env.PROD;
const ANALYTICS_ENABLED = IS_PRODUCTION && MIXPANEL_TOKEN;

if (ANALYTICS_ENABLED) {
  mixpanel.init(MIXPANEL_TOKEN, {
    debug: false,
    track_pageview: true,
    persistence: 'localStorage',
    ignore_dnt: false,
  });
} else {
  console.log('[Analytics] Mixpanel disabled (no token or dev mode)');
}

/**
 * Analytics utility functions
 */
export const analytics = {
  /**
   * Track an event
   */
  track(eventName, properties = {}) {
    if (!ANALYTICS_ENABLED) {
      console.log('[Analytics]', eventName, properties);
      return;
    }
    
    mixpanel.track(eventName, {
      ...properties,
      timestamp: new Date().toISOString(),
    });
  },

  /**
   * Identify a user
   */
  identify(userId, traits = {}) {
    if (!ANALYTICS_ENABLED) return;
    
    mixpanel.identify(userId);
    if (Object.keys(traits).length > 0) {
      mixpanel.people.set(traits);
    }
  },

  /**
   * Track page view
   */
  page(pageName, properties = {}) {
    if (!ANALYTICS_ENABLED) return;
    
    mixpanel.track('Page View', {
      page: pageName,
      url: window.location.href,
      ...properties,
    });
  },

  /**
   * Reset user (on logout)
   */
  reset() {
    if (!ANALYTICS_ENABLED) return;
    mixpanel.reset();
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
      action, // 'add' or 'remove'
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
      method, // 'native' or 'clipboard'
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

// Track initial page load
if (typeof window !== 'undefined') {
  analytics.page('App Loaded');
}

export default analytics;
