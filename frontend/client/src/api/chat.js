/**
 * Chat Messages API Functions
 * Functions for managing chat messages with the Django backend
 */

import { apiGet, apiPost } from './client.js';

/**
 * Get messages for a workspace
 * @param {string|number} workspaceId - Workspace ID
 * @returns {Promise<Array>} - Array of message objects [{id, workspace, user: {id, username}, message, timestamp}, ...]
 */
export async function getMessages(workspaceId) {
  try {
    const response = await apiGet(`/api/messages/?workspace_id=${workspaceId}`);
    console.log('[Chat API] getMessages raw response:', response);
    
    // DRF ViewSet can return:
    // 1. Array directly if no pagination: [...]
    // 2. Paginated format: {count: N, next: null, previous: null, results: [...]}
    // 3. Custom format: {success: true, data: [...]}
    
    if (Array.isArray(response)) {
      console.log('[Chat API] Response is array, returning directly');
      return response;
    }
    
    if (response.results && Array.isArray(response.results)) {
      console.log('[Chat API] Response has results array, returning results');
      return response.results;
    }
    
    if (response.data && Array.isArray(response.data)) {
      console.log('[Chat API] Response has data array, returning data');
      return response.data;
    }
    
    console.warn('[Chat API] Unexpected response format:', response);
    return [];
  } catch (error) {
    console.error('[Chat API] Error fetching messages:', error);
    throw error;
  }
}

/**
 * Send a message to a workspace
 * @param {string|number} workspaceId - Workspace ID
 * @param {string} message - Message content
 * @returns {Promise<object>} - Created message object
 */
export async function sendMessage(workspaceId, message) {
  const response = await apiPost('/api/messages/', {
    workspace: workspaceId,
    message: message.trim(),
  });
  // DRF ViewSet returns the created object directly
  return response;
}

