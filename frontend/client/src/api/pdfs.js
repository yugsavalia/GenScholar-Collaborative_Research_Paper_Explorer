/**
 * PDF API Functions
 * Functions for PDF management with the Django backend
 */

import { API_BASE_URL } from './config.js';

/**
 * Get list of PDFs for a workspace
 * @param {string|number} workspaceId - Workspace ID
 * @returns {Promise<Array>} - Array of PDF objects
 */
export async function getPdfs(workspaceId) {
  const response = await fetch(`${API_BASE_URL}/api/pdfs/?workspace=${workspaceId}`, {
    method: 'GET',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch PDFs: ${response.statusText}`);
  }

  const data = await response.json();
  // DRF ViewSet returns {results: [...]} format
  return data.results || [];
}

/**
 * Upload a PDF to a workspace
 * @param {string|number} workspaceId - Workspace ID
 * @param {File} file - PDF file to upload
 * @param {string} title - PDF title
 * @returns {Promise<object>} - Uploaded PDF object
 */
export async function uploadPdf(workspaceId, file, title) {
  const { getCsrfToken } = await import('../utils/csrf.js');
  
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', title);
  formData.append('workspace', workspaceId);

  // Get CSRF token
  const csrfToken = await getCsrfToken();

  const response = await fetch(`${API_BASE_URL}/api/pdfs/`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'X-CSRFToken': csrfToken,
    },
    body: formData,
  });

  if (!response.ok) {
    let errorMessage = `Failed to upload PDF: ${response.statusText}`;
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorData.error || errorMessage;
      
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

  return await response.json();
}

/**
 * Get PDF file bytes and create a blob URL
 * @param {string|number} pdfId - PDF ID
 * @returns {Promise<string>} - Blob URL for the PDF
 */
export async function getPdfUrl(pdfId) {
  const response = await fetch(`${API_BASE_URL}/api/pdfs/${pdfId}/download/`, {
    method: 'GET',
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch PDF: ${response.statusText}`);
  }

  const blob = await response.blob();
  return URL.createObjectURL(blob);
}

/**
 * Delete a PDF
 * @param {string|number} pdfId - PDF ID
 * @returns {Promise<void>}
 */
export async function deletePdf(pdfId) {
  const { getCsrfToken } = await import('../utils/csrf.js');
  
  // Get CSRF token
  const csrfToken = await getCsrfToken();

  const response = await fetch(`${API_BASE_URL}/api/pdfs/${pdfId}/`, {
    method: 'DELETE',
    credentials: 'include',
    headers: {
      'X-CSRFToken': csrfToken,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    let errorMessage = `Failed to delete PDF: ${response.statusText}`;
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorData.error || errorMessage;
      
      // Handle CSRF errors specifically
      if (response.status === 403 && (errorData.detail?.includes('CSRF') || errorData.message?.includes('CSRF'))) {
        errorMessage = 'CSRF verification failed. Please refresh the page and try again.';
      }
    } catch (e) {
      if (response.status === 403) {
        errorMessage = 'CSRF verification failed. Please refresh the page and try again.';
      }
    }
    throw new Error(errorMessage);
  }
}

