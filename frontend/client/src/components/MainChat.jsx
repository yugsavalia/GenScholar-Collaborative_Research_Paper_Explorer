import { useState, useEffect, useRef } from 'react';
import { storage } from '../utils/storage';
import { STORAGE_KEYS } from '../utils/constants';
import { getCurrentUser } from '../api/auth';
import { getMessages, sendMessage } from '../api/chat';
import Icon from './Icon';
import MessageBubble from './MessageBubble';
import MentionAutocomplete from './MentionAutocomplete';

const USE_BACKEND_API = import.meta.env.VITE_USE_BACKEND_API === 'true';

export default function MainChat({ workspaceId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [currentUsername, setCurrentUsername] = useState(null);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);
  const inputRef = useRef(null);
  const shouldAutoScroll = useRef(false);

  // Get current user's username
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const user = await getCurrentUser();
        if (user && user.username) {
          setCurrentUsername(user.username);
        }
      } catch (error) {
        console.warn('Failed to get current user:', error);
        setCurrentUsername('me');
      }
    };
    fetchUser();
  }, []);

  // Initial message load (only once)
  useEffect(() => {
    if (!workspaceId) return;

    const loadInitialMessages = async () => {
      if (USE_BACKEND_API) {
        try {
          setLoading(true);
          const apiMessages = await getMessages(workspaceId);
          const transformed = apiMessages.map(msg => ({
            id: msg.id,
            username: msg.user?.username || 'Unknown',
            content: msg.message,
            timestamp: msg.timestamp,
            author: msg.user?.username === currentUsername ? 'me' : 'other',
          }));
          setMessages(transformed);
        } catch (error) {
          console.error('Failed to fetch messages:', error);
          const saved = storage.get(STORAGE_KEYS.MAIN_CHAT(workspaceId)) || [];
          setMessages(saved);
        } finally {
          setLoading(false);
        }
      } else {
        const saved = storage.get(STORAGE_KEYS.MAIN_CHAT(workspaceId)) || [];
        const migrated = saved.map(msg => {
          if (msg.author && !msg.username) {
            return {
              ...msg,
              username: msg.author === 'me' ? (currentUsername || 'me') : (msg.username || 'Other'),
              timestamp: msg.createdAt || msg.timestamp || new Date().toISOString()
            };
          }
          if (!msg.timestamp && msg.createdAt) {
            return {
              ...msg,
              timestamp: msg.createdAt
            };
          }
          return msg;
        });
        setMessages(migrated);
      }
    };

    loadInitialMessages();
  }, [workspaceId, currentUsername]);

  // WebSocket connection for real-time messages
  useEffect(() => {
    if (!USE_BACKEND_API || !workspaceId) return;

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const wsUrl = `${protocol}://${window.location.host}/ws/chat/${workspaceId}/`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('Main chat WebSocket connected');
    };

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      const newMessage = {
        id: msg.id,
        username: msg.username || 'Unknown',
        content: msg.message,
        timestamp: msg.timestamp,
        author: msg.username === currentUsername ? 'me' : 'other',
      };
      setMessages(prev => {
        if (prev.some(m => m.id === newMessage.id)) {
          return prev;
        }
        return [...prev, newMessage];
      });
      shouldAutoScroll.current = true;
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket closed');
    };

    wsRef.current = ws;

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [workspaceId, currentUsername]);

  useEffect(() => {
    if (shouldAutoScroll.current && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
      shouldAutoScroll.current = false;
    }
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Get username if not already set
    let username = currentUsername;
    if (!username) {
      try {
        const user = await getCurrentUser();
        username = user?.username || 'me';
        setCurrentUsername(username);
      } catch (error) {
        username = 'me';
      }
    }

    const messageContent = input.trim();
    setInput('');

    if (USE_BACKEND_API) {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        try {
          wsRef.current.send(JSON.stringify({
            message: messageContent
          }));
          shouldAutoScroll.current = true;
        } catch (error) {
          console.error('Failed to send message via WebSocket:', error);
          setInput(messageContent);
          alert('Failed to send message. Please try again.');
        }
      } else {
        try {
          const savedMessage = await sendMessage(workspaceId, messageContent);
          const newMessage = {
            id: savedMessage.id,
            username: savedMessage.user?.username || username,
            content: savedMessage.message,
            timestamp: savedMessage.timestamp,
            author: savedMessage.user?.username === username ? 'me' : 'other',
          };
          setMessages(prev => [...prev, newMessage]);
          shouldAutoScroll.current = true;
        } catch (error) {
          console.error('Failed to send message:', error);
          setInput(messageContent);
          alert('Failed to send message. Please try again.');
        }
      }
    } else {
      // Use localStorage (fallback mode)
      const newMessage = {
        id: Date.now().toString(),
        author: 'me',
        username: username,
        content: messageContent,
        createdAt: new Date().toISOString(),
        timestamp: new Date().toISOString()
      };
      const updated = [...messages, newMessage];
      setMessages(updated);
      storage.set(STORAGE_KEYS.MAIN_CHAT(workspaceId), updated);
      shouldAutoScroll.current = true;
    }
  };

  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {loading && messages.length === 0 && (
          <div className="text-center py-4" style={{ color: 'var(--muted-text)' }}>
            Loading messages...
          </div>
        )}
        {!loading && messages.length === 0 && (
          <div className="text-center py-4" style={{ color: 'var(--muted-text)' }}>
            No messages yet. Start the conversation!
          </div>
        )}
        {messages.map(msg => {
          const isOwnMessage = msg.author === 'me' || (currentUsername && msg.username === currentUsername);
          return (
            <div
              key={msg.id}
              className={`flex ${isOwnMessage ? 'justify-end' : 'justify-start'}`}
              data-testid={`message-${msg.id}`}
            >
              <MessageBubble
                username={msg.username || (msg.author === 'me' ? (currentUsername || 'me') : 'Other')}
                content={msg.content}
                timestamp={msg.timestamp || msg.createdAt}
                isOwnMessage={isOwnMessage}
              />
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>
      
      <form onSubmit={handleSend} className="p-4" style={{ borderTop: '1px solid var(--border-color)' }}>
        <div className="flex gap-2 relative">
          <div className="flex-1 relative">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message..."
              className="w-full px-4 py-2 rounded-md focus:outline-none"
              style={{
                background: 'var(--input-bg)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-color)'
              }}
              onFocus={(e) => e.target.style.borderColor = 'var(--accent-color)'}
              onBlur={(e) => e.target.style.borderColor = 'var(--border-color)'}
              data-testid="input-main-chat"
            />
            <MentionAutocomplete
              inputValue={input}
              onInputChange={setInput}
              workspaceId={workspaceId}
              inputRef={inputRef}
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 rounded-md transition-colors"
            style={{ background: 'var(--accent-color)', color: '#fff' }}
            onMouseEnter={(e) => e.target.style.opacity = '0.9'}
            onMouseLeave={(e) => e.target.style.opacity = '1'}
            data-testid="button-send-main-chat"
          >
            <Icon name="send" size={18} />
          </button>
        </div>
      </form>
    </div>
  );
}
