/**
 * Profile API Functions
 * Functions for fetching user profile information
 */

import { apiGet } from './client.js';

/**
 * Get current user profile with stats
 * @returns {Promise<object>} - Profile data with user info and stats
 */
export async function getProfile() {
  const response = await apiGet('/api/profile/me/');
  
  // Extract profile data from response
  // Response format: {success: true, data: {profile: {...}}}
  return response.data.profile;
}

