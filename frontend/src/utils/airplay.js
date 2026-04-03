/**
 * AirPlay integration utilities.
 */

/**
 * Check if AirPlay is available (Safari on macOS/iOS).
 */
export function isAirPlayAvailable() {
  // Check for WebKit's AirPlay API
  return !!(window.WebKitPlaybackTargetAvailabilityEvent);
}

/**
 * Enable AirPlay for a video/audio element.
 * @param {HTMLMediaElement} mediaElement - The video or audio element
 */
export function enableAirPlay(mediaElement) {
  if (!mediaElement) return;
  
  // Enable AirPlay on the media element
  mediaElement.setAttribute('x-webkit-airplay', 'allow');
  
  // For iOS, also set these attributes
  if (/iPad|iPhone|iPod/.test(navigator.userAgent)) {
    mediaElement.setAttribute('webkit-playsinline', 'true');
    mediaElement.setAttribute('playsinline', 'true');
  }
}

/**
 * Show native AirPlay picker for a media element.
 * @param {HTMLMediaElement} mediaElement - The video or audio element
 */
export function showAirPlayPicker(mediaElement) {
  if (!mediaElement || !mediaElement.webkitShowPlaybackTargetPicker) {
    console.warn('AirPlay picker not available');
    return false;
  }
  
  try {
    mediaElement.webkitShowPlaybackTargetPicker();
    return true;
  } catch (error) {
    console.error('Failed to show AirPlay picker:', error);
    return false;
  }
}

/**
 * Check if media is currently playing via AirPlay.
 * @param {HTMLMediaElement} mediaElement - The video or audio element
 */
export function isAirPlaying(mediaElement) {
  if (!mediaElement) return false;
  
  // Check webkitCurrentPlaybackTargetIsWireless
  return mediaElement.webkitCurrentPlaybackTargetIsWireless === true;
}

/**
 * Listen for AirPlay availability changes.
 * @param {HTMLMediaElement} mediaElement - The video or audio element
 * @param {Function} callback - Called with boolean when availability changes
 */
export function onAirPlayAvailabilityChange(mediaElement, callback) {
  if (!mediaElement || !window.WebKitPlaybackTargetAvailabilityEvent) {
    return () => {}; // No-op cleanup
  }
  
  const handler = (event) => {
    const available = event.availability === 'available';
    callback(available);
  };
  
  mediaElement.addEventListener('webkitplaybacktargetavailabilitychanged', handler);
  
  // Return cleanup function
  return () => {
    mediaElement.removeEventListener('webkitplaybacktargetavailabilitychanged', handler);
  };
}

/**
 * Listen for AirPlay state changes.
 * @param {HTMLMediaElement} mediaElement - The video or audio element
 * @param {Function} callback - Called with boolean when state changes
 */
export function onAirPlayStateChange(mediaElement, callback) {
  if (!mediaElement) {
    return () => {}; // No-op cleanup
  }
  
  const handler = () => {
    const isPlaying = isAirPlaying(mediaElement);
    callback(isPlaying);
  };
  
  mediaElement.addEventListener('webkitcurrentplaybacktargetiswirelesschanged', handler);
  
  // Return cleanup function
  return () => {
    mediaElement.removeEventListener('webkitcurrentplaybacktargetiswirelesschanged', handler);
  };
}
