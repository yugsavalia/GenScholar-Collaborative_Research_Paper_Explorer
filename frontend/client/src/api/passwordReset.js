/**
 * Password Reset API Functions
 * Functions for password reset functionality
 */

import { apiPost } from './client.js';

/**
 * Request a password reset email
 * @param {string} email - User's email address
 * @returns {Promise<object>} - Response with success message
 */
export async function requestPasswordReset(email) {
  const response = await apiPost('/api/auth/password-reset/', {
    email,
  });
  
  return response;
}

/**
 * Confirm password reset with new password
 * @param {string} uid - Base64 encoded user ID
 * @param {string} token - Password reset token
 * @param {string} newPassword - New password
 * @param {string} reNewPassword - Confirm new password
 * @returns {Promise<object>} - Response with success message
 */
export async function confirmPasswordReset(uid, token, newPassword, reNewPassword) {
  const response = await apiPost('/api/auth/password-reset/confirm/', {
    uid,
    token,
    new_password: newPassword,
    re_new_password: reNewPassword,
  });
  
  return response;
}

