/**
 * API Configuration
 * Base URL for the Django backend API
 */

// Get API base URL from environment or use default
let apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Remove trailing slash if present
apiBaseUrl = apiBaseUrl.replace(/\/+$/, '');

export const API_BASE_URL = apiBaseUrl;

