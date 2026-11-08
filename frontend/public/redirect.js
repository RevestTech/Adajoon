/**
 * Client-side redirect from non-www to www
 * This runs before React even loads to ensure all API calls use the correct domain
 */
(function() {
  if (window.location.hostname === 'adajoon.com') {
    const newUrl = window.location.href.replace('adajoon.com', 'www.adajoon.com');
    console.log('[Redirect] Non-www detected, redirecting to:', newUrl);
    window.location.replace(newUrl);
  }
})();
