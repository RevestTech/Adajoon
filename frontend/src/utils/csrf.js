/**
 * CSRF token utilities for secure cookie-based authentication.
 */

/**
 * Get CSRF token from cookie.
 */
export function getCsrfToken() {
  const match = document.cookie.match(/csrf_token=([^;]+)/);
  return match ? match[1] : null;
}

/**
 * Fetch a new CSRF token from the server.
 */
export async function fetchCsrfToken() {
  try {
    const response = await fetch('/api/csrf/token', {
      credentials: 'include', // Important: send cookies
    });
    
    if (response.ok) {
      const data = await response.json();
      return data.csrf_token;
    }
  } catch (error) {
    console.error('Failed to fetch CSRF token:', error);
  }
  return null;
}

/**
 * Make an authenticated fetch request with CSRF protection.
 */
export async function authenticatedFetch(url, options = {}) {
  const csrfToken = getCsrfToken();
  
  // For mutating requests, require CSRF token
  const method = options.method?.toUpperCase() || 'GET';
  const isMutating = !['GET', 'HEAD', 'OPTIONS'].includes(method);
  
  if (isMutating && !csrfToken) {
    // Try to fetch a new token
    const newToken = await fetchCsrfToken();
    if (!newToken) {
      throw new Error('Failed to get CSRF token');
    }
  }
  
  // Build headers
  const headers = {
    ...options.headers,
    ...(csrfToken && isMutating ? { 'X-CSRF-Token': csrfToken } : {}),
  };
  
  // Make request with credentials (cookies)
  return fetch(url, {
    ...options,
    headers,
    credentials: 'include', // Always include cookies
  });
}

/**
 * Logout user by clearing cookies.
 */
export async function logout() {
  try {
    await authenticatedFetch('/api/csrf/logout', {
      method: 'POST',
    });
  } catch (error) {
    console.error('Logout failed:', error);
  }
  
  // Clear any localStorage remnants (migration support)
  try {
    localStorage.removeItem('adajoon_token');
    localStorage.removeItem('adajoon_user');
  } catch {
    // Ignore
  }
}
