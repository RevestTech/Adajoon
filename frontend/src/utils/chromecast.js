/**
 * Google Cast (Chromecast) integration utilities.
 */

/**
 * Initialize Cast SDK and return cast context.
 */
export function initializeCast() {
  return new Promise((resolve) => {
    if (!window.chrome?.cast) {
      console.warn('Cast SDK not available');
      resolve(null);
      return;
    }

    window['__onGCastApiAvailable'] = (isAvailable) => {
      if (isAvailable) {
        const context = cast.framework.CastContext.getInstance();
        context.setOptions({
          receiverApplicationId: chrome.cast.media.DEFAULT_MEDIA_RECEIVER_APP_ID,
          autoJoinPolicy: chrome.cast.AutoJoinPolicy.ORIGIN_SCOPED,
        });
        resolve(context);
      } else {
        resolve(null);
      }
    };
  });
}

/**
 * Check if Cast is available.
 */
export function isCastAvailable() {
  return !!(window.chrome?.cast?.framework);
}

/**
 * Get current Cast session.
 */
export function getCastSession() {
  if (!isCastAvailable()) return null;
  
  const context = cast.framework.CastContext.getInstance();
  return context.getCurrentSession();
}

/**
 * Cast a media item to Chromecast.
 * @param {Object} item - Media item with url, title, image
 * @param {string} item.url - Stream URL
 * @param {string} item.title - Content title
 * @param {string} item.logo - Content logo/image
 * @param {string} item.type - 'tv' or 'radio'
 */
export async function castMedia(item) {
  const session = getCastSession();
  if (!session) {
    throw new Error('No active Cast session');
  }

  // Determine content type
  const contentType = item.type === 'radio' 
    ? 'audio/mp3'  // Most radio streams are MP3
    : 'application/x-mpegURL';  // HLS for video

  // Build media info
  const mediaInfo = new chrome.cast.media.MediaInfo(item.url, contentType);
  mediaInfo.metadata = new chrome.cast.media.GenericMediaMetadata();
  mediaInfo.metadata.title = item.title;
  mediaInfo.metadata.subtitle = item.subtitle || '';
  
  if (item.logo) {
    mediaInfo.metadata.images = [
      new chrome.cast.Image(item.logo)
    ];
  }

  // Create load request
  const request = new chrome.cast.media.LoadRequest(mediaInfo);
  request.autoplay = true;

  try {
    await session.loadMedia(request);
    return true;
  } catch (error) {
    console.error('Failed to cast media:', error);
    throw error;
  }
}

/**
 * Stop casting.
 */
export function stopCasting() {
  const session = getCastSession();
  if (session) {
    session.endSession(true);
  }
}

/**
 * Check if currently casting.
 */
export function isCasting() {
  const session = getCastSession();
  return !!(session && session.getSessionState() === cast.framework.SessionState.SESSION_STARTED);
}

/**
 * Get Cast button element that can be inserted into DOM.
 * Returns a google-cast-launcher custom element.
 */
export function createCastButton() {
  const button = document.createElement('google-cast-launcher');
  return button;
}
