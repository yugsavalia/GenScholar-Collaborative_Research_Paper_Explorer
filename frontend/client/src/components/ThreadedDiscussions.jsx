import { useState, useEffect, useRef } from 'react';
import { getThreads, getThread, addMessage } from '../api/threads';
import { createWebSocketConnection } from '../utils/ws';
import Icon from './Icon';
import MentionAutocomplete from './MentionAutocomplete';
import { renderMessageWithMentions } from '../utils/mentions.jsx';

/**
 * ThreadedDiscussions - Panel showing all threads for a PDF with message history
 * @param {object} props
 * @param {string|number} props.workspaceId - Workspace ID
 * @param {string|number} props.pdfId - PDF ID
 * @param {number} props.selectedThreadId - Currently selected thread ID (optional)
 * @param {function} props.onThreadSelect - Callback when a thread is selected
 */
export default function ThreadedDiscussions({ workspaceId, pdfId, selectedThreadId, onThreadSelect }) {
  const [threads, setThreads] = useState([]);
  const [selectedThread, setSelectedThread] = useState(null);
  const [loading, setLoading] = useState(true);
  const [messageInput, setMessageInput] = useState('');
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);
  const messageInputRef = useRef(null);

  // Load threads when PDF changes
  useEffect(() => {
    if (!workspaceId || !pdfId) {
      setThreads([]);
      setSelectedThread(null);
      setLoading(false);
      return;
    }

    const loadThreads = async () => {
      setLoading(true);
      try {
        const threadList = await getThreads(workspaceId, pdfId);
        setThreads(threadList);
        
        // If a thread is pre-selected, load it
        if (selectedThreadId) {
          const thread = threadList.find(t => t.id === selectedThreadId);
          if (thread) {
            await loadThreadDetails(thread.id);
          }
        }
      } catch (error) {
        console.error('Failed to load threads:', error);
      } finally {
        setLoading(false);
      }
    };

    loadThreads();
  }, [workspaceId, pdfId, selectedThreadId]);

  // Connect to WebSocket for real-time updates with polling fallback
  useEffect(() => {
    if (!workspaceId || !pdfId) return;

    const wsPath = `/ws/threads/workspace/${workspaceId}/pdf/${pdfId}/`;
    
    // Polling fallback function
    const pollThreads = async () => {
      try {
        const threadList = await getThreads(workspaceId, pdfId);
        setThreads(threadList);
        // If a thread is selected, refresh its messages
        if (selectedThread) {
          const updatedThread = await getThread(selectedThread.id);
          setSelectedThread(updatedThread);
        }
      } catch (error) {
        console.error('[ThreadedDiscussions] Polling error:', error);
      }
    };

    // Create WebSocket connection with polling fallback
    const wsConnection = createWebSocketConnection(wsPath, {
      onMessage: (data) => {
        if (data.type === 'thread.created') {
          // Add new thread to list (avoid duplicates)
          setThreads(prev => {
            if (prev.some(t => t.id === data.thread.id)) return prev;
            return [data.thread, ...prev];
          });
        } else if (data.type === 'message.created') {
          // Add message to selected thread if it matches
          if (selectedThread && selectedThread.id === data.thread_id) {
            setSelectedThread(prev => {
              // Avoid duplicates
              if (prev.messages?.some(msg => msg.id === data.message.id)) return prev;
              return {
                ...prev,
                messages: [...(prev.messages || []), data.message],
              };
            });
          }
          // Update thread's last_activity_at in list
          setThreads(prev => prev.map(t => 
            t.id === data.thread_id 
              ? { ...t, last_activity_at: data.message.created_at, message_count: (t.message_count || 0) + 1 }
              : t
          ));
        }
      },
      onOpen: () => {
        console.log('[ThreadedDiscussions] WebSocket connected');
      },
      onError: (error) => {
        console.warn('[ThreadedDiscussions] WebSocket error:', error);
      },
      onClose: (event) => {
        console.log('[ThreadedDiscussions] WebSocket closed:', event.code, event.reason);
      },
      onPoll: pollThreads,
      maxReconnectAttempts: 3,
      reconnectDelay: 1000,
      pollInterval: 5000,
    });

    wsRef.current = wsConnection;

    return () => {
      if (wsConnection && wsConnection.close) {
        wsConnection.close();
      }
    };
  }, [workspaceId, pdfId, selectedThread]);

  const shouldAutoScroll = useRef(false);

  useEffect(() => {
    if (shouldAutoScroll.current && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
      shouldAutoScroll.current = false;
    }
  }, [selectedThread?.messages]);

  const loadThreadDetails = async (threadId) => {
    try {
      const thread = await getThread(threadId);
      setSelectedThread(thread);
      if (onThreadSelect) {
        onThreadSelect(thread);
      }
    } catch (error) {
      console.error('Failed to load thread details:', error);
    }
  };

  const handleThreadClick = (thread) => {
    loadThreadDetails(thread.id);
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!messageInput.trim() || !selectedThread || sending) return;

    const content = messageInput.trim();
    setMessageInput('');
    setSending(true);

    try {
      const newMessage = await addMessage(selectedThread.id, content);
      
      // Update thread with new message
      setSelectedThread(prev => ({
        ...prev,
        messages: [...(prev.messages || []), newMessage],
      }));
      
      // Update thread in list
      setThreads(prev => prev.map(t => 
        t.id === selectedThread.id 
          ? { ...t, last_activity_at: newMessage.created_at, message_count: (t.message_count || 0) + 1 }
          : t
      ));
      
      shouldAutoScroll.current = true;
    } catch (error) {
      console.error('Failed to send message:', error);
      setMessageInput(content); // Restore input on error
      alert('Failed to send message: ' + (error.message || 'Unknown error'));
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-[#BDBDBD]">Loading threads...</p>
      </div>
    );
  }

  if (!selectedThread) {
    return (
      <div className="h-full flex flex-col min-h-0">
        <div className="p-4" style={{ borderBottom: '1px solid var(--border-color)' }}>
          <h3 className="text-lg font-semibold" style={{ color: 'var(--text-color)' }}>Threaded Discussions</h3>
          <p className="text-sm mt-1" style={{ color: 'var(--muted-text)' }}>
            {threads.length} {threads.length === 1 ? 'thread' : 'threads'}
          </p>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {threads.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <p className="text-center" style={{ color: 'var(--muted-text)' }}>
                No threads yet. Select text in the PDF and click "Start chat" to create a thread.
              </p>
            </div>
          ) : (
            threads.map(thread => (
              <button
                key={thread.id}
                onClick={() => handleThreadClick(thread)}
                className={`w-full text-left p-3 rounded-md transition-colors ${
                  selectedThreadId === thread.id ? 'active' : ''
                }`}
                style={selectedThreadId === thread.id
                  ? { background: 'var(--accent-color)', color: '#fff' }
                  : { background: 'var(--hover-bg)', color: 'var(--text-color)' }
                }
                onMouseEnter={(e) => {
                  if (selectedThreadId !== thread.id) e.target.style.background = 'var(--border-color)';
                }}
                onMouseLeave={(e) => {
                  if (selectedThreadId !== thread.id) e.target.style.background = 'var(--hover-bg)';
                }}
                data-testid={`thread-item-${thread.id}`}
              >
                <div className="flex items-start gap-2">
                  <Icon name="message-circle" size={16} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      Page {thread.page_number}
                    </p>
                    <p className="text-xs opacity-75 mt-1 line-clamp-2">
                      "{thread.selection_text}"
                    </p>
                    <p className="text-xs opacity-60 mt-1">
                      {thread.message_count || 0} {thread.message_count === 1 ? 'message' : 'messages'}
                    </p>
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      </div>
    );
  }

  // Show thread detail view
  return (
    <div className="h-full flex flex-col min-h-0">
      {/* Header with back button */}
      <div className="p-4" style={{ borderBottom: '1px solid var(--border-color)' }}>
        <button
          onClick={() => setSelectedThread(null)}
          className="mb-2 text-sm flex items-center gap-1 transition-colors"
          style={{ color: 'var(--accent-color)' }}
          onMouseEnter={(e) => e.target.style.opacity = '0.8'}
          onMouseLeave={(e) => e.target.style.opacity = '1'}
          data-testid="button-back-to-threads"
        >
          <Icon name="arrow-left" size={16} />
          Back to threads
        </button>
        <p className="text-xs mb-1" style={{ color: 'var(--muted-text)' }}>Selected text:</p>
        <p className="text-sm italic" style={{ color: 'var(--text-color)' }}>"{selectedThread.selection_text}"</p>
        <p className="text-xs mt-1" style={{ color: 'var(--muted-text)' }}>Page {selectedThread.page_number}</p>
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {selectedThread.messages && selectedThread.messages.length > 0 ? (
          selectedThread.messages.map(msg => (
            <div
              key={msg.id}
              className={`flex ${msg.sender?.id === selectedThread.created_by?.id ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className="max-w-[80%] px-4 py-2 rounded-lg"
                style={msg.sender?.id === selectedThread.created_by?.id
                  ? { background: 'var(--accent-color)', color: '#fff' }
                  : { background: 'var(--hover-bg)', color: 'var(--text-color)' }
                }
              >
                {msg.sender && (
                  <p className="text-xs opacity-75 mb-1">{msg.sender.username}</p>
                )}
                <p className="text-sm">{renderMessageWithMentions(msg.content)}</p>
                <p className="text-xs opacity-60 mt-1">
                  {new Date(msg.created_at).toLocaleString()}
                </p>
              </div>
            </div>
          ))
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-center" style={{ color: 'var(--muted-text)' }}>No messages yet. Start the conversation!</p>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      {/* Message input */}
      <form onSubmit={handleSendMessage} className="p-4" style={{ borderTop: '1px solid var(--border-color)' }}>
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <input
              ref={messageInputRef}
              type="text"
              value={messageInput}
              onChange={(e) => setMessageInput(e.target.value)}
              placeholder="Type a message..."
              className="w-full px-4 py-2 rounded-md focus:outline-none"
              style={{
                background: 'var(--input-bg)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-color)'
              }}
              onFocus={(e) => e.target.style.borderColor = 'var(--accent-color)'}
              onBlur={(e) => e.target.style.borderColor = 'var(--border-color)'}
              data-testid="input-thread-message"
              disabled={sending}
            />
            {workspaceId && (
              <MentionAutocomplete
                inputValue={messageInput}
                onInputChange={setMessageInput}
                workspaceId={workspaceId}
                inputRef={messageInputRef}
              />
            )}
          </div>
          <button
            type="submit"
            className="px-4 py-2 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ background: 'var(--accent-color)', color: '#fff' }}
            onMouseEnter={(e) => !sending && (e.target.style.opacity = '0.9')}
            onMouseLeave={(e) => e.target.style.opacity = '1'}
            data-testid="button-send-thread-message"
            disabled={sending || !messageInput.trim()}
          >
            <Icon name="send" size={18} />
          </button>
        </div>
      </form>
    </div>
  );
}

