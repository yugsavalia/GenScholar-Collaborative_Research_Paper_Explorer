/**
 * Workspace API Functions
 * Functions for workspace management with the Django backend
 */

import { apiGet, apiPost, apiPatch } from './client.js';

/**
 * Get list of workspaces
 * @param {string} searchQuery - Optional search query to filter workspaces by name
 * @returns {Promise<Array>} - Array of workspace objects [{id, name, created_at, created_by}, ...]
 */
export async function getWorkspaces(searchQuery = '') {
  // Build endpoint with query parameter if provided
  let endpoint = '/api/workspaces/';
  if (searchQuery) {
    endpoint += `?q=${encodeURIComponent(searchQuery)}`;
  }
  
  const response = await apiGet(endpoint);
  
  // Extract workspaces array from response
  // Response format: {success: true, data: {workspaces: [...]}}
  return response.data.workspaces;
}

/**
 * Create a new workspace
 * @param {string} name - Workspace name
 * @returns {Promise<object>} - Workspace object {id, name, created_at, created_by}
 */
export async function createWorkspace(name) {
  const response = await apiPost('/api/workspaces/', {
    name: name.trim(),
  });
  
  // Extract workspace object from response
  // Response format: {success: true, data: {workspace: {id, name, created_at, created_by}}}
  return response.data.workspace;
}

/**
 * Get workspace members
 * @param {string|number} workspaceId - Workspace ID
 * @returns {Promise<Array>} - Array of member objects [{id, user: {id, username, email}, role, is_creator, joined_at}, ...]
 */
export async function getWorkspaceMembers(workspaceId) {
  const response = await apiGet(`/api/workspaces/${workspaceId}/members/`);
  // Response format: {success: true, data: {members: [...]}}
  return response.data.members;
}

/**
 * Invite a user to workspace
 * @param {string|number} workspaceId - Workspace ID
 * @param {number} userId - User ID to invite
 * @param {string} role - Role to assign ('RESEARCHER' or 'REVIEWER')
 * @returns {Promise<object>} - Invitation object
 */
export async function inviteUserToWorkspace(workspaceId, userId, role) {
  const response = await apiPost(`/api/workspaces/${workspaceId}/invite/`, {
    user_id: userId,
    role: role
  });
  // Response format: {success: true, data: {invitation: {...}}}
  return response.data.invitation;
}

/**
 * Update member role
 * @param {string|number} workspaceId - Workspace ID
 * @param {number} memberId - Member ID
 * @param {string} role - New role ('RESEARCHER' or 'REVIEWER')
 * @returns {Promise<object>} - Updated member object
 */
export async function updateMemberRole(workspaceId, memberId, role) {
  const response = await apiPatch(`/api/workspaces/${workspaceId}/members/${memberId}/`, {
    role: role
  });
  // Response format: {success: true, data: {member: {...}}}
  return response.data.member;
}

/**
 * Search users
 * @param {string} query - Search query (username or email)
 * @returns {Promise<Array>} - Array of user objects [{id, username, email}, ...]
 */
export async function searchUsers(query) {
  const endpoint = `/api/users/?q=${encodeURIComponent(query)}`;
  const response = await apiGet(endpoint);
  // DRF ViewSet returns {results: [...]} format
  return response.results || [];
}

/**
 * Get pending invitations for current user
 * @returns {Promise<Array>} - Array of invitation objects
 */
export async function getPendingInvitations() {
  const response = await apiGet('/api/invitations/');
  // Response format: {success: true, data: {invitations: [...]}}
  return response.data.invitations;
}

/**
 * Accept a workspace invitation
 * @param {number} invitationId - Invitation ID
 * @returns {Promise<object>} - Member object
 */
export async function acceptInvitation(invitationId) {
  const response = await apiPost(`/api/invitations/${invitationId}/accept/`, {});
  // Response format: {success: true, data: {member: {...}}}
  return response.data.member;
}

/**
 * Decline a workspace invitation
 * @param {number} invitationId - Invitation ID
 * @returns {Promise<object>} - Success message
 */
export async function declineInvitation(invitationId) {
  const response = await apiPost(`/api/invitations/${invitationId}/decline/`, {});
  // Response format: {success: true, data: {message: "..."}}
  return response.data;
}

/**
 * Get notifications for current user
 * @returns {Promise<object>} - Object with notifications array and unread_count
 */
export async function getNotifications() {
  const response = await apiGet('/api/notifications/');
  // Response format: {success: true, data: {notifications: [...], unread_count: number}}
  return response.data;
}

/**
 * Mark a notification as read
 * @param {number} notificationId - Notification ID
 * @returns {Promise<object>} - Success message
 */
export async function markNotificationRead(notificationId) {
  const response = await apiPatch(`/api/notifications/${notificationId}/`, {});
  // Response format: {success: true, data: {message: "..."}}
  return response.data;
}

