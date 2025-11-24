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
  const url = `${API_BASE_URL}${endpoint}`;
  
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
    const responseData = await response.json();

    // Check if response is successful (HTTP status and success field)
    if (!response.ok || responseData.success === false) {
      // If response has a message, use it; otherwise use status text
      const errorMessage = responseData.message || responseData.error || response.statusText;
      const error = new Error(errorMessage);
      error.status = response.status;
      error.data = responseData;
      throw error;
    }

    return responseData;
  } catch (error) {
    // If it's already our custom error, rethrow it
    if (error.status) {
      throw error;
    }
    
    // Network error or other fetch errors
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

