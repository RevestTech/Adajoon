/**
 * Parental control utilities.
 */

// Adult content keywords/patterns (case-insensitive)
const NSFW_KEYWORDS = [
  'xxx', 'adult', 'porn', 'sex', 'erotic', 'sexy', 'nude', 'playboy',
  'penthouse', 'hustler', '18+', '+18', 'adults only', 'mature',
];

// Adult categories
const NSFW_CATEGORIES = [
  'XXX', 'Adult', 'Erotic', 'Porn', 'xxx',
];

/**
 * Check if content should be hidden in kids mode.
 * @param {Object} item - Channel or station object
 * @returns {boolean} - True if content is adult/NSFW
 */
export function isAdultContent(item) {
  if (!item) return false;
  
  const name = (item.name || '').toLowerCase();
  const categories = (item.categories || '').toLowerCase();
  const tags = (item.tags || '').toLowerCase();
  
  // Check name for NSFW keywords
  for (const keyword of NSFW_KEYWORDS) {
    if (name.includes(keyword)) return true;
  }
  
  // Check categories/tags
  const contentTags = `${categories} ${tags}`;
  for (const cat of NSFW_CATEGORIES) {
    if (contentTags.includes(cat.toLowerCase())) return true;
  }
  
  return false;
}

/**
 * Filter content list for kids mode.
 * @param {Array} items - List of channels or stations
 * @returns {Array} - Filtered list without adult content
 */
export function filterAdultContent(items) {
  if (!items || !Array.isArray(items)) return [];
  return items.filter(item => !isAdultContent(item));
}

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
