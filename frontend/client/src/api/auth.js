/**
 * Auth API Functions
 * Functions for authentication with the Django backend
 */

import { apiGet, apiPost } from './client.js';

/**
 * Login user
 * @param {string} identifier - Username OR email
 * @param {string} password - Password
 * @returns {Promise<object>} - User data {id, username}
 */
export async function login(identifier, password) {
  const response = await apiPost('/api/auth/login/', {
    identifier,
    password,
  });
  
  // Extract user data from response
  // Response format: {success: true, data: {user: {id, username}}}
  return response.data.user;
}

/**
 * Request email verification before signup (sends OTP)
 * @param {string} email - Email address to verify
 * @returns {Promise<object>} - Success message
 */
export async function requestEmailVerification(email) {
  const response = await apiPost('/api/auth/request-email-verification/', {
    email,
  });
  
  // Response format: {success: true, data: {message: "..."}}
  return response.data;
}

/**
 * Verify OTP code
 * @param {string} email - Email address
 * @param {string} otp - 6-digit OTP code
 * @returns {Promise<object>} - {email, message} for use in signup
 */
export async function verifyOTP(email, otp) {
  const response = await apiPost('/api/auth/verify-otp/', {
    email,
    otp,
  });
  
  // Response format: {success: true, data: {email, message}}
  return response.data;
}

/**
 * Verify email token (called after user clicks link in email) - kept for backward compatibility
 * @param {string} token - Verification token from email link
 * @returns {Promise<object>} - {email, token} for use in signup
 */
export async function verifyEmailToken(token) {
  const response = await apiGet(`/api/auth/verify-email/?token=${encodeURIComponent(token)}`);
  
  // Response format: {success: true, data: {email, token, message}}
  return response.data;
}

/**
 * Signup user (requires verified OTP)
 * @param {string} username - Username (must be unique)
 * @param {string} email - Email address (must match verified email)
 * @param {string} password - Password
 * @param {string} confirm_password - Password confirmation
 * @returns {Promise<object>} - User data {id, username}
 */
export async function signup(username, email, password, confirm_password) {
  const response = await apiPost('/api/auth/signup/', {
    username,
    email,
    password,
    confirm_password,
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

