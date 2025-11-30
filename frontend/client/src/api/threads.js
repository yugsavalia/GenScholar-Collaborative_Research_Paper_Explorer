/**
 * Threads API Functions
 * Functions for managing threaded discussions on PDF text selections
 */

import { buildApiUrl } from './config.js';
import { getCsrfToken } from '../utils/csrf.js';

/**
 * Get all threads for a PDF
 * @param {string|number} workspaceId - Workspace ID
 * @param {string|number} pdfId - PDF ID
 * @returns {Promise<Array>} - Array of thread objects
 */
export async function getThreads(workspaceId, pdfId) {
  const response = await fetch(
    `${buildApiUrl('/api/threads/')}?workspace_id=${workspaceId}&pdf_id=${pdfId}`,
    {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch threads: ${response.statusText}`);
  }

  const data = await response.json();
  return data.results || data || [];
}

/**
 * Create a new thread from a text selection
 * @param {string|number} workspaceId - Workspace ID
 * @param {string|number} pdfId - PDF ID
 * @param {object} threadData - Thread data {page_number, selection_text, anchor_rect, anchor_side}
 * @returns {Promise<object>} - Created thread object
 */
export async function createThread(workspaceId, pdfId, threadData) {
  const csrfToken = await getCsrfToken();

  const response = await fetch(buildApiUrl('/api/threads/'), {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify({
      workspace_id: workspaceId,
      pdf_id: pdfId,
      pdf: pdfId,
      ...threadData,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || errorData.message || `Failed to create thread: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Get a thread with all its messages
 * @param {string|number} threadId - Thread ID
 * @returns {Promise<object>} - Thread object with messages
 */
export async function getThread(threadId) {
  const response = await fetch(buildApiUrl(`/api/threads/${threadId}/`), {
    method: 'GET',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch thread: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Add a message to a thread
 * @param {string|number} threadId - Thread ID
 * @param {string} content - Message content
 * @returns {Promise<object>} - Created message object
 */
export async function addMessage(threadId, content) {
  const csrfToken = await getCsrfToken();

  const response = await fetch(buildApiUrl(`/api/threads/${threadId}/messages/`), {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify({ content }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || errorData.message || `Failed to add message: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Delete a thread
 * @param {string|number} threadId - Thread ID
 * @returns {Promise<void>}
 */
export async function deleteThread(threadId) {
  const csrfToken = await getCsrfToken();

  const response = await fetch(buildApiUrl(`/api/threads/${threadId}/`), {
    method: 'DELETE',
    credentials: 'include',
    headers: {
      'X-CSRFToken': csrfToken,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to delete thread: ${response.statusText}`);
  }
}

