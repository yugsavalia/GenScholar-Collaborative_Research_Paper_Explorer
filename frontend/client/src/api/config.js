/**
 * API Configuration
 * Base URL for the Django backend API
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Build a full API URL from an endpoint path
 * Handles trailing slashes to prevent double slashes
 * @param {string} endpoint - API endpoint path (e.g., '/api/auth/login/')
 * @returns {string} - Full URL
 */
export function buildApiUrl(endpoint) {
  const baseUrl = API_BASE_URL.replace(/\/+$/, '');
  const endpointPath = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${baseUrl}${endpointPath}`;
}

