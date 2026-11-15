/**
 * Parental control utilities.
 *
 * Adult-content filtering itself is enforced server-side (channels'
 * is_nsfw column, radio's tag-keyword filter in radio_service.py) based on
 * the signed-in user's kids_mode_enabled - not here. A client-side filter
 * can't be the actual security boundary since it's trivially bypassed by
 * calling the API directly.
 */

/**
 * Store PIN unlock timestamp in session storage.
 */
export function setPinUnlocked() {
  try {
    sessionStorage.setItem('pin_unlocked_at', Date.now().toString());
  } catch {
    // Ignore storage errors
  }
}

/**
 * Check if PIN was recently unlocked (session-based).
 * @param {number} maxAgeMinutes - Max age in minutes (default: 30)
 */
export function isPinUnlocked(maxAgeMinutes = 30) {
  try {
    const unlockedAt = sessionStorage.getItem('pin_unlocked_at');
    if (!unlockedAt) return false;
    
    const elapsed = Date.now() - parseInt(unlockedAt, 10);
    const maxAge = maxAgeMinutes * 60 * 1000;
    
    return elapsed < maxAge;
  } catch {
    return false;
  }
}

/**
 * Clear PIN unlock status.
 */
export function clearPinUnlock() {
  try {
    sessionStorage.removeItem('pin_unlocked_at');
  } catch {
    // Ignore
  }
}
