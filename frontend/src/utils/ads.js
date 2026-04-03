/**
 * Google IMA SDK integration for video/audio ads.
 */

// Default VAST ad tag URL (replace with your ad server)
const DEFAULT_AD_TAG = import.meta.env.VITE_AD_TAG_URL || 
  'https://pubads.g.doubleclick.net/gampad/ads?iu=/21775744923/external/single_ad_samples&sz=640x480&cust_params=sample_ct%3Dlinear&ciu_szs=300x250%2C728x90&gdfp_req=1&output=vast&unviewed_position_start=1&env=vp&impl=s&correlator=';

/**
 * Initialize IMA SDK and create ads loader.
 */
export function createAdsLoader(adDisplayContainer, videoElement) {
  if (!window.google?.ima) {
    console.warn('IMA SDK not loaded');
    return null;
  }

  const adsLoader = new google.ima.AdsLoader(adDisplayContainer);
  
  // Set ad will auto play
  adsLoader.getSettings().setVpaidMode(google.ima.ImaSdkSettings.VpaidMode.ENABLED);
  
  return adsLoader;
}

/**
 * Create IMA ad display container.
 */
export function createAdDisplayContainer(videoElement, adContainerElement) {
  if (!window.google?.ima) return null;
  
  return new google.ima.AdDisplayContainer(
    adContainerElement,
    videoElement
  );
}

/**
 * Request ads from ad server.
 */
export function requestAds(adsLoader, adDisplayContainer, width = 640, height = 360) {
  if (!adsLoader || !window.google?.ima) return;
  
  const adsRequest = new google.ima.AdsRequest();
  adsRequest.adTagUrl = DEFAULT_AD_TAG;
  adsRequest.linearAdSlotWidth = width;
  adsRequest.linearAdSlotHeight = height;
  adsRequest.nonLinearAdSlotWidth = width;
  adsRequest.nonLinearAdSlotHeight = height / 3;
  
  adsLoader.requestAds(adsRequest);
}

/**
 * Setup IMA ads manager event listeners.
 */
export function setupAdsManager(
  adsManager,
  callbacks = {}
) {
  if (!adsManager) return;
  
  const {
    onAdError = () => {},
    onAdStarted = () => {},
    onAdComplete = () => {},
    onAdSkipped = () => {},
    onAllAdsComplete = () => {},
  } = callbacks;
  
  // Ad error event
  adsManager.addEventListener(
    google.ima.AdErrorEvent.Type.AD_ERROR,
    onAdError
  );
  
  // Ad started
  adsManager.addEventListener(
    google.ima.AdEvent.Type.STARTED,
    onAdStarted
  );
  
  // Ad completed
  adsManager.addEventListener(
    google.ima.AdEvent.Type.COMPLETE,
    onAdComplete
  );
  
  // User skipped ad
  adsManager.addEventListener(
    google.ima.AdEvent.Type.SKIPPED,
    onAdSkipped
  );
  
  // All ads completed
  adsManager.addEventListener(
    google.ima.AdEvent.Type.ALL_ADS_COMPLETED,
    onAllAdsComplete
  );
}

/**
 * Check if ads are supported.
 */
export function areAdsSupported() {
  return !!(window.google?.ima);
}

/**
 * Determine if ads should be shown (based on user tier, etc.).
 * @param {Object} user - Current user object
 */
export function shouldShowAds(user) {
  // Show ads to:
  // - Anonymous users
  // - Free tier users
  // Don't show to premium subscribers
  if (!user) return true;
  
  // Check subscription tier (to be implemented with MONET-002)
  const tier = user.subscription_tier || 'free';
  return tier === 'free';
}
