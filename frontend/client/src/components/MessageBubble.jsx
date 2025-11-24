import { formatDateTime } from '../utils/dateFormat';
import { renderMessageWithMentions } from '../utils/mentions.jsx';

/**
 * MessageBubble - Reusable component for displaying chat messages
 * Shows username, content, and timestamp in a consistent format
 * 
 * @param {object} props
 * @param {string} props.username - Username of the message sender
 * @param {string} props.content - Message content/text
 * @param {string|Date} props.timestamp - Timestamp (ISO string or Date object)
 * @param {boolean} props.isOwnMessage - Whether this is the current user's message (affects styling)
 */
export default function MessageBubble({ username, content, timestamp, isOwnMessage = false }) {
  const renderedContent = renderMessageWithMentions(content);
  
  return (
    <div
      className="max-w-[80%] px-4 py-2 rounded-lg"
      style={isOwnMessage
        ? { background: 'var(--accent-color)', color: '#fff' }
        : { background: 'var(--hover-bg)', color: 'var(--text-color)' }
      }
    >
      {/* Username at the top */}
      {username && (
        <p className={`text-xs font-semibold mb-1 ${
          isOwnMessage ? 'opacity-90' : 'opacity-75'
        }`}>
          {username}
        </p>
      )}
      
      {/* Message content with highlighted mentions */}
      <p className="text-sm">{renderedContent}</p>
      
      {/* Timestamp at the bottom */}
      {timestamp && (
        <p className={`text-xs mt-1 ${
          isOwnMessage ? 'opacity-70' : 'opacity-60'
        }`}>
          {formatDateTime(timestamp)}
        </p>
      )}
    </div>
  );
}

