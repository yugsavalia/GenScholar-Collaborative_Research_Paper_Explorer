/**
 * Date formatting utilities
 * Provides consistent date/time formatting across the application
 */

/**
 * Format a date/timestamp to DD/MM/YYYY, HH:mm:ss format
 * @param {string|Date} dateInput - ISO string, timestamp string, or Date object
 * @returns {string} Formatted date string (e.g., "15/01/2024, 10:30:45")
 */
export function formatDateTime(dateInput) {
  if (!dateInput) return '';
  
  const date = typeof dateInput === 'string' ? new Date(dateInput) : dateInput;
  
  if (isNaN(date.getTime())) {
    console.warn('Invalid date:', dateInput);
    return '';
  }
  
  // Format: DD/MM/YYYY, HH:mm:ss
  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const year = date.getFullYear();
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  
  return `${day}/${month}/${year}, ${hours}:${minutes}:${seconds}`;
}

/**
 * Format a date/timestamp to a shorter format (DD/MM/YYYY, HH:mm)
 * @param {string|Date} dateInput - ISO string, timestamp string, or Date object
 * @returns {string} Formatted date string (e.g., "15/01/2024, 10:30")
 */
export function formatDateTimeShort(dateInput) {
  if (!dateInput) return '';
  
  const date = typeof dateInput === 'string' ? new Date(dateInput) : dateInput;
  
  if (isNaN(date.getTime())) {
    console.warn('Invalid date:', dateInput);
    return '';
  }
  
  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const year = date.getFullYear();
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  
  return `${day}/${month}/${year}, ${hours}:${minutes}`;
}

