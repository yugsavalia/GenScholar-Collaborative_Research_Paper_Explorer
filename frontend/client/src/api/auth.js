/**
 * Auth API Functions
 * Functions for authentication with the Django backend
 */

import { apiGet, apiPost } from './client.js';

/**
 * Login user
 * @param {string} username - Username
 * @param {string} password - Password
 * @returns {Promise<object>} - User data {id, username}
 */
export async function login(username, password) {
  const response = await apiPost('/api/auth/login/', {
    username,
    password,
  });
  
  // Extract user data from response
  // Response format: {success: true, data: {user: {id, username}}}
  return response.data.user;
}

/**
 * Signup user
 * @param {string} username - Username
 * @param {string} password1 - Password
 * @param {string} password2 - Password confirmation
 * @returns {Promise<object>} - User data {id, username}
 */
export async function signup(username, password1, password2) {
  const response = await apiPost('/api/auth/signup/', {
    username,
    password1,
    password2,
  });
  
  // Extract user data from response
  // Response format: {success: true, data: {user: {id, username}}}
  return response.data.user;
}

/**
 * Logout user
 * @returns {Promise<object>} - Logout response
 */
export async function logout() {
  const response = await apiPost('/api/auth/logout/', {});
  
  // Response format: {success: true, data: {message: "Logged out successfully"}}
  return response.data;
}

/**
 * Get current user
 * @returns {Promise<object|null>} - User data {id, username} or null if not authenticated
 */
export async function getCurrentUser() {
  try {
    const response = await apiGet('/api/auth/user/');
    
    // Extract user data from response
    // Response format: {success: true, data: {user: {id, username}}}
    return response.data.user;
  } catch (error) {
    // If 401 (not authenticated), return null
    if (error.status === 401) {
      return null;
    }
    
    // Otherwise, rethrow the error
    throw error;
  }
}

