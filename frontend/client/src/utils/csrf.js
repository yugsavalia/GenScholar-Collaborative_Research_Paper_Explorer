/**
 * CSRF Token Utilities
 * Functions to get and manage CSRF tokens for Django backend
 */

/**
 * Get a cookie value by name
 * @param {string} name - Cookie name
 * @returns {string|null} - Cookie value or null if not found
 */
export function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === name + '=') {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

/**
 * Get CSRF token from cookie or fetch from server
 * @param {boolean} forceRefresh - Force refresh from server even if cookie exists
 * @returns {Promise<string>} - CSRF token
 */
export async function getCsrfToken(forceRefresh = false) {
  // First, try to get from cookie
  if (!forceRefresh) {
    const token = getCookie('csrftoken');
    if (token) {
      return token;
    }
  }

  // If not in cookie, fetch from server
  try {
    const { API_BASE_URL } = await import('../api/config.js');
    const response = await fetch(`${API_BASE_URL}/api/auth/csrf/`, {
      method: 'GET',
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch CSRF token: ${response.statusText}`);
    }

    const data = await response.json();
    
    // Token should now be in cookie, but also return it from response
    return data.data?.csrf_token || getCookie('csrftoken') || '';
  } catch (error) {
    console.error('Error fetching CSRF token:', error);
    // Fallback to cookie if fetch fails
    return getCookie('csrftoken') || '';
  }
}

/**
 * Initialize CSRF token on app load
 * Call this once when the app starts
 * @returns {Promise<void>}
 */
export async function initializeCsrfToken() {
  try {
    await getCsrfToken();
  } catch (error) {
    console.warn('Failed to initialize CSRF token:', error);
  }
}

