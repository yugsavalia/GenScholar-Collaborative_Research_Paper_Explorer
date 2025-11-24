import React from 'react';

/**
 * Utility functions for handling @mentions in messages
 */

/**
 * Parse message text to find all @mentions
 * @param {string} text - Message text
 * @returns {Array} - Array of mention objects {username, start, end}
 */
export function parseMentions(text) {
  const mentions = [];
  const regex = /@([A-Za-z0-9_]+)/g;
  let match;
  
  while ((match = regex.exec(text)) !== null) {
    mentions.push({
      username: match[1],
      start: match.index,
      end: match.index + match[0].length,
      fullMatch: match[0]
    });
  }
  
  return mentions;
}

/**
 * Render message with highlighted mentions
 * @param {string} text - Message text
 * @returns {Array|string} - Array of React elements (text and spans) or plain string
 */
export function renderMessageWithMentions(text) {
  const mentions = parseMentions(text);
  if (mentions.length === 0) {
    return text;
  }
  
  const parts = [];
  let lastIndex = 0;
  
  mentions.forEach((mention, index) => {
    if (mention.start > lastIndex) {
      parts.push(text.substring(lastIndex, mention.start));
    }
    
    parts.push(
      <span key={`mention-${index}`} style={{ color: 'var(--accent-color)', fontWeight: 500 }}>
        {mention.fullMatch}
      </span>
    );
    
    lastIndex = mention.end;
  });
  
  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }
  
  return parts;
}

