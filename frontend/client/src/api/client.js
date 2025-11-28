/**
 * Simple API Client
 * Fetch wrapper for making API requests to the Django backend
 */

import { API_BASE_URL } from './config.js';
import { getCsrfToken } from '../utils/csrf.js';

/**
 * Make an API request
 * @param {string} method - HTTP method (GET, POST, etc.)
 * @param {string} endpoint - API endpoint (e.g., '/api/auth/login/')
 * @param {object} data - Request body data (optional, for POST/PUT requests)
 * @param {object} options - Additional fetch options (optional)
 * @returns {Promise<object>} - Response data
 */
export async function apiRequest(method, endpoint, data = null, options = {}) {
  // Ensure endpoint starts with / and API_BASE_URL doesn't end with /
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${API_BASE_URL}${cleanEndpoint}`;
  
  // Get CSRF token for state-changing requests
  let csrfToken = null;
  if (method === 'POST' || method === 'PUT' || method === 'PATCH' || method === 'DELETE') {
    csrfToken = await getCsrfToken();
  }
  
  // Build headers
  const headers = {
    ...options.headers,
  };
  
  // Add Content-Type only if not FormData (FormData sets its own Content-Type with boundary)
  if (!(data instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  
  // Add CSRF token for state-changing requests
  if (csrfToken) {
    headers['X-CSRFToken'] = csrfToken;
  }
  
  const config = {
    method,
    headers,
    credentials: 'include', // Include cookies for session authentication
    ...options,
  };

  // Add body for POST/PUT/PATCH/DELETE requests
  if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
    // If FormData, use directly; otherwise stringify JSON
    config.body = data instanceof FormData ? data : JSON.stringify(data);
  }

  try {
    const response = await fetch(url, config);
    
    // Handle 204 No Content responses (common for DELETE operations)
    if (response.status === 204) {
      if (!response.ok) {
        const error = new Error(`Server returned ${response.status} ${response.statusText}`);
        error.status = response.status;
        throw error;
      }
      return { success: true };
    }
    
    // Check Content-Type to ensure we're getting JSON, not HTML
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      // If we get HTML, it's likely a 404 or error page
      const text = await response.text();
      console.error(`[API Client] Received non-JSON response (${contentType}) for ${endpoint}:`, text.substring(0, 200));
      console.error(`[API Client] Full URL: ${url}`);
      console.error(`[API Client] Response status: ${response.status}`);
      
      let errorMessage = `Server returned ${response.status} ${response.statusText}`;
      if (response.status === 404) {
        errorMessage = `API endpoint not found: ${endpoint}. Make sure the backend server is running on ${API_BASE_URL} and the endpoint exists.`;
      } else if (response.status === 500) {
        errorMessage = `Server error: ${response.statusText}. Check backend server logs.`;
      } else if (response.status === 0) {
        errorMessage = `Cannot connect to backend server at ${API_BASE_URL}. Is the server running?`;
      } else if (response.status === 403) {
        errorMessage = `Access forbidden. This may be a CORS or CSRF issue. Check that ${window.location.origin} is allowed by the backend CORS settings.`;
      }
      
      const error = new Error(errorMessage);
      error.status = response.status;
      error.data = { rawResponse: text.substring(0, 500) };
      throw error;
    }
    
    const responseData = await response.json();

    // Check if response is successful (HTTP status)
    if (!response.ok) {
      // If response has a message, use it; otherwise use status text
      const errorMessage = responseData.message || responseData.error || responseData.detail || response.statusText;
      const error = new Error(errorMessage);
      error.status = response.status;
      error.data = responseData;
      throw error;
    }

    // For custom endpoints, check if there's a 'success' field
    if (responseData.success === false) {
      const errorMessage = responseData.message || responseData.error || response.statusText;
      const error = new Error(errorMessage);
      error.status = response.status;
      error.data = responseData;
      throw error;
    }

    return responseData;
  } catch (error) {
    // If it's already our custom error, rethrow it
    if (error.status !== undefined) {
      throw error;
    }
    
    // Network error or JSON parsing error
    // Check if it's a CORS error
    if (error.message.includes('CORS') || error.message.includes('Failed to fetch') || error.name === 'TypeError') {
      throw new Error(`CORS error: Cannot connect to backend at ${API_BASE_URL}. Make sure the backend allows requests from ${window.location.origin}`);
    }
    
    throw new Error(`API request failed: ${error.message}`);
  }
}

/**
 * GET request
 * @param {string} endpoint - API endpoint
 * @param {object} options - Additional fetch options
 * @returns {Promise<object>} - Response data
 */
export function apiGet(endpoint, options = {}) {
  return apiRequest('GET', endpoint, null, options);
}

/**
 * POST request
 * @param {string} endpoint - API endpoint
 * @param {object} data - Request body data
 * @param {object} options - Additional fetch options
 * @returns {Promise<object>} - Response data
 */
export function apiPost(endpoint, data, options = {}) {
  return apiRequest('POST', endpoint, data, options);
}

/**
 * PUT request
 * @param {string} endpoint - API endpoint
 * @param {object} data - Request body data
 * @param {object} options - Additional fetch options
 * @returns {Promise<object>} - Response data
 */
export function apiPut(endpoint, data, options = {}) {
  return apiRequest('PUT', endpoint, data, options);
}

/**
 * PATCH request
 * @param {string} endpoint - API endpoint
 * @param {object} data - Request body data
 * @param {object} options - Additional fetch options
 * @returns {Promise<object>} - Response data
 */
export function apiPatch(endpoint, data, options = {}) {
  return apiRequest('PATCH', endpoint, data, options);
}

/**
 * DELETE request
 * @param {string} endpoint - API endpoint
 * @param {object} options - Additional fetch options
 * @returns {Promise<object>} - Response data
 */
export function apiDelete(endpoint, options = {}) {
  return apiRequest('DELETE', endpoint, null, options);
}

