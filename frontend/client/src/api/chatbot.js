/**
 * Chatbot API Functions
 * Functions for interacting with the AI chatbot
 */

import { API_BASE_URL } from './config.js';
import { getCsrfToken } from '../utils/csrf.js';

/**
 * Ask a question to the AI chatbot
 * @param {string|number} workspaceId - Workspace ID
 * @param {string} question - User's question
 * @returns {Promise<object>} - Response with user_question and ai_answer
 */
export async function askChatbot(workspaceId, question) {
  const csrfToken = await getCsrfToken();
  
  // Create AbortController for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 90000); // 90 second timeout
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/chatbot/ask/`, {
      method: 'POST',
      credentials: 'include',
      signal: controller.signal, // Add abort signal
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({
        question: question,
        workspace_id: workspaceId,
      }),
    });
    
    clearTimeout(timeoutId); // Clear timeout if request completes

    if (!response.ok) {
      let errorMessage = `Failed to get chatbot response: ${response.statusText}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.error || errorData.detail || errorData.message || errorMessage;
        
        // Handle CSRF errors specifically
        if (response.status === 403 && (errorData.detail?.includes('CSRF') || errorData.message?.includes('CSRF'))) {
          errorMessage = 'CSRF verification failed. Please refresh the page and try again.';
        }
      } catch (e) {
        // If response is not JSON, use status text
        if (response.status === 403) {
          errorMessage = 'CSRF verification failed. Please refresh the page and try again.';
        }
      }
      throw new Error(errorMessage);
    }

    const data = await response.json();
    
    // Handle different response formats
    if (data.status === 'ok') {
      return {
        user_question: data.user_question,
        ai_answer: data.ai_answer
      };
    }
    
    // If there's an error field, throw it
    if (data.error) {
      throw new Error(data.error);
    }
    
    return data;
  } catch (error) {
    clearTimeout(timeoutId); // Clear timeout on error
    if (error.name === 'AbortError') {
      throw new Error('Request timed out. The AI is taking too long to respond. Please try again with a simpler question.');
    }
    throw error;
  }
}

