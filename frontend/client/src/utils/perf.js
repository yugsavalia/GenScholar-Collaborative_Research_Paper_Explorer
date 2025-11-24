/**
 * Performance utilities for timing and debouncing
 */

/**
 * Create a debounced function
 * @param {function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {function} Debounced function
 */
export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Performance timing utility
 */
export class PerformanceTimer {
  constructor(label) {
    this.label = label;
    this.startTime = performance.now();
  }

  mark(event) {
    const elapsed = performance.now() - this.startTime;
    console.debug(`[PERF:${this.label}] ${event}: ${elapsed.toFixed(2)}ms`);
    return elapsed;
  }

  end() {
    const elapsed = performance.now() - this.startTime;
    console.debug(`[PERF:${this.label}] Total: ${elapsed.toFixed(2)}ms`);
    return elapsed;
  }
}

/**
 * Create a performance timer
 * @param {string} label - Label for the timer
 * @returns {PerformanceTimer}
 */
export function createTimer(label) {
  return new PerformanceTimer(label);
}

