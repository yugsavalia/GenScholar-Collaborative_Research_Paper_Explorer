/**
 * WebSocket utility functions
 * Handles WebSocket URL construction, connection, reconnection, and polling fallback
 */

import { API_BASE_URL } from '../api/config.js';

/**
 * Build WebSocket URL from API base URL
 * @param {string} path - WebSocket path (e.g., '/ws/threads/workspace/1/pdf/2/')
 * @returns {string} WebSocket URL
 */
export function buildWebSocketUrl(path) {
  // Remove leading slash if present (we'll add it)
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  
  // Determine protocol (ws or wss)
  const wsProtocol = API_BASE_URL.startsWith('https') ? 'wss' : 'ws';
  
  // Extract host from API_BASE_URL (remove http:// or https://)
  const apiHost = API_BASE_URL.replace(/^https?:\/\//, '').replace(/\/$/, '');
  
  // Build WebSocket URL
  const wsUrl = `${wsProtocol}://${apiHost}${cleanPath}`;
  
  console.debug('[WS] Built WebSocket URL:', wsUrl);
  return wsUrl;
}

/**
 * Create a WebSocket connection with reconnection and polling fallback
 * @param {string} path - WebSocket path
 * @param {object} options - Connection options
 * @param {function} options.onMessage - Callback for messages
 * @param {function} options.onOpen - Callback when connected
 * @param {function} options.onError - Callback for errors
 * @param {function} options.onClose - Callback when closed
 * @param {function} options.onPoll - Polling fallback function (called when WS unavailable)
 * @param {number} options.maxReconnectAttempts - Maximum reconnection attempts (default: 5)
 * @param {number} options.reconnectDelay - Initial reconnect delay in ms (default: 1000)
 * @param {number} options.pollInterval - Polling interval in ms (default: 5000)
 * @returns {object} Connection object with {ws, close, reconnect} methods
 */
export function createWebSocketConnection(path, options = {}) {
  const {
    onMessage,
    onOpen,
    onError,
    onClose,
    onPoll,
    maxReconnectAttempts = 5,
    reconnectDelay = 1000,
    pollInterval = 5000
  } = options;

  let ws = null;
  let reconnectAttempts = 0;
  let reconnectTimer = null;
  let pollTimer = null;
  let isPolling = false;
  let isManuallyClosed = false;

  const wsUrl = buildWebSocketUrl(path);

  const connect = () => {
    if (isManuallyClosed) return;

    try {
      console.debug('[WS] Attempting to connect:', wsUrl);
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('[WS] Connected successfully');
        reconnectAttempts = 0;
        isPolling = false;
        if (pollTimer) {
          clearInterval(pollTimer);
          pollTimer = null;
        }
        if (onOpen) onOpen();
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.debug('[WS] Message received:', data);
          if (onMessage) onMessage(data);
        } catch (error) {
          console.error('[WS] Failed to parse message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('[WS] Connection error:', error);
        if (onError) onError(error);
      };

      ws.onclose = (event) => {
        console.log('[WS] Connection closed:', event.code, event.reason);
        ws = null;

        if (onClose) onClose(event);

        // Don't reconnect if manually closed
        if (isManuallyClosed) return;

        // Try to reconnect if not exceeded max attempts
        if (reconnectAttempts < maxReconnectAttempts) {
          const delay = reconnectDelay * Math.pow(2, reconnectAttempts); // Exponential backoff
          console.debug(`[WS] Reconnecting in ${delay}ms (attempt ${reconnectAttempts + 1}/${maxReconnectAttempts})`);
          reconnectTimer = setTimeout(() => {
            reconnectAttempts++;
            connect();
          }, delay);
        } else {
          // Fall back to polling
          console.warn('[WS] Max reconnection attempts reached. Falling back to polling.');
          startPolling();
        }
      };
    } catch (error) {
      console.error('[WS] Failed to create WebSocket:', error);
      if (onError) onError(error);
      // Fall back to polling immediately
      startPolling();
    }
  };

  const startPolling = () => {
    if (isPolling || !onPoll) return;
    
    isPolling = true;
    console.log('[WS] Starting polling fallback');
    
    // Poll immediately, then at intervals
    onPoll();
    pollTimer = setInterval(() => {
      if (!isManuallyClosed && onPoll) {
        onPoll();
      }
    }, pollInterval);
  };

  const close = () => {
    isManuallyClosed = true;
    
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
    
    if (ws) {
      ws.close();
      ws = null;
    }
  };

  const reconnect = () => {
    reconnectAttempts = 0;
    isManuallyClosed = false;
    if (ws) {
      ws.close();
    } else {
      connect();
    }
  };

  // Start connection
  connect();

  return {
    ws,
    close,
    reconnect,
    isConnected: () => ws && ws.readyState === WebSocket.OPEN,
    isPolling: () => isPolling
  };
}

